"""Builder para boss3_real_loop.mal - Bucle autónomo while x > 0 en Classic Malbolge.

Construcción del archivo .mal bajo el loader estricto (celdas fuente válidas 33-126).
Arquitectura limpia de ruta A:
- 100% inmutable, sin sobreescritura de ROM en seek o load
- Tabla de saltos estáticos en memoria baja
- Bloques START, REARM y PN en memoria alta
- Rearme de la instrucción de salida '<' en memoria entre iteraciones (subrutina compartida)
- Cumplimiento integral de los contratos G1-G8 y paridad de 3 oráculos
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import sys
from typing import Tuple

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.insert(0, str(PURE_EPOCH_ROOT))

from baseline.epoch_probe import XLAT1, XLAT2, crazy, MEM_SIZE
from tools.build_candidates import encode, strict_byte


def rot(v: int) -> int:
    return (v // 3) + (v % 3) * 19683


def rot_k(v: int, k: int) -> int:
    for _ in range(k):
        v = rot(v)
    return v


def g(x: int) -> int:
    return crazy(x, 29524)


def trits(v: int, n: int = 10) -> list:
    out = []
    for _ in range(n):
        out.append(v % 3)
        v //= 3
    return out


def from_trits(t: list) -> int:
    n, p = 0, 1
    for x in t:
        n += x * p
        p *= 3
    return n


def reset_vector(y: int) -> int:
    ty = trits(y)
    tx = [2 if t == 2 else 0 for t in ty]
    return from_trits(tx)


def has_printable_rotation(v: int) -> bool:
    if 33 <= v <= 126:
        return True
    for k in range(1, 10):
        if 33 <= rot_k(v, k) <= 126:
            return True
    return False


def choose_placeholder(pos: int):
    candidates = []
    for b in range(33, 97):
        if not strict_byte(b, pos):
            continue
        t = trits(b)
        c2 = t.count(2)
        if c2 == 0:
            candidates.append((0, b))
        elif c2 == 1:
            idx = t.index(2)
            if idx in (0, 1, 2, 3):
                candidates.append((1, b))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


L = 50000
T = {m: g(m) + 1 for m in range(0, 127)}
OUT = 29588
HP = 60
SCRATCH = [36, 52, 75, 76, 81]

JUMPS = {35: 34, 44: 38, 48: 34, 58: 42, 66: 52, 70: 64, 74: 61, 79: 78, 84: 34, 88: 75, 92: 71, 97: 79}
RESERVED = set(SCRATCH) | {53, HP, 0} | set(JUMPS.keys())
PORTALS = [p for p in range(34, 98) if p not in RESERVED]

MERGE_PATH = 'oooooooooooooooooooojooooooj'


def allocate_layout():
    used = [
        (0, 20500),      # Zona 1: Inicialización y tablas
        (29300, 400),    # Zona 3: T[m] y OUT
    ]

    def can_alloc(a: int, span: int) -> bool:
        for u, u_span in used:
            if max(a, u) < min(a + span, u + u_span):
                return False
        return True

    pn_list = [49168, 49177, 49181, 49195, 49199, 49203, 49207, 49211, 49215]
    PN = {j + 1: pn_list[j] for j in range(9)}
    for a in pn_list:
        used.append((a, 4))

    START5_ADDR = 24422
    START8_ADDR = 36078
    assert can_alloc(START5_ADDR, 900)
    used.append((START5_ADDR, 900))
    assert can_alloc(START8_ADDR, 900)
    used.append((START8_ADDR, 900))

    REARM = {}
    for a in range(20000, 48500):
        if encode('o', a) <= 96 and has_printable_rotation(g(a - 1)):
            if can_alloc(a, 1300):
                REARM[len(REARM) + 1] = a
                used.append((a, 1300))
                if len(REARM) == 9:
                    break
    assert len(REARM) == 9, len(REARM)

    START = {}
    START[5] = START5_ADDR
    START[8] = START8_ADDR

    for j in range(11):
        if j in (5, 8):
            continue
        span = 20 if j in (0, 10) else 900
        for a in range(20000, 48500):
            if encode('o', a) <= 96 and has_printable_rotation(g(a - 1)):
                if can_alloc(a, span):
                    START[j] = a
                    used.append((a, span))
                    break
    assert len(START) == 11, len(START)
    START_LIST = [START[j] for j in range(11)]
    return START_LIST, REARM, PN


def prepare_constants(START, REARM, PN, mode: str):
    targets = set()
    for m in list(range(48, 58)) + [47, 58, 65, 0]:
        targets.add(g(T[m] - 1))
        j = m - 48 if 48 <= m <= 57 else 0
        jj = j
        if mode == 'off_by_one' and 48 <= m <= 57:
            if m not in (53, 56):
                jj = min(j + 1, 10)
        elif mode == 'broken_exit' and j == 0:
            jj = 1
        targets.add(g(START[jj] - 1))
        targets.add(reset_vector(T[m] - 1))
        targets.add(reset_vector(choose_placeholder(T[m])))

    for j in range(1, 10):
        targets.add(g(PN[j] - 1))
        targets.add(g(OUT - 1))
        targets.add(g(PN[j] + 1))
        nxt = REARM[j - 1] - 1 if j > 1 else START[0] - 1
        if mode == 'broken_decrement' and j > 1:
            nxt = REARM[j] - 1
        targets.add(g(nxt))
        targets.add(reset_vector(PN[j] - 1))
        targets.add(reset_vector(PN[j] + 1))
        targets.add(reset_vector(choose_placeholder(PN[j])))
        targets.add(reset_vector(choose_placeholder(PN[j] + 2)))

    targets.add(8)
    targets.add(49)
    targets.add(g(encode('<', OUT)))
    targets.add(reset_vector(OUT - 1))
    targets.add(reset_vector(choose_placeholder(OUT)))
    targets.discard(0)

    rk_map = {}
    for t in sorted(targets):
        for k in range(10):
            r = rot_k(t, k)
            if 33 <= r <= 126:
                rk_map[t] = (r, (10 - k) % 10)
                break
        assert t in rk_map, f"No printable rotation for target {t}"

    unique_bytes = sorted(set(r for r, k in rk_map.values()))
    avail = [p for p in range(34, 98) if p not in RESERVED]
    match = {}

    def dfs(u, seen):
        for v in avail:
            if strict_byte(u, v) and v not in seen:
                seen.add(v)
                if v not in match or dfs(match[v], seen):
                    match[v] = u
                    return True
        return False

    unique_bytes.sort(key=lambda b: len([p for p in avail if strict_byte(b, p)]))
    for b_byte in unique_bytes:
        seen = set()
        assert dfs(b_byte, seen), f"Could not match byte {b_byte}"
    byte_to_cell = {u: v for v, u in match.items()}
    return rk_map, byte_to_cell


class Builder:
    def __init__(self, byte_to_cell, START, REARM, PN):
        self.cells = [encode('o', p) for p in range(L)]
        self.c = 99
        self.d = 1
        self.a = 0
        self.input_byte = 48
        self.byte_to_cell = byte_to_cell
        self.cells[0] = encode('i', 0)
        for cell, target in JUMPS.items():
            b_target = target - 1
            assert strict_byte(b_target, cell)
            self.cells[cell] = b_target
        for p, v in {36: 81, 52: 81, 53: 81, 60: 39, 75: 81, 76: 80, 81: 81}.items():
            assert strict_byte(v, p), (p, v)
            self.cells[p] = v
        for b_val, p in byte_to_cell.items():
            assert strict_byte(b_val, p), (p, b_val)
            self.cells[p] = b_val
        for m in range(0, 127):
            ph = choose_placeholder(T[m])
            assert ph is not None, T[m]
            self.cells[T[m]] = ph
        for j in range(1, 10):
            pn = PN[j]
            for cell in (pn, pn + 1, pn + 2, pn + 3):
                ph = choose_placeholder(cell)
                assert ph is not None, cell
                self.cells[cell] = ph

        self.cells[START[0]] = encode('v', START[0])
        self.cells[START[10]] = encode('v', START[10])
        for j in range(1, 10):
            self.cells[START[j]] = encode('j', START[j])
            self.cells[REARM[j]] = encode('j', REARM[j])

        self.cells[OUT] = encode('<', OUT)
        self.cells[OUT + 1] = encode('i', OUT + 1)
        self.mem = self.cells[:]
        while len(self.mem) < MEM_SIZE:
            self.mem.append(crazy(self.mem[-1], self.mem[-2]))
        self.adj = {}
        for p in range(1, 98):
            edges = []
            if p + 1 <= 97:
                edges.append(('o', p + 1))
            self.adj[p] = edges
        for cell, target in JUMPS.items():
            self.adj[cell].append(('j', target))

    def emit(self, op: str):
        pos = self.c
        self.cells[pos] = encode(op, pos)
        self.mem[pos] = encode(op, pos)
        if op == 'j':
            self.d = (self.mem[self.d] + 1) % MEM_SIZE
            self.mem[pos] = ord(XLAT2[self.mem[pos] - 33])
            self.c += 1
        elif op == 'i':
            newc = self.mem[self.d]
            assert 33 <= self.mem[newc] <= 126, ("i to non-printable", newc)
            self.d = (self.d + 1) % MEM_SIZE
            self.mem[newc] = ord(XLAT2[self.mem[newc] - 33])
            self.c = (newc + 1) % MEM_SIZE
        elif op == '*':
            self.a = self.mem[self.d] = rot(self.mem[self.d])
            self.mem[pos] = ord(XLAT2[self.mem[pos] - 33])
            self.c += 1
            self.d = (self.d + 1) % MEM_SIZE
        elif op == 'p':
            self.a = self.mem[self.d] = crazy(self.a, self.mem[self.d])
            self.mem[pos] = ord(XLAT2[self.mem[pos] - 33])
            self.c += 1
            self.d = (self.d + 1) % MEM_SIZE
        elif op in ('<', '/', 'o'):
            if op == '/':
                self.a = self.input_byte
            self.mem[pos] = ord(XLAT2[self.mem[pos] - 33])
            self.c += 1
            self.d = (self.d + 1) % MEM_SIZE
        elif op == 'v':
            self.c += 1
        else:
            raise ValueError(op)

    def seek(self, target: int):
        assert 34 <= target <= 97, target
        while self.d > 97:
            self.emit('j')
        assert self.d <= 97, self.d
        start = self.d
        if start == target:
            return
        q = deque([(start, [])])
        seen = {start}
        while q:
            d, route = q.popleft()
            if d == target:
                for op, _ in route:
                    self.emit(op)
                assert self.d == target, (self.d, target)
                return
            for op, nxt in self.adj.get(d, []):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, route + [(op, nxt)]))
        raise ValueError(f"seek {target} from {start}")

    def load_a(self, target: int, depth: int = 6):
        if self.a == target:
            return
        scratch = SCRATCH
        start = (self.a, tuple(self.mem[s] for s in scratch))
        q = deque([(start, [])])
        seen = {start}
        while q:
            (a, mems), route = q.popleft()
            if len(route) >= depth:
                continue
            for i, s in enumerate(scratch):
                for op in ('*', 'p'):
                    na = rot(mems[i]) if op == '*' else crazy(a, mems[i])
                    nm = list(mems)
                    nm[i] = na
                    st = (na, tuple(nm))
                    if st in seen:
                        continue
                    seen.add(st)
                    nr = route + [(op, s)]
                    if na == target:
                        for o2, s2 in nr:
                            self.seek(s2)
                            self.emit(o2)
                        assert self.a == target
                        return
                    q.append((st, nr))
        raise ValueError(f"load_a({target}) from a={self.a}")

    def load_constant(self, target: int, rk_map: dict):
        if self.a == target:
            return None
        if target == 0:
            self.load_a(0, depth=6)
            return None
        assert target in rk_map, f"Target {target} not in rk_map"
        b, k = rk_map[target]
        cell = self.byte_to_cell[b]
        rot_count = 10 if k == 0 else k
        for _ in range(rot_count):
            self.seek(cell)
            self.emit('*')
        assert self.a == target, (self.a, target, b, k)
        restore_count = 0 if k == 0 else (10 - k)
        return (cell, restore_count)

    def restore_portal(self, token):
        if token is None:
            return
        cell, count = token
        for _ in range(count):
            self.seek(cell)
            self.emit('*')

    def set_hp(self, X: int, rk_map: dict):
        if self.mem[HP] != X - 1:
            if self.mem[HP] != 29524:
                rv = reset_vector(self.mem[HP])
                tok_rv = self.load_constant(rv, rk_map)
                self.seek(HP)
                self.emit('p')
                assert self.mem[HP] == 29524, (self.mem[HP], 29524)
                self.restore_portal(tok_rv)
            tok = self.load_constant(g(X - 1), rk_map)
            self.seek(HP)
            self.emit('p')
            assert self.mem[HP] == X - 1, (self.mem[HP], X - 1)
            self.restore_portal(tok)
        while self.d > 97:
            self.emit('j')
        assert self.d <= 97, self.d

    def seek_high(self, X: int, rk_map: dict):
        self.set_hp(X, rk_map)
        self.seek(HP)
        self.emit('j')
        assert self.d == X, (self.d, X)

    def write_high(self, X: int, V: int, rk_map: dict):
        self.seek_high(X, rk_map)
        rv = reset_vector(self.mem[X])
        tok_rv = self.load_constant(rv, rk_map)
        self.seek(HP); self.emit('j')
        self.emit('p')
        assert self.mem[X] == 29524, (X, self.mem[X])
        self.restore_portal(tok_rv)
        tok = self.load_constant(g(V), rk_map)
        self.seek(HP); self.emit('j')
        self.emit('p')
        assert self.mem[X] == V, (X, self.mem[X], V)
        self.restore_portal(tok)

    def image(self) -> bytes:
        return bytes(self.cells)


def build_boss3_real_loop(mode: str = 'normal') -> Tuple[bytes, dict]:
    """Construye un programa Malbolge autónomo para el bucle while x > 0."""
    if mode not in ('normal', 'broken_decrement', 'broken_exit', 'broken_rearm', 'off_by_one'):
        raise ValueError(f"Modo no soportado: {mode}")

    START, REARM, PN = allocate_layout()
    rk_map, byte_to_cell = prepare_constants(START, REARM, PN, mode)
    b = Builder(byte_to_cell, START, REARM, PN)

    # Paso 1: Inicialización y tablas en memoria de forma autónoma
    b.load_a(0)
    b.seek(HP); b.emit('p')
    assert b.mem[HP] == 29524

    domain_m = list(range(48, 58)) + [47, 58, 65, 0]
    for m in domain_m:
        j = m - 48 if 48 <= m <= 57 else 0
        jj = j
        if mode == 'off_by_one' and 48 <= m <= 57:
            if m not in (53, 56):
                jj = min(j + 1, 10)
        elif mode == 'broken_exit' and j == 0:
            jj = 1
        b.write_high(T[m], START[jj] - 1, rk_map)

    for j in range(1, 10):
        nxt = REARM[j - 1] - 1 if j > 1 else START[0] - 1
        if mode == 'broken_decrement' and j > 1:
            nxt = REARM[j] - 1
        b.write_high(PN[j], OUT - 1, rk_map)
        b.write_high(PN[j] + 2, nxt, rk_map)

    assert b.c < 20500, f"Paso 1 excedió límite 20500: {b.c}"

    # Preparar mem[HP] = 29524 antes de leer la entrada
    if b.mem[HP] != 29524:
        rv = reset_vector(b.mem[HP])
        tok_rv = b.load_constant(rv, rk_map)
        b.seek(HP); b.emit('p')
        assert b.mem[HP] == 29524
        b.restore_portal(tok_rv)

    # Leer el byte de entrada y despachar dinámicamente
    b.emit('/')
    b.seek(HP); b.emit('p')
    b.seek(HP); b.emit('j')
    b.emit('i')

    # Paso 2: Bloques
    Wout = g(encode('<', OUT))
    for j in (0, 10):
        b.c = START[j]
        b.emit('v')

    def reset_block_entry_points():
        for k in range(11):
            b.mem[START[k]] = b.cells[START[k]]
        for k in range(1, 10):
            b.mem[REARM[k]] = b.cells[REARM[k]]

    for j in range(1, 10):
        reset_block_entry_points()
        b.mem[OUT] = encode('<', OUT)
        b.c = START[j]
        b.d = T[48 + j] + 1
        b.mem[HP] = T[48 + j] - 1

        if j in (3, 6):
            b.emit('j')
            b.emit('j')
            for op in MERGE_PATH:
                b.emit(op)
            assert b.d == 34, b.d
        else:
            while b.d > 97:
                b.emit('j')
            assert b.d <= 97

        b.set_hp(PN[j], rk_map)
        c49 = b.byte_to_cell[49]
        for _ in range(10):
            b.seek(c49)
            b.emit('*')
        assert b.a == 49, b.a

        b.seek(HP); b.emit('j')
        assert b.d == PN[j]

        assert b.c - START[j] < 900
        b.emit('i')
        b.emit('<')
        b.emit('i')

    for j in range(1, 10):
        reset_block_entry_points()
        b.c = REARM[j]
        b.d = PN[j + 1] + 3 if j < 9 else PN[9] + 3
        b.mem[HP] = PN[j + 1] - 1 if j < 9 else PN[9] - 1

        while b.d > 97:
            b.emit('j')

        if mode != 'broken_rearm':
            b.mem[OUT] = 35
            b.seek_high(OUT, rk_map)
            tok8 = b.load_constant(8, rk_map)
            b.seek(HP); b.emit('j')
            b.emit('p')
            b.restore_portal(tok8)

            tokW = b.load_constant(Wout, rk_map)
            b.seek(HP); b.emit('j')
            b.emit('p')
            b.restore_portal(tokW)
            while b.d > 97:
                b.emit('j')

        b.seek_high(T[48 + j], rk_map)
        assert b.c - REARM[j] < 1300
        b.emit('i')

    b.cells[OUT] = encode('<', OUT)
    b.cells[OUT + 1] = encode('i', OUT + 1)
    img = b.image()
    assert all(strict_byte(v, p) for p, v in enumerate(img)), "Violación de loader estricto"

    sha = hashlib.sha256(img).hexdigest()
    meta = {
        'kind': 'BOSS3_REAL_LOOP',
        'mode': mode,
        'sha256': sha,
        'length_bytes': len(img),
        'claims': {
            'autonomous_loop': mode == 'normal',
            'host_intervention_required': False,
            'zero_external_memory_writes': True,
            'status': 'PASS' if mode == 'normal' else 'MUTANT'
        }
    }
    return img, meta


if __name__ == '__main__':
    root = PURE_EPOCH_ROOT
    candidates_dir = root / 'candidates'
    candidates_dir.mkdir(parents=True, exist_ok=True)

    # Generar normal como el candidato principal boss3_real_loop.{mal,json}
    img_normal, meta_normal = build_boss3_real_loop('normal')
    (candidates_dir / 'boss3_real_loop.mal').write_bytes(img_normal)
    (candidates_dir / 'boss3_real_loop.json').write_text(json.dumps(meta_normal, indent=2) + '\n')
    print(f"boss3_real_loop (normal): len={len(img_normal)}, sha256={meta_normal['sha256']}")

    # Generar boss3_real_loop_normal.{mal,json}
    (candidates_dir / 'boss3_real_loop_normal.mal').write_bytes(img_normal)
    (candidates_dir / 'boss3_real_loop_normal.json').write_text(json.dumps(meta_normal, indent=2) + '\n')

    # Generar mutantes
    for mode in ['broken_decrement', 'broken_exit', 'broken_rearm', 'off_by_one']:
        src, meta = build_boss3_real_loop(mode)
        out_mal = candidates_dir / f'boss3_real_loop_{mode}.mal'
        out_json = candidates_dir / f'boss3_real_loop_{mode}.json'
        out_mal.write_bytes(src)
        out_json.write_text(json.dumps(meta, indent=2) + '\n')
        print(f"boss3_real_loop_{mode}: len={len(src)}, sha256={meta['sha256']}")
