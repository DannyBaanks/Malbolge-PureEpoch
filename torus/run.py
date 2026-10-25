#!/usr/bin/env python3
"""Reproduce bounded toroidal observations. All writes stay in this directory.
Every child command has a 120-second timeout. No existing run is overwritten.
Worst-case VM allocation of this runner: 395,170,192 steps (<400M).
"""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
LOCAL=ROOT.parents[1]/'BolgeForge'
REMOTE=ROOT.parent/'sources/BolgeForge'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def execute(name,cmd,stdin=b'',budget=0):
    meta=ROOT/'runs'/f'{name}.command.json'
    if meta.exists():return json.loads(meta.read_text())
    start=time.monotonic()
    try:
        r=subprocess.run(cmd,input=stdin,capture_output=True,timeout=120,cwd=ROOT)
        stdout,stderr,code,timeout=r.stdout,r.stderr,r.returncode,False
    except subprocess.TimeoutExpired as e:
        stdout,stderr,code,timeout=e.stdout or b'',e.stderr or b'',None,True
    (ROOT/'runs'/f'{name}.command.stdout').write_bytes(stdout)
    (ROOT/'runs'/f'{name}.command.stderr').write_bytes(stderr)
    info=dict(name=name,command=list(map(str,cmd)),input_sha256=hashlib.sha256(stdin).hexdigest(),allocated_steps=budget,returncode=code,timeout=timeout,seconds=round(time.monotonic()-start,6))
    meta.write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info),flush=True);return info
def main():
    inputs={'m281':'artifacts/candidate_m281_53562b.mal','lutter':'reference/quine_lutter.malbolge','m284':'artifacts/candidate_m284_54134b.mal','cat':'reference/malbolge_org/cat.mal'}
    manifest={}
    for name,rel in inputs.items():
        dest=ROOT/'programs'/f'{name}.mal'
        if not dest.exists():shutil.copyfile(LOCAL/rel,dest)
        manifest[name]=dict(path=str(dest),local_source=str(LOCAL/rel),sha256=sha(dest),remote_sha256=sha(REMOTE/rel) if (REMOTE/rel).exists() else None)
    (ROOT/'programs'/'short.mal').write_bytes(b'DP')
    manifest['short']=dict(path=str(ROOT/'programs/short.mal'),sha256=sha(ROOT/'programs/short.mal'),definition='Two loader-valid cells: numeric op68 then op81; no input.')
    (ROOT/'programs'/'journal_access_candidate.mal').write_bytes(b'(&<N')
    manifest['journal_access_candidate']=dict(path=str(ROOT/'programs/journal_access_candidate.mal'),sha256=sha(ROOT/'programs/journal_access_candidate.mal'),definition='Four loader-valid cells: j,* ,p,v. Demonstrates read/modify access at D-only cells 41 and 42. Does not compare or recover.')
    for f in ['vendor/mb_ref.c','vendor/mb_fingerprint.py','observe.c','run.py']:
        manifest[f]=dict(sha256=sha(ROOT/f))
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    execute('build_ref',['gcc','-O3','-std=c11','-Wall','-Wextra','vendor/mb_ref.c','-o','mb_ref'])
    execute('build_observe',['gcc','-O3','-std=c11','-Wall','-Wextra','-Wno-deprecated-declarations','observe.c','-lcrypto','-o','observe'])
    # Independent strict oracles: no observational modifications to the copied C.
    for name,budget in [('m281',63_000_000),('lutter',70_000_000),('cat',1_000_000),('short',32)]:
        execute('ref_'+name,[str(ROOT/'mb_ref'),str(ROOT/'programs'/f'{name}.mal'),str(budget)],b'abc\n' if name=='cat' else b'',budget)
    for name,budget in [('m281',63_000_000),('lutter',70_000_000),('m284',64_000_000),('cat',1_000_000),('short',32)]:
        execute('observe_'+name,[str(ROOT/'observe'),str(ROOT/'programs'/f'{name}.mal'),str(budget),str(ROOT/'runs'/name)],b'abc\n' if name=='cat' else b'',budget)
    execute('ref_cat_empty',[str(ROOT/'mb_ref'),str(ROOT/'programs/cat.mal'),'20000'],budget=20_000)
    execute('observe_cat_empty',[str(ROOT/'observe'),str(ROOT/'programs/cat.mal'),'20000',str(ROOT/'runs/cat_empty')],budget=20_000)
    name='journal_access_candidate'
    execute('ref_'+name,[str(ROOT/'mb_ref'),str(ROOT/'programs'/f'{name}.mal'),'32'],budget=32)
    execute('observe_'+name,[str(ROOT/'observe'),str(ROOT/'programs'/f'{name}.mal'),'32',str(ROOT/'runs'/name)],budget=32)
    # Execute original unmodified script once on the headline quine. Python's
    # no-input behavior and EOF=-1 are retained; preserve timeout if it occurs.
    for name,budget in [('m281',63_000_000),('cat',100_000),('short',32)]:
        execute('external_'+name,['python3',str(ROOT/'vendor/mb_fingerprint.py'),str(ROOT/'programs'/f'{name}.mal'),str(budget)],budget=budget)
    execute('external_journal_access_candidate',['python3',str(ROOT/'vendor/mb_fingerprint.py'),str(ROOT/'programs/journal_access_candidate.mal'),'32'],budget=32)
    execute('observe_m281_prefix',[str(ROOT/'observe'),str(ROOT/'programs/m281.mal'),'30000',str(ROOT/'runs/m281_prefix')],budget=30_000)
    (ROOT/'binary_hashes.json').write_text(json.dumps({n:sha(ROOT/n) for n in ['mb_ref','observe']},indent=2)+'\n')
    records=[json.loads(p.read_text()) for p in (ROOT/'runs').glob('*.command.json')]
    (ROOT/'budget.json').write_text(json.dumps(dict(command_timeout_seconds=120,allocated_steps=sum(r['allocated_steps'] for r in records),commands=records),indent=2)+'\n')
if __name__=='__main__':main()
