#!/usr/bin/env python3
"""Huella de trayectoria Malbolge sobre T^10 x T^2 (agregacion en linea, sin guardar pasos)."""
import sys, json, hashlib, time

N = 3 ** 10
_ORIGINAL = r"""!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"""
_TRANSLATED = r"""5z]&gqtyfr$(we4{WP)H-Zn,[%\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G"i@"""
_ENC = {ord(o): ord(t) for o, t in zip(_ORIGINAL, _TRANSLATED)}
_CRAZY = ((1,0,0),(1,0,2),(2,2,1))

def crazy(x, y):
    res = 0; p = 1
    for _ in range(10):
        res += _CRAZY[y % 3][x % 3] * p
        x //= 3; y //= 3; p *= 3
    return res

def load(src):
    chars = [ord(c) for c in src if not c.isspace()]
    mem = [0]*N
    mem[:len(chars)] = chars
    for i in range(len(chars), N):
        mem[i] = crazy(mem[i-1], mem[i-2])
    return mem, len(chars)

def run(path, max_steps=200_000_000):
    src = open(path, encoding="utf-8", errors="surrogateescape").read()
    mem, ncells = load(src)
    a = c = d = 0
    out = bytearray()
    steps = 0
    opc = [0]*94
    vis_c = bytearray(N); vis_d = bytearray(N)
    enc_hits = 0
    segs = 1; last_delta = 0; breaks = {4:0, 40:0, "otro":0}
    diag_steps = 0
    status = "MAX_STEPS"
    t0 = time.time()
    while steps < max_steps:
        steps += 1
        cell = mem[c]
        op = (cell + c) % 94
        opc[op] += 1
        vis_c[c] = 1; vis_d[d] = 1
        jumped = False; c_target = 0
        if op == 4:
            c_target = mem[d]; jumped = True
        elif op == 5:
            out.append(a % 256)
        elif op == 23:
            a = -1
        elif op == 39:
            v = mem[d]; mem[d] = v//3 + (v % 3)*(3**9); a = mem[d]
        elif op == 40:
            d = mem[d]
        elif op == 62:
            mem[d] = crazy(a, mem[d]); a = mem[d]
        elif op == 81:
            status = "HALTED"
            break
        if jumped:
            c = c_target
        mc = mem[c]
        if 33 <= mc <= 126:
            mem[c] = _ENC[mc]; enc_hits += 1
        c = (c+1) % N; d = (d+1) % N
        nd = (d - c) % N
        if nd != last_delta:
            breaks[4 if op == 4 else (40 if op == 40 else "otro")] += 1
            segs += 1; last_delta = nd
        else:
            diag_steps += 1
    dt = time.time() - t0
    vc = sum(vis_c); vd = sum(vis_d)
    # simetrias de traslacion del footprint (firma de sub-toro, sin depender de una radix)
    def symmetries(vis):
        V = int.from_bytes(bytes(vis), "little")
        full = (1 << N) - 1
        found = []
        for s in range(1, N):
            sh = ((V >> s) | (V << (N - s))) & full
            if (sh & V) == V:
                found.append(s)
        return found
    sym = symmetries(vis_c)
    print(json.dumps({
        "file": path,
        "cells_source": ncells,
        "status": status,
        "steps": steps,
        "seconds": round(dt, 1),
        "output_len": len(out),
        "output_sha256": hashlib.sha256(bytes(out)).hexdigest(),
        "opcodes": {str(k): v for k, v in enumerate(opc) if v},
        "visited_c": vc, "visited_d": vd, "visited_union": sum(1 for i in range(N) if vis_c[i] or vis_d[i]),
        "coverage_c": round(vc/N, 4),
        "encryption_hits": enc_hits,
        "delta_segments": segs,
        "delta_breaks": {str(k): v for k, v in breaks.items()},
        "diagonal_fraction": round(diag_steps/steps, 6) if steps else None,
        "shift_symmetries": sym,
        "shift_symmetry_count": len(sym),
    }, indent=2))

if __name__ == "__main__":
    run(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 200_000_000)
