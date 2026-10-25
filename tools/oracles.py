"""Compile and compare three standalone executions. Never resume a snapshot."""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import tempfile

from tools.observe import run

ROOT = Path(__file__).resolve().parents[1]


def compile_oracles():
    build = ROOT/'build'
    build.mkdir(exist_ok=True)
    for name, source, flags in [('mb_ref', ROOT/'vendor/mb_ref.c', []),
                                ('olmstead', ROOT/'vendor/olmstead_original.c', []),
                                ('trace_ref', ROOT/'tools/trace_ref.c', [])]:
        binary = build/name
        inputs = [source, ROOT/'vendor/mb_ref.c']
        if not binary.exists() or binary.stat().st_mtime < max(p.stat().st_mtime for p in inputs):
            subprocess.run(['gcc', '-O2', *flags, str(source), '-o', str(binary)], check=True, capture_output=True)
    return build


def raw_reference(source, payload, budget=5000):
    build = compile_oracles()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder)/'program.mal'
        path.write_bytes(source)
        return subprocess.run([str(build/'mb_ref'), str(path), str(budget)], input=payload, capture_output=True, timeout=20)


def verify(source, payload, budget=5000, evidence=None):
    build = compile_oracles()
    py = run(source, payload, budget)
    with tempfile.TemporaryDirectory() as folder:
        tmp = Path(folder)
        program = tmp/'program.mal'
        program.write_bytes(source)
        c = subprocess.run([str(build/'trace_ref'), str(program), str(budget), str(tmp/'trace.jsonl'), str(tmp/'state.bin')], input=payload, capture_output=True, timeout=20)
        ref = subprocess.run([str(build/'mb_ref'), str(program), str(budget)], input=payload, capture_output=True, timeout=20)
        # The historical interpreter has no step budget; process timeout is an
        # external negative-test bound, never recovery. Small candidates HALT.
        original = None
        if py['terminal'] == 'HALT':
            original = subprocess.run([str(build/'olmstead'), str(program)], input=payload, capture_output=True, timeout=20)
        c_trace = [json.loads(line) for line in (tmp/'trace.jsonl').read_text().splitlines()]
        c_state = (tmp/'state.bin').read_bytes()
        py_state = struct.pack('<59049H', *py['memory'])
        summary = json.loads(c.stderr)
        report = {'trace_equal': c_trace == py['trace'], 'memory_equal': c_state == py_state,
                  'registers_equal': summary['registers'] == py['registers'],
                  'terminal_equal': summary['terminal'] == py['terminal'],
                  'outputs_equal': py['output'] == c.stdout == ref.stdout and (original is None or ref.stdout == original.stdout),
                  'reference_returncode': ref.returncode, 'original_returncode': original.returncode if original else None,
                  'original_run': 'completed' if original else 'not_run: historical VM has no instruction budget; negative non-HALT is checked by bounded strict C and Python',
                  'instrumented_returncode': c.returncode,
                  'source_sha256': hashlib.sha256(source).hexdigest(), 'payload_hex': payload.hex(),
                  'terminal': py['terminal'], 'steps_excluding_halt': py['steps'],
                  'fetched_instructions': len(py['trace']), 'registers': py['registers'],
                  'output_hex': py['output'].hex(), 'memory_sha256': hashlib.sha256(c_state).hexdigest(),
                  'trace_sha256': hashlib.sha256((tmp/'trace.jsonl').read_bytes()).hexdigest()}
        if evidence:
            dest = Path(evidence)
            dest.mkdir(parents=True, exist_ok=True)
            for src in ['trace.jsonl', 'state.bin']:
                (dest/src).write_bytes((tmp/src).read_bytes())
            (dest/'python-trace.jsonl').write_text(''.join(json.dumps(e, separators=(',',':'))+'\n' for e in py['trace']))
            (dest/'stdout.bin').write_bytes(ref.stdout)
            (dest/'reference-stderr.txt').write_bytes(ref.stderr)
            (dest/'original-stderr.txt').write_bytes(original.stderr if original else report['original_run'].encode())
            (dest/'instrumented-summary.json').write_bytes(c.stderr)
            (dest/'parity.json').write_text(json.dumps(report, indent=2)+'\n')
        return report
