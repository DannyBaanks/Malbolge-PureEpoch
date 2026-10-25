#!/usr/bin/env python3
"""M1: Locate and classify D \\ C \\ E borrow-and-return windows across m281, lutter, and m284
from the retained full-run CSVs and the 30,000-step prefix trace (executes 0 new VM steps).
Explicitly excludes live cell 53.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def analyze_quine_dce(name: str) -> dict:
    counts = list(csv.DictReader((ROOT / 'runs' / f'{name}.counts.csv').read_text().splitlines()))
    total_steps = max(int(c['firstC']) for c in counts)

    dce_all = []
    pass_through_r0_w0 = []
    read_only_w0_bounded = []
    delayed_init_rw = []

    for row in counts:
        addr = int(row['address'])
        if addr == 53:
            continue
        c_vis = int(row['C_visits'])
        d_vis = int(row['D_visits'])
        enc = int(row['encryptions'])
        if d_vis > 0 and c_vis == 0 and enc == 0:
            r_cnt = int(row['operand_reads'])
            w_cnt = int(row['direct_writes'])
            first_d = int(row['firstD'])
            first_r = int(row['firstR'])
            last_r = int(row['lastR'])
            first_w = int(row['firstW'])
            last_w = int(row['lastW'])
            entry = {
                'address': addr,
                'D_visits': d_vis,
                'operand_reads': r_cnt,
                'direct_writes': w_cnt,
                'firstD': first_d,
                'firstR': first_r,
                'lastR': last_r,
                'firstW': first_w,
                'lastW': last_w,
            }
            dce_all.append(entry)
            if r_cnt == 0 and w_cnt == 0:
                pass_through_r0_w0.append(entry)
            elif r_cnt > 0 and w_cnt == 0:
                entry['pre_read_loan_window_steps'] = max(0, first_r - first_d)
                entry['post_read_loan_window_steps'] = max(0, total_steps - last_r)
                read_only_w0_bounded.append(entry)
            elif w_cnt > 0 and first_w > first_d + 1000:
                first_active = min(x for x in (first_r, first_w) if x > 0)
                entry['pre_init_loan_window_steps'] = max(0, first_active - first_d)
                delayed_init_rw.append(entry)

    c53 = next(r for r in counts if int(r['address']) == 53)
    return {
        'program': name,
        'total_steps': total_steps,
        'cell_53_excluded': {
            'address': 53,
            'D_visits': int(c53['D_visits']),
            'operand_reads': int(c53['operand_reads']),
            'direct_writes': int(c53['direct_writes']),
            'firstW': int(c53['firstW']),
            'lastW': int(c53['lastW']),
            'status': 'EXCLUDED_LIVE_LOOP_POINTER',
        },
        'dce_excluding_53_count': len(dce_all),
        'pass_through_r0_w0_count': len(pass_through_r0_w0),
        'pass_through_r0_w0_cells': pass_through_r0_w0,
        'read_only_w0_bounded_count': len(read_only_w0_bounded),
        'read_only_w0_bounded_cells': read_only_w0_bounded,
        'delayed_init_pre_20k_cells_low_mem': [e for e in delayed_init_rw if e['address'] < 94],
    }


def main():
    quines = {name: analyze_quine_dce(name) for name in ('m281', 'lutter', 'm284')}
    prefix_rows = list(csv.DictReader((ROOT / 'runs/journal_prefix_30000.csv').read_text().splitlines()))

    band_39_44 = {}
    for addr in range(39, 45):
        events = [
            {
                'step': int(r['step']),
                'c': int(r['c']),
                'opcode': int(r['opcode']),
                'operand': int(r['operand']),
                'direct_new': int(r['direct_new']),
            }
            for r in prefix_rows
            if int(r['d']) == addr
        ]
        band_39_44[str(addr)] = {
            'initial_byte_in_m281': events[0]['operand'] if events else None,
            'visits_in_first_30000_steps': len(events),
            'events': events,
        }

    report = {
        'schema': 'pure-epoch-torus-dce-borrow-windows/v1',
        'scope_note': (
            'The 49+47 C∩D decomposition and unvisited complement cells (D=0, e.g. 3..22) do not prove '
            'journal availability or autonomy. Availability requires D-reachability in D\\C\\E plus an '
            'explicit temporary borrow-and-return preservation contract.'
        ),
        'cell_53_policy': 'FORBIDDEN (live pointer cell written at steps 18, 20575, 20605 and read 1143 times)',
        'shared_low_memory_dce_band_39_44': {
            'addresses': [39, 40, 41, 42, 43, 44],
            'in_D_minus_C_minus_E_across_all_three_quines': all(
                any(c['address'] == a for c in quines[q]['pass_through_r0_w0_cells'] + quines[q]['read_only_w0_bounded_cells'])
                for q in ('m281', 'lutter', 'm284')
                for a in range(39, 45)
            ),
            'roles': {
                '39': 'Read-only once at step 138 (mem[39]=60 for j->61); borrowable in steps 4..137 (if returned before 138) or steps 139..end',
                '40': 'Pass-through D\\C\\E (firstD=5, R=0, W=0, E=0); used as state cell S in E-T3',
                '41': 'Read-only at steps 19708..19828 (mem[41]=121 for j->122); pre-read loan window steps 6..19707 (19702 steps), used as borrowed cell in E-T2',
                '42': 'Pass-through D\\C\\E (firstD=7, mem[42]=120, R=0, W=0, E=0); used as borrowed journal cell J in E-T3 with downstream j consumer verification',
                '43': 'Pass-through D\\C\\E (firstD=8, mem[43]=119, R=0, W=0, E=0); used as loan-ledger cell L in E-T2',
                '44': 'Pass-through D\\C\\E (firstD=9, mem[44]=118, R=0, W=0, E=0); used as loan-ledger cell L in E-T3',
            },
            'prefix_30000_trace_on_band': band_39_44,
        },
        'quines': quines,
    }

    dest = ROOT / 'runs/dce_borrow_windows.json'
    dest.write_text(json.dumps(report, indent=2) + '\n')
    print(dest, 'shared_band_verified:', report['shared_low_memory_dce_band_39_44']['in_D_minus_C_minus_E_across_all_three_quines'])


if __name__ == '__main__':
    main()
