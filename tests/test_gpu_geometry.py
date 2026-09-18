from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import REPO,run_msvc
class GpuGeometryTest(unittest.TestCase):
 def test_slices_cover_rectangle_without_overread(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'gpu.cpp';exe=p/'gpu.exe'
   src.write_text('''#include "PSPGpuGeometry.h"
int main(){
 if(!pspGpuWindowFits(4,164,472,108)||pspGpuWindowFits(-1,0,10,10)||pspGpuWindowFits(0,0,481,272))return 1;
 for(int x=0;x<480;++x)for(int w=1;w<=480-x;++w){
  int end=x+w,total=0;
  for(int a=x;a<end;){int b=pspGpuSliceEnd(a,end);if(b<=a||b>end||b-a>32)return 2;total+=b-a;a=b;}
  if(total!=w)return 3;
 }
 return 0;
}''',encoding='ascii')
   r=run_msvc(f'cl /O2 /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
