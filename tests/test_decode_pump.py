import unittest,tempfile,subprocess
from pathlib import Path
from test_cp936_runtime import REPO,run_msvc
class DecodePumpTest(unittest.TestCase):
 def test_bounded_decode_keeps_one_allocation_and_services_progress(self):
  helper=(REPO/'ONSPcmChunk.inc').read_text()
  body=r'''
#include <stdlib.h>
#include <string.h>
typedef unsigned char Uint8;typedef unsigned int Uint32;
struct SDL_AudioCVT{int needed,len_mult,len,len_cvt;Uint8*buf;};
struct OVInfo{long decoded_length;SDL_AudioCVT cvt;};
struct Mix_Chunk{int allocated;Uint8*abuf;Uint32 alen;};
int allocs=0,frees=0,pumps=0,calls=0;long remaining=20001;bool bad=false;
void pspDiagLog(const char*,...){}int SDL_SetError(const char*,...){return -1;}
void* SDL_malloc(size_t n){++allocs;return malloc(n);}void SDL_free(void*p){++frees;free(p);}
long decodeOggVorbis(OVInfo*,Uint8*p,long n,bool){++calls;if(n>8192)bad=true;long got=n<remaining?n:remaining;memset(p,7,got);remaining-=got;return got;}
int SDL_ConvertAudio(SDL_AudioCVT*c){c->len_cvt=c->len;return 0;}
Mix_Chunk* Mix_QuickLoad_RAW(Uint8*p,Uint32 n){Mix_Chunk*c=new Mix_Chunk();c->abuf=p;c->alen=n;return c;}
void progress(void*ctx){++*static_cast<int*>(ctx);}
'''+helper+r'''
int main(){OVInfo o={20001,{0,1,0,0,NULL}};
Mix_Chunk*c=onsDecodePcmChunk(&o,0,progress,&pumps);
if(!c||bad||allocs!=1||calls<3||pumps<3||c->alen!=20001||!c->allocated)return 1;
for(unsigned i=0;i<c->alen;++i)if(c->abuf[i]!=7)return 2;
SDL_free(c->abuf);delete c;
remaining=4000;pumps=0;c=onsDecodePcmChunk(&o,0,progress,&pumps);
if(!c||c->alen!=4000||pumps<1)return 3;
SDL_free(c->abuf);delete c;remaining=0;
if(onsDecodePcmChunk(&o,0,progress,&pumps))return 4;
return allocs==frees?0:5;}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'check.cpp';e=Path(d)/'check.exe';p.write_text(body)
   r=run_msvc(f'cl /nologo /EHsc /O2 "{p}" /Fe:"{e}"',cwd=d);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   r=subprocess.run([str(e)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
