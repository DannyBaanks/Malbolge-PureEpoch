#!/usr/bin/env python3
"""Pure-Malbolge epoch observability experiment.

The target executes *unchanged* Classic Malbolge. This Python program is
measurement tooling, NEVER the runtime recovery mechanism.

Source: implements the strict Classic Olmstead semantics mirrored in
BolgeForge/tools/prove_truth_machine.py and oracle/mb_ref.c.
"""
from __future__ import annotations

import argparse
from array import array
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys

MEM_SIZE=59049
XLAT1 = "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha"
XLAT2 = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@"
VALID=set("ji*p</vo")
TRITS=((1,0,0),(1,0,2),(2,2,1))


def crazy(x,y):
    n=0
    power=1
    for _ in range(10):
        n += TRITS[y%3][x%3]*power
        x//=3; y//=3; power*=3
    return n


def load(source):
    cells=[]
    for pos,byte in enumerate(source):
        if byte in (9,10,13,32):
            continue
        if not 33 <= byte <= 126:
            raise ValueError(f"non-ASCII printable byte at file offset {pos}")
        instruction=XLAT1[(byte-33+len(cells))%94]
        if instruction not in VALID:
            raise ValueError(f"strict loader rejects position {len(cells)}: {instruction!r}")
        cells.append(byte)
    if not 2 <= len(cells) <= MEM_SIZE:
        raise ValueError("program must occupy 2..59049 cells")
    while len(cells)<MEM_SIZE:
        cells.append(crazy(cells[-1],cells[-2]))
    return cells


@dataclass
class Machine:
    mem:list[int]
    payload:bytes
    a:int=0
    c:int=0
    d:int=0
    input_cursor:int=0
    steps:int=0
    output:bytes=b""
    terminal:str="RUNNING"

    def regs(self):
        return (self.a,self.c,self.d,self.input_cursor)

    def snapshot(self):
        return array('H',self.mem).tobytes()

    def tick(self):
        if self.terminal!="RUNNING":
            return set()
        pc=self.c
        v=self.mem[pc]
        if not 33<=v<=126:
            self.terminal="STALL"
            return set()
        instruction=XLAT1[(v-33+pc)%94]
        changed=set()
        if instruction=='j': self.d=self.mem[self.d]
        elif instruction=='i': self.c=self.mem[self.d]
        elif instruction=='*':
            old=self.mem[self.d]
            self.a=self.mem[self.d]=old//3+(old%3)*19683
            if old!=self.mem[self.d]: changed.add(self.d)
        elif instruction=='p':
            old=self.mem[self.d]
            self.a=self.mem[self.d]=crazy(self.a,old)
            if old!=self.mem[self.d]: changed.add(self.d)
        elif instruction=='<': self.output+=bytes([self.a&255])
        elif instruction=='/':
            if self.input_cursor<len(self.payload):
                self.a=self.payload[self.input_cursor]
                self.input_cursor+=1
            else: self.a=59048
        elif instruction=='v':
            self.terminal="HALT"
            return changed
        old=self.mem[self.c]
        if not 33<=old<=126:
            self.terminal="STALL"
            return changed
        self.mem[self.c]=ord(XLAT2[old-33])
        if old!=self.mem[self.c]: changed.add(self.c)
        self.c=(self.c+1)%MEM_SIZE
        self.d=(self.d+1)%MEM_SIZE
        self.steps+=1
        return changed


def max_untouched_run(touched):
    longest_start=longest_len=run_start=0
    for pos in range(MEM_SIZE+1):
        if pos==MEM_SIZE or pos in touched:
            length=pos-run_start
            if length>longest_len:
                longest_start,longest_len=run_start,length
            run_start=pos+1
    return longest_start,longest_len


def analyze(program:bytes,payload=b'1',warmup=1000,max_steps=5000,mutate=True):
    initial=load(program)
    vm=Machine(initial.copy(),payload)
    # Full byte snapshots, NOT just hashes, ensure no-alias of VM state.
    seen={}
    touched=set()
    writes_by_step=[]
    cycle=None
    for _ in range(max_steps):
        if vm.terminal!='RUNNING': break
        writes=vm.tick()
        touched.update(writes)
        writes_by_step.append(writes)
        if vm.steps < warmup: continue
        key=vm.regs()
        blob=vm.snapshot()
        if key in seen:
            start_step,start_mem,start_output=seen[key]
            if blob==start_mem and len(vm.output)>start_output:
                epoch_writes=set().union(*writes_by_step[start_step:vm.steps])
                cycle={"start_step":start_step,"end_step":vm.steps,
                       "modified_cell_count":len(epoch_writes),
                       "modified_cells_returned_to_anchor":len(epoch_writes),
                       "period":vm.steps-start_step,
                       "output_growth":len(vm.output)-start_output,
                       "output_during_cycle":vm.output[start_output:].hex(),
                       "same_registers_memory_input":True,
                       "anchor_memory":start_mem,
                       "anchor_output_cursor":start_output,
                       "anchor_regs":key}
                break
        else:
            seen[key]=(vm.steps,blob,len(vm.output))
    run_start,run_length=max_untouched_run(touched)
    verdict="DEMONSTRATED_CYCLE" if cycle else "NOT_DEMONSTRATED"
    negative=None
    if cycle and mutate and run_length:
        # Fault injection is TEST instrumentation, never a runtime recovery.
        addr=run_start+run_length//2
        cells=array('H')
        cells.frombytes(cycle['anchor_memory'])
        if sys.byteorder!='little':
            raise RuntimeError("probe supports little-endian measurement host")
        old=cells[addr]
        cells[addr]=(old+1)%MEM_SIZE
        fault=Machine(list(cells),payload,a=cycle['anchor_regs'][0],c=cycle['anchor_regs'][1],
                      d=cycle['anchor_regs'][2],input_cursor=cycle['anchor_regs'][3])
        for _ in range(cycle['period']):
            if fault.terminal!='RUNNING':break
            fault.tick()
        negative={"mutated_cell":addr,"previous_value":old,"injected_value":(old+1)%MEM_SIZE,
                  "cell_restored_by_malbolge":fault.mem[addr]==old,
                  "full_anchor_state_restored":fault.regs()==cycle['anchor_regs'] and fault.snapshot()==cycle['anchor_memory']}
    result={
        "schema":"malbolge-pure-epoch-probe/v0",
        "source_sha256":hashlib.sha256(program).hexdigest(),
        "source_bytes":len(program),"memory_cells":MEM_SIZE,
        "payload_hex":payload.hex(),"max_steps":max_steps,"warmup":warmup,
        "status":vm.terminal,"observed_steps":vm.steps,
        "touched_cell_count":len(touched),
        "untouched_run":{"start":run_start,"length":run_length},
        "cycle":({k:v for k,v in cycle.items() if not k.startswith('anchor_')} if cycle else None),
        "negative_control":negative,
        "verdict":verdict,
        "claim_boundary":"External observer only. Does not synthesize, checkpoint or rollback at runtime."
    }
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('program',type=Path)
    p.add_argument('--input',default='1')
    p.add_argument('--warmup',type=int,default=1000)
    p.add_argument('--max-steps',type=int,default=5000)
    p.add_argument('--no-negative',action='store_true')
    args=p.parse_args()
    r=analyze(args.program.read_bytes(),args.input.encode('latin1'),args.warmup,args.max_steps,not args.no_negative)
    print(json.dumps(r,indent=2,sort_keys=True))
    return 0 if r['verdict']=='DEMONSTRATED_CYCLE' else 2

if __name__=='__main__':raise SystemExit(main())
