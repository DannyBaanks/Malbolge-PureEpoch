#!/usr/bin/env python3
"""Independent set algebra and byte-exact validation; executes no VM steps."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def rows(name,suffix):return list(csv.DictReader((ROOT/'runs'/f'{name}.{suffix}.csv').read_text().splitlines()))
def main():
    names=['m281','lutter','m284','cat','cat_empty','short','journal_access_candidate'];result={};sets={}
    for n in names:
        j=json.loads((ROOT/'runs'/f'{n}.json').read_text());r=rows(n,'sets')
        s={key:{int(x['address']) for x in r if x[col]=='1'} for key,col in [('C','C'),('D','D'),('R','read'),('W','written'),('E','encrypted')]}
        s.update(intersection=s['C']&s['D'],union=s['C']|s['D'],complement=set(range(59049))-(s['C']|s['D']),D_minus_C=s['D']-s['C'])
        for key in ['intersection','union','complement','D_minus_C']:assert len(s[key])==j[key]
        assert sum(j['opcodes'].values())==j['steps']
        assert j['diagonal_steps']==j['steps']-1-j['break4']-j['break40']-j['break_other']
        assert j['delta_segments']==1+j['break4']+j['break40']+j['break_other']
        h=rows(n,'segments');assert sum(int(x['count']) for x in h)==j['delta_segments'];assert sum(int(x['count'])*int(x['transition_length']) for x in h)==j['steps']-1
        out=(ROOT/'runs'/f'{n}.stdout.bin').read_bytes();j['output_sha256']=sha(out)
        src=ROOT/'programs'/f'{n}.mal'
        if n in ['m281','lutter','m284']:assert out==src.read_bytes();j['byte_exact_quine']=True
        ref=ROOT/'runs'/f'ref_{n}.command.stdout'
        if ref.exists():assert out==ref.read_bytes();j['matches_independent_mb_ref']=True
        if n=='cat':assert out==b'abc\n'
        if n=='cat_empty':assert out==b''
        if n in ['m281','lutter','m284']:
            sd=ROOT/'sets'/n;sd.mkdir(parents=True,exist_ok=True)
            for key,values in s.items():(sd/f'{key}.txt').write_text(''.join(f'{v}\n' for v in sorted(values)))
            final=rows(n,'samples')[-1];counts=rows(n,'counts');finalstep=j['steps'];fc=int(final['c']);fd=int(final['d']);assert fc!=fd
            assert int(counts[fc]['firstC'])==finalstep and int(counts[fd]['firstD'])<finalstep
            j['pre_halt_footprint']=dict(C=len(s['C'])-1,D=len(s['D']),union=len(s['union'])-1,complement=59049-len(s['union'])+1)
            j['flawed_symmetry_detector_vacuously_zero']=8*max(s['C'])+1>59049
        sets[n]=s;result[n]=j
    # Provenance control: fixed intersections and relocated Lutter loop overlap.
    fixed=sets['m281']['intersection']&sets['lutter']['intersection']&sets['m284']['intersection']
    moving={n:sets[n]['intersection']-fixed for n in ['m281','lutter','m284']}
    assert len(fixed)==49 and all(len(x)==47 for x in moving.values())
    assert {x+3102 for x in moving['m281']}==moving['lutter']
    assert {x+2820 for x in moving['m284']}==moving['lutter']
    result['provenance_overlap']=dict(fixed_count=49,fixed=sorted(fixed),relocated_count=47,m281_to_lutter_delta=3102,m284_to_lutter_delta=2820)
    external=json.loads((ROOT/'runs/external_m281.command.stdout').read_text());mainj=result['m281']
    for k in ['status','steps','cells_source','visited_c','visited_d','output_len','output_sha256','encryption_hits','delta_segments','opcodes']:assert external[k]==mainj[k],k
    assert external['visited_union']==mainj['union']
    py=json.loads((ROOT/'runs/journal_prefix_30000.json').read_text());c=json.loads((ROOT/'runs/m281_prefix.json').read_text());assert py['trace_sha256']==c['event_sha256']
    result['independent_python_C_prefix_hash_match']=True
    result['budget']=json.loads((ROOT/'budget.json').read_text())['allocated_steps']+60_000 # initial failed replay and corrected replay
    assert result['budget']<=400_000_000
    actual=30000+json.loads((ROOT/'runs/journal_replay_failed_v1.json').read_text())['completed_transitions']
    for meta in (ROOT/'runs').glob('*.command.json'):
        rec=json.loads(meta.read_text());name=rec['name']
        if name.startswith('build'):continue
        if name.startswith('external'):
            actual+=json.loads((ROOT/'runs'/f'{name}.command.stdout').read_text())['steps']
        else:
            key=name.removeprefix('ref_').removeprefix('observe_')
            actual+=json.loads((ROOT/'runs'/f'{key}.json').read_text())['steps']
    result['actual_completed_VM_instructions']=actual
    edges=[{k:int(v) for k,v in x.items()} for x in rows('m281','d_edges')]
    reach=dict(cell=53,observed_redirect_incoming=[x for x in edges if x['to_d_after_increment']==53],observed_redirect_outgoing=[x for x in edges if x['from_d']==53])
    (ROOT/'runs/journal53_reachability.json').write_text(json.dumps(reach,indent=2)+'\n')
    (ROOT/'budget_all.json').write_text(json.dumps(dict(allocated_steps=result['budget'],actual_completed_VM_instructions=result['actual_completed_VM_instructions'],runner_allocated_steps=result['budget']-60000,failed_replay_allocated_steps=30000,corrected_replay_allocated_steps=30000,per_child_timeout_seconds=120),indent=2)+'\n')
    (ROOT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,independently_recomputed_intersections={n:len(sets[n]['intersection']) for n in names},allocated_steps=result['budget'],python_C_prefix_hash_match=True),indent=2))
if __name__=='__main__':main()
