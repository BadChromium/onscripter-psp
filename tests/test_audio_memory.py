import unittest,tempfile,subprocess
from pathlib import Path
from test_cp936_runtime import REPO,run_msvc
class AudioMemoryTest(unittest.TestCase):
 def test_single_buffer_actual_length_and_ownership(self):
  helper=(REPO/'ONSPcmChunk.inc').read_text()
  body=r'''
#include <stdlib.h>
#include <string.h>
#include <limits.h>
typedef unsigned char Uint8;typedef unsigned int Uint32;
struct SDL_AudioCVT{int needed,len_mult,len,len_cvt;Uint8*buf;};
struct OVInfo{long decoded_length;SDL_AudioCVT cvt;};
struct Mix_Chunk{int allocated;Uint8*abuf;Uint32 alen;};
static int allocations=0,frees=0;static size_t capacity=0;
static long decoded=4;static bool fail_alloc=false,fail_convert=false,fail_chunk=false;
void pspDiagLog(const char*,...){}int SDL_SetError(const char*,...){return -1;}
void* SDL_malloc(size_t n){if(fail_alloc)return NULL;++allocations;capacity=n;return malloc(n);}
void SDL_free(void*p){if(p){++frees;free(p);}}
long decodeOggVorbis(OVInfo*,Uint8*p,long,bool){if(decoded>0)memset(p,7,decoded);return decoded;}
int SDL_ConvertAudio(SDL_AudioCVT*c){if(fail_convert)return -1;c->len_cvt=c->len*2;return 0;}
Mix_Chunk* Mix_QuickLoad_RAW(Uint8*p,Uint32 n){if(fail_chunk)return NULL;Mix_Chunk*c=new Mix_Chunk();c->abuf=p;c->alen=n;return c;}
void Mix_FreeChunk(Mix_Chunk*c){if(c->allocated)SDL_free(c->abuf);delete c;}
'''+helper+r'''
int main(){OVInfo o={8,{1,2,0,0,NULL}};
Mix_Chunk*c=onsDecodePcmChunk(&o,0);
if(!c||allocations!=1||capacity!=16||c->alen!=8||!c->allocated)return 1;
Mix_FreeChunk(c);if(frees!=1)return 2;
decoded=0;if(onsDecodePcmChunk(&o,0))return 3;
decoded=4;fail_convert=true;if(onsDecodePcmChunk(&o,0))return 4;fail_convert=false;
fail_chunk=true;if(onsDecodePcmChunk(&o,0))return 5;fail_chunk=false;
if(allocations!=frees)return 6;
fail_alloc=true;if(onsDecodePcmChunk(&o,0))return 7;fail_alloc=false;
o.decoded_length=LONG_MAX;if(onsDecodePcmChunk(&o,0))return 8;
o.decoded_length=8;o.cvt.needed=0;o.cvt.len_mult=1;
c=onsDecodePcmChunk(&o,0);if(!c||c->alen!=4)return 9;Mix_FreeChunk(c);
return allocations==frees?0:10;}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'check.cpp';e=Path(d)/'check.exe';p.write_text(body)
   r=run_msvc(f'cl /nologo /EHsc /O2 "{p}" /Fe:"{e}"',cwd=d)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   r=subprocess.run([str(e)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
if __name__=='__main__':unittest.main()
