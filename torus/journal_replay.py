#!/usr/bin/env python3
"""Independent strict 30,000-step prefix replay, with a complete small trace.
No injected state. An independent implementation of ternary crazy and rotation.
The emitted 32-byte transition encoding is identical to observe.c for comparison.
"""
import csv,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent
N=59049
ENC=b'5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK\'X~xDl}REokN:#?G"i@'
def crazy(x,y):
    z=0
    for pos in range(10):
        xt=x%3;yt=y%3
        v=1 if (yt,xt) in [(0,0),(1,0),(2,2)] else (2 if (yt,xt) in [(1,2),(2,0),(2,1)] else 0)
        z+=v*3**pos;x//=3;y//=3
    return z
def main():
    src=(ROOT/'programs/m281.mal').read_bytes();program=[x for x in src if x not in b' \t\n\r\v\f']
    assert all(33<=x<=126 and (x+i)%94 in [4,5,23,39,40,62,68,81] for i,x in enumerate(program))
    mem=program+[0]*(N-len(program))
    for i in range(len(program),N):mem[i]=crazy(mem[i-1],mem[i-2])
    a=c=d=0;sha=hashlib.sha256();all53=[];frontiers=[]
    with (ROOT/'runs/journal_prefix_30000.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['step','a','c','d','cell','opcode','operand','direct_new','enc_addr','enc_old','enc_new','next_c','next_d'])
        for step in range(1,30001):
            assert 33<=mem[c]<=126
            oa,oc,od=a,c,d;cell=mem[c];op=(cell+c)%94;operand=mem[d];direct=ea=eb=en=65535
            if op==4:c=mem[d]
            elif op==5:pass
            elif op==23:a=59048
            elif op==39:a=mem[d]=direct=mem[d]//3+(mem[d]%3)*19683
            elif op==40:d=mem[d]
            elif op==62:a=mem[d]=direct=crazy(a,mem[d])
            elif op==81:raise AssertionError('Unexpected prefix HALT')
            assert 33<=mem[c]<=126
            ea=c;eb=mem[c];en=ENC[mem[c]-33];mem[c]=en;c=(c+1)%N;d=(d+1)%N
            vals=[oa,oc,od,cell,op,operand,direct,ea,eb,en,c,d];w.writerow([step]+vals);sha.update(struct.pack('<Q12H',step,*vals))
            if od==53 and op in [4,39,40,62]:all53.append(dict(step=step,c=oc,opcode=op,before=operand,after=direct if direct!=65535 else operand))
            if step in [17,18,19,1358,20574,20575,20605,25000,30000]:frontiers.append(dict(step=step,a=a,c=c,d=d,mem53=mem[53]))
    result=dict(allocated_steps=30000,steps=30000,trace_sha256=sha.hexdigest(),cell53_operand_events=all53,frontiers=frontiers)
    (ROOT/'runs/journal_prefix_30000.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
