from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import REPO,run_msvc
class PmfTimingTest(unittest.TestCase):
 def test_poll_wait_deducts_elapsed_and_stays_positive(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'timing.cpp';exe=p/'timing.exe'
   src.write_text('''#include "PSPPmfTiming.h"
int main(){
 if(pspPmfDelayAfterPublish(33,0,false)!=33)return 1;
 if(pspPmfDelayAfterPublish(33,12000,false)!=21)return 2;
 if(pspPmfDelayAfterPublish(33,33000,false)!=1)return 3;
 if(pspPmfDelayAfterPublish(33,90000,false)!=1)return 4;
 if(pspPmfDelayAfterPublish(33,0,true)!=1)return 5;
 if(pspPmfDelayAfterPublish(0,0,false)!=1)return 6;
 if(pspPmfDelayAfterPublish(999,0,false)!=100)return 7;
 unsigned int then=0xfffffff0u,now=0x00002700u;
 if(pspPmfDelayAfterPublish(33,now-then,false)!=23)return 8;
 return 0;
}''',encoding='ascii')
   r=run_msvc(f'cl /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
