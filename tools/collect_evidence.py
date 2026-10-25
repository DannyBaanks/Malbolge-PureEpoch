"""Reproduce small experiments from zero, preserving raw observational evidence."""
from pathlib import Path
import hashlib
import json
import platform
import shutil
import subprocess
import sys

from tools import build_candidates as build
from tools.observe import run, target_contract, conditional_contract, m1e_contract, m2_contract, m2_journal_consumption
from tools.oracles import verify, compile_oracles, validate_parity
from tools.autobolge_adapter import bridge, eof_probe, semantic_probes

ROOT = Path(__file__).resolve().parents[1]

PINNED_REPOSITORIES = {
    'Autobolge': {
        'remote': 'https://github.com/DannyBaanks/Autobolge.git',
        'commit': 'ac0de274cee079ed4c85e4f018754a538c952a9e',
    },
    'BolgeForge': {
        'remote': 'https://github.com/DannyBaanks/BolgeForge.git',
        'commit': 'eef65c83a2885b6e3d66c26fede9931dfdba5e40',
    },
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def emit_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2)+'\n')


def main():
    build.main()
    emit_json(ROOT/'evidence/trampoline-rearm.json', build.trampoline_rearm_analysis())
    measurements = []
    cases = [('m1a_rot10', b'', 5000), ('m1a_rot9_negative', b'', 5000)]
    cases += [('m1b_normal', p, 5000) for p in [b'\x01\x00', b'\x03\x00']]
    cases += [(f'm1b_{mode}', b'\x01\x00', 5000) for mode in ['no_save','corrupt_journal','early_halt','output_impostor']]
    cases += [('m1c_normal', p, 5000) for p in [b'\x01\x01', b'\x01\x03', b'\x03\x01', b'\x03\x03']]
    cases += [(f'm1c_{mode}', b'\x03\x03', 1000) for mode in ['no_save','corrupt_journal','no_restore','no_recovery','broken_return','early_halt','force_retry_failure']]
    cases += [('m1e_normal', p, 5000) for p in [b'\x01\x01', b'\x01\x03', b'\x03\x01', b'\x03\x03']]
    cases += [(f'm1e_{mode}', p, 5000) for mode in ['no_save','corrupt_journal','no_restore','no_recovery','broken_return','early_halt','output_impostor','force_retry_failure','force_retry_stall'] for p in [b'\x01\x03', b'\x03\x03']]
    cases += [('m2_normal', bytes([i, c1, c2]), 10000) for i in [1, 3] for c1, c2 in [(1, 1), (3, 1), (1, 3), (3, 3)]]
    cases += [(f'm2_{mode}', bytes([i, 3, 3]), 10000) for mode in ['no_save','corrupt_journal','no_restore','broken_rearm','force_retry_failure','output_impostor'] for i in [1, 3]]
    for name, payload, budget in cases:
        source = (ROOT/'candidates'/f'{name}.mal').read_bytes()
        meta = json.loads((ROOT/'candidates'/f'{name}.json').read_text())
        tag = f'{name}-{payload.hex() or "empty"}'
        dest = ROOT/'evidence/traces'/tag
        report = verify(source, payload, budget, dest)
        result = run(source, payload, budget)
        if name.startswith('m2'):
            contract = m2_contract(result, meta, payload[0], payload[1], payload[2])
        elif name.startswith('m1e'):
            contract = m1e_contract(result, meta, payload[0], payload[1])
        elif name.startswith('m1c'):
            contract = conditional_contract(result, meta, payload[0], payload[1])
        else:
            contract = target_contract(result, meta['target'], 37 if name.startswith('m1a') else 29524-payload[0])
        expected = name in {'m1a_rot10','m1b_normal','m1c_normal','m1e_normal','m2_normal'}
        parity = validate_parity(report)
        if not parity or contract != expected:
            raise AssertionError((tag, report, contract, expected))
        phases = {label: [e for e in result['trace'] if e['pre'][1] == pc] for label, pc in meta.get('labels',{}).items()}
        emit_json(dest/'phases.json', phases)
        C = {e['pre'][1] for e in result['trace']}
        D = {e['pre'][2] for e in result['trace']}
        changed = {v[0] for e in result['trace'] for v in e['changes']}
        extra = {'attempt_counter_final': result['memory'][meta['attempt_counter_cell']]} if 'attempt_counter_cell' in meta else {}
        if name.startswith('m2'):
            extra['journal_consumption'] = m2_journal_consumption(result, meta)
        report.update({'name':name, 'source_bytes':len(source), 'logical_contract':contract,
                       'expected_logical_contract':expected, 'target_final':result['memory'][meta['target']],
                       'journal_final':result['memory'][meta['journal']] if 'journal' in meta else None,
                       **extra,
                       'C_unique':len(C), 'D_unique':len(D), 'C_intersect_D':sorted(C&D),
                       'changed_cells':len(changed), 'trace_directory':str(dest.relative_to(ROOT))})
        measurements.append(report)
        print(tag, 'HALT/state:',report['terminal'],contract,'instructions:',len(result['trace']))
    emit_json(ROOT/'evidence/measurements.json', measurements)
    eof_strict = verify(b'uP', b'', 10, ROOT/'evidence/eof-strict')
    if not validate_parity(eof_strict):
        raise AssertionError(('eof-strict', eof_strict))
    emit_json(ROOT/'evidence/autobolge-bridge.json', {'eof_difference':eof_probe(),
               'semantic_probes':semantic_probes(),
               'cases':[bridge(p) for p in [b'\x01\x03',b'\x03\x03']]})
    zig_bin = shutil.which('zig')
    tool_versions = {'python':sys.version,'platform':platform.platform(),
                     'gcc':subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
                     'zig':subprocess.check_output([zig_bin,'version'],text=True).strip() if zig_bin else 'not_installed (optional)'}
    repositories = dict(PINNED_REPOSITORIES)
    git_bin = shutil.which('git')
    for name in ['Autobolge','BolgeForge']:
        repo=ROOT/'sources'/name
        if repo.exists() and git_bin:
            repositories[name]={'remote':subprocess.check_output([git_bin,'remote','get-url','origin'],cwd=repo,text=True).strip(),
                                'commit':subprocess.check_output([git_bin,'rev-parse','HEAD'],cwd=repo,text=True).strip()}
    paths = [p for d in ['baseline','vendor','candidates','tools','tests'] for p in (ROOT/d).rglob('*')
             if p.is_file() and '__pycache__' not in p.parts]
    binaries = {p.name:digest(p) for p in compile_oracles().iterdir() if p.is_file()}
    manifest = {'schema':'pure-epoch-experiment/v1','client_date':'2026-10-25','timezone':'America/Mexico_City',
                'original_worktrees':'evidence/initial_state.json', 'source_checkouts':repositories,
                'environment':tool_versions, 'binary_sha256':binaries,
                'semantics':{'primary':'Strict Olmstead Classic; 59049 cells, strict address loader, EOF59048, destination encryption, diagnostic stop on undefined encryption/stalled PC',
                  'step_convention':'measurements steps_excluding_halt counts non-HALT instructions; fetched_instructions includes HALT',
                  'state_contract':'logical target cell and explicit recovery protocol; NOT physical full-VM rollback',
                  'autobolge':'toolkit semantics used only on checked common-domain runs; EOF probe demonstrates divergence',
                  'runtime_host_writes':False, 'source_loads_per_run':1},
                'budgets':{'small_candidate_instructions':5000,'two_epoch_candidate_instructions':10000,'forced_failure_instructions':1000,
                           'toroidal':'torus/budget_all.json'},
                'file_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}}
    emit_json(ROOT/'evidence/manifest.json',manifest)
    baseline = json.loads((ROOT/'baseline/report.json').read_text())
    reproduced = json.loads((ROOT/'evidence/report-reproduced.json').read_text())
    assert baseline == reproduced, 'M0 reproduction differs'
    initial = json.loads((ROOT/'evidence/initial_state.json').read_text())
    assert all(digest(ROOT/'baseline'/name)==sha for name,sha in initial['baseline_files'].items())
    print('M0 byte preservation and reproduced JSON: identical')


if __name__ == '__main__':
    main()
