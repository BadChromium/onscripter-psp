from pathlib import Path
import tempfile,subprocess,unittest
from test_cp936_runtime import REPO,run_msvc
class ExactMovieTest(unittest.TestCase):
 def test_exact_native_pixels_and_window(self):
  self.assertTrue((REPO/'PSPExactMovie.h').exists(),'exact compositor missing')
  program=r'''
#include "PSPExactMovie.h"
#include "PSPFastPixels.h"
#include <vector>
#include <stdint.h>
int main(){
 uint32_t seed=19;
 std::vector<uint32_t> movie(512*272);
 std::vector<uint16_t> bg(512*272),overlay(512*272),out(512*272,0xa55a);
 for(int i=0;i<512*272;i++){seed=seed*1664525+1013904223;movie[i]=seed;seed=seed*1664525+1013904223;bg[i]=seed;overlay[i]=seed>>16;}
 int rects[][4]={{4,164,472,108},{0,0,480,272},{0,271,480,1},{479,0,1,272},{17,91,221,53}};
 for(auto &r:rects){
  if(!pspExactMovieFrame(out.data(),movie.data(),bg.data(),overlay.data(),r[0],r[1],r[2],r[3]))return 1;
  for(int y=0;y<272;y++)for(int x=0;x<512;x++){
   int i=y*512+x;if(x>=480){if(out[i]!=0xa55a)return 2;continue;}
   uint16_t expected;
   if(x>=r[0]&&x<r[0]+r[2]&&y>=r[1]&&y<r[1]+r[3])expected=overlay[i];
   else{uint16_t d=pspSwap565(bg[i]),s=pspAbgrTo565(movie[i]);unsigned char a=255;pspBlend565Row(&d,&s,&a,1,256);expected=pspSwap565(d);}
   if(out[i]!=expected)return 3;
  }
 }
 if(pspExactMovieFrame(out.data(),movie.data(),bg.data(),overlay.data(),-1,0,10,10))return 4;
 return 0;
}'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'exact.cpp';p.write_text(program);e=Path(d)/'exact.exe'
   result=run_msvc(f'cl /nologo /EHsc /O2 /I"{REPO}" "{p}" /Fe:"{e}"',cwd=d)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   subprocess.run([str(e)],check=True)
