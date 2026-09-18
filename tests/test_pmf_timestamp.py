from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import REPO,run_msvc
class TimestampTest(unittest.TestCase):
 def test_published_frames_use_current_pts_without_synthetic_zero(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'pts.cpp';exe=p/'pts.exe'
   src.write_text('''#include "third_party/libpspav/include/pspav_timing.h"
int main(){
 if(pspavPresentationTimestamp(90000,0,1)!=90000)return 1;
 if(pspavPresentationTimestamp(93003,90000,1)!=93003)return 2;
 if(pspavPresentationTimestamp(90000,0,0)!=0)return 3;
 if(pspavPresentationTimestamp(93003,90000,0)!=90000)return 4;
 return 0;
}''',encoding='ascii')
   r=run_msvc(f'cl /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
