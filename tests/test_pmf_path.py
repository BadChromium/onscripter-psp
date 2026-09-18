from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import run_msvc,REPO
class PmfPathTest(unittest.TestCase):
 def test_compiled_native_path_accepts_ons_separators_and_rejects_truncation(self):
  self.assertTrue((REPO/'PSPPmfPath.h').exists(),'native PMF path normalization is missing')
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'path.cpp';exe=p/'path.exe'
   src.write_text(r'''#include "PSPPmfPath.h"
#include <string.h>
int main(){char out[256];
if(!pspPmfCopyPath(out,sizeof(out),"movie\\ha01_01.pmf"))return 1;
if(strcmp(out,"movie/ha01_01.pmf"))return 2;
if(!pspPmfCopyPath(out,sizeof(out),"MOVIE/A.PMF"))return 3;
if(strcmp(out,"MOVIE/A.PMF"))return 4;
if(pspPmfCopyPath(out,2,"abc"))return 5;
if(pspPmfCopyPath(out,sizeof(out),""))return 6;
return 0;}''',encoding='ascii')
   r=run_msvc(f'cl /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
 def test_resolves_worker_paths_against_parent_game_directory(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'resolve.cpp';exe=p/'resolve.exe'
   src.write_text(r'''#include "PSPPmfPath.h"
#include <string.h>
int main(){char out[256];
if(!pspPmfResolvePath(out,sizeof(out),"movie\\ha01_01.pmf","ms0:/PSP/GAME/TESTGAME"))return 1;
if(strcmp(out,"ms0:/PSP/GAME/TESTGAME/movie/ha01_01.pmf"))return 2;
if(!pspPmfResolvePath(out,sizeof(out),"movie/A.PMF","umd0:"))return 3;
if(strcmp(out,"umd0:/movie/A.PMF"))return 4;
if(!pspPmfResolvePath(out,sizeof(out),"movie/A.PMF","ms0:/PSP/GAME/TESTGAME/"))return 5;
if(strcmp(out,"ms0:/PSP/GAME/TESTGAME/movie/A.PMF"))return 6;
if(!pspPmfResolvePath(out,sizeof(out),"ef0:/Movie/A.PMF",0))return 7;
if(strcmp(out,"ef0:/Movie/A.PMF"))return 8;
if(!pspPmfResolvePath(out,sizeof(out),"/Movie/A.PMF","ms0:/PSP/GAME/TESTGAME"))return 9;
if(strcmp(out,"ms0:/Movie/A.PMF"))return 10;
if(pspPmfResolvePath(out,sizeof(out),"movie/A.PMF",0))return 11;
if(pspPmfResolvePath(out,sizeof(out),"movie/A.PMF","relative"))return 12;
if(pspPmfResolvePath(out,8,"movie/A.PMF","ms0:"))return 13;
if(pspPmfResolvePath(out,sizeof(out),"","ms0:"))return 14;
if(pspPmfResolvePath(0,sizeof(out),"a","ms0:"))return 15;
if(!pspPmfResolvePath(out,9,"a","ms0:/x"))return 16;
if(strcmp(out,"ms0:/x/a"))return 17;
if(pspPmfResolvePath(out,8,"a","ms0:/x"))return 18;
return 0;}''',encoding='ascii')
   r=run_msvc(f'cl /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
if __name__=='__main__':unittest.main()
