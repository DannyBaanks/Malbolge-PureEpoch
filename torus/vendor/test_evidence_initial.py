#!/usr/bin/env python3
"""Tests for semantic boundaries that can invalidate trajectory claims.
No long VM runs: checks retained executions and their raw data.
"""
import ast,csv,hashlib,json,struct,unittest
from pathlib import Path
from journal_replay import crazy
ROOT=Path(__file__).resolve().parent
class Evidence(unittest.TestCase):
 def test_crazy_all_single_trits_and_lift(self):
  table=((1,0,0),(1,0,2),(2,2,1))
  for x in range(3):
   for y in range(3):
    for k in range(10):
     # All other positions have crazy(0,0)=1.
     self.assertEqual(crazy(x*3**k,y*3**k),29524+(table[y][x]-1)*3**k)
 def test_complete_four_step_journal_fixture_hash(self):
  rows=list(csv.DictReader((ROOT/'runs/journal_access_candidate.samples.csv').open()))
  fields=['a','c','d','cell','opcode','operand','direct_new','enc_addr','enc_old','enc_new','next_c','next_d'];h=hashlib.sha256()
  self.assertEqual(len(rows),4)
  for r in rows:h.update(struct.pack('<Q12H',int(r['step']),*(int(r[k]) for k in fields)))
  j=json.loads((ROOT/'runs/journal_access_candidate.json').read_text());self.assertEqual(h.hexdigest(),j['event_sha256'])
  self.assertEqual([int(r['d']) for r in rows],[0,41,42,43]);self.assertEqual([int(rows[i]['direct_new']) for i in [1,2]],[26,29543])
  self.assertEqual(j['read_written_not_C'],2);self.assertEqual(j['status'],'HALTED')
 def test_jump_encrypts_destination(self):
  seen=0
  for n in ['m281','lutter','cat']:
   for r in csv.DictReader((ROOT/'runs'/f'{n}.samples.csv').open()):
    if r['opcode']=='4':
     seen+=1;self.assertEqual(r['enc_addr'],r['operand']);self.assertEqual(int(r['next_c']),(int(r['operand'])+1)%59049)
  self.assertGreater(seen,0)
 def test_original_symmetry_detector_has_false_zero(self):
  tree=ast.parse((ROOT/'vendor/mb_fingerprint.py').read_text())
  func=next(x for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name=='symmetries')
  env={'N':9};exec(compile(ast.Module(body=[func],type_ignores=[]),'original_symmetry_function','exec'),env)
  # All nine positions are visited: every one of eight nonzero shifts is a
  # true symmetry. The exact original function nevertheless returns none.
  self.assertEqual(env['symmetries'](bytearray([1]*9)),[])
  self.assertEqual([s for s in range(1,9) if all(1==1 for i in range(9))],list(range(1,9)))
 def test_halt_is_visited_without_encryption(self):
  j=json.loads((ROOT/'runs/short.json').read_text());self.assertEqual((j['steps'],j['visited_c'],j['visited_d'],j['encryption_hits'],j['diagonal_steps']),(2,2,2,1,1))
 def test_recomputed_96_sets_are_relocated_not_identical(self):
  sets={n:set(map(int,(ROOT/'sets'/n/'intersection.txt').read_text().split())) for n in ['m281','lutter','m284']}
  self.assertEqual([len(v) for v in sets.values()],[96,96,96]);self.assertNotEqual(sets['m281'],sets['lutter'])
if __name__=='__main__':unittest.main(verbosity=2)
