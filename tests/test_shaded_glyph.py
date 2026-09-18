from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import REPO,run_msvc
class ShadedGlyphTest(unittest.TestCase):
 def test_shaded_glyph_copies_pixmap_when_mono_bitmap_is_uncached(self):
  source=(REPO/'third_party/sdl-ttf/SDL_ttf.c').read_text()
  body=source.split('SDL_Surface* TTF_RenderGlyph_Shaded(',1)[1]
  copy=body.split('/* Copy the character from the pixmap */',1)[1].split('/* Handle the underline style */',1)[0]
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'glyph.cpp';exe=p/'glyph.exe'
   src.write_text('''#include <string.h>
typedef unsigned char Uint8;
struct Bitmap {int rows,width,pitch;Uint8 *buffer;};
struct Glyph {Bitmap bitmap,pixmap;};
struct Surface {void *pixels;int pitch;};
int main(){
Uint8 pixels[8]={1,2,3,99,4,5,6,99},output[10]={0};
Glyph value={{0,0,0,0},{2,3,4,pixels}};Glyph *glyph=&value;
Surface surface={output,5};Surface *textbuf=&surface;
Uint8 *src,*dst;int row;
'''+copy+'''
if(memcmp(output,"\\1\\2\\3\\0\\0\\4\\5\\6\\0\\0",10))return 1;
return 0;}
''',encoding='ascii')
   r=run_msvc(f'cl /nologo "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0,'Shaded glyph copied no ink when only pixmap was loaded')
if __name__=='__main__':unittest.main()
