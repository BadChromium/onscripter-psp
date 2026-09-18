from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import REPO,run_msvc
class BackgroundCacheTest(unittest.TestCase):
 def test_movie_tick_does_not_copy_decoder_frame_twice(self):
  source=(REPO/'ONScripterLabel_image.cpp').read_text()
  start=source.index('void ONScripterLabel::refreshSurface(')
  start=source.index('{',start)+1
  end=source.index('SDL_Rect clip',start)
  prefix=source[start:end]
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'refresh.cpp';exe=p/'refresh.exe'
   src.write_text('''#include "PSPBackgroundCache.h"
bool pmf_refresh_only=false; PSPBackgroundCache pmf_background_cache;
int copies=0; const int REFRESH_NONE_MODE=0;
void updatePmfSpriteFrame(){++copies;}
void refresh(int refresh_mode){'''+prefix+'''}
int main(){refresh(1);if(copies!=1)return 1;
pmf_refresh_only=true;refresh(1);if(copies!=1)return 2;
pmf_refresh_only=false;refresh(0);return copies==1?0:3;}
''',encoding='ascii')
   r=run_msvc(f'cl /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
 def test_exact_pitched_restore_invalidation_and_resize(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d); src=p/'cache.cpp'; exe=p/'cache.exe'
   src.write_text(r'''#include "PSPBackgroundCache.h"
int main(){
 PSPBackgroundCache c;
 unsigned short a[21],b[27];
 for(int i=0;i<21;++i)a[i]=(unsigned short)(i*3137);
 for(int i=0;i<27;++i)b[i]=0xabcd;
 if(c.restore(b,18,4,3))return 1;
 if(!c.capture(a,14,4,3))return 2;
 if(c.restore(b,18,5,3))return 3;
 if(!c.restore(b,18,4,3))return 4;
 for(int y=0;y<3;++y)for(int x=0;x<9;++x)
  if(b[y*9+x]!=(x<4?a[y*7+x]:0xabcd))return 5;
 c.invalidate(); if(c.restore(b,18,4,3))return 6;
 if(!c.capture(a,14,3,2)||!c.restore(b,18,3,2))return 7;
 if(c.capture(a,2,3,2)||c.restore(b,18,3,2))return 8;
 return 0;
}''',encoding='ascii')
   r=run_msvc(f'cl /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
