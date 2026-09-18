from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import REPO,run_msvc
class RepeatTest(unittest.TestCase):
 def test_repeat_keeps_context_and_rewinds_only_between_passes(self):
  s=(REPO/'third_party/libpspav/src/pspav.c').read_text()
  marker='static int pspavRepeatVideoPasses(int repeat)'
  self.assertIn(marker,s)
  a=s.index(marker);b=s.index('{',a);depth=1;e=b+1
  while depth:
   depth+=(s[e]=='{')-(s[e]=='}');e+=1
  body=s[a:e]
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'repeat.cpp';exe=p/'repeat.exe'
   src.write_text('''#include <stdio.h>
int calls=0,seeks=0,aus=0,work=1,failseek=0,failplay=0;
int pspavfd=1,MPEGstart=2048,MPEGcounter=999,mps_header_injected=0;
int m_Mpeg=0,m_pEsBufferAVC=0,m_MpegAuAVC=0;
const int PSP_SEEK_SET=0,PAD_USER_CANCEL=1;
int pad(){return calls>=3?1:0;}
struct Callbacks{int(*getPadState)();} cb={pad},*av_callbacks=&cb;
int pspavPlay(){++calls;return failplay?-4:0;}
int sceIoLseek(int,int offset,int){++seeks;return failseek?-5:offset;}
int sceMpegInitAu(int*,int,int*){++aus;return 0;}
void pspDiagLog(const char*,...){}
'''+body+'''
int main(){
 if(pspavRepeatVideoPasses(0)||calls!=1||seeks||aus)return 1;
 calls=seeks=aus=0;
 if(pspavRepeatVideoPasses(1)||calls!=3||seeks!=2||aus!=2||MPEGcounter!=MPEGstart)return 2;
 calls=seeks=aus=0;failseek=1;
 if(pspavRepeatVideoPasses(1)!=-5||calls!=1||aus)return 3;
 failseek=0;failplay=1;calls=seeks=0;
 if(pspavRepeatVideoPasses(1)!=-4||calls!=1||seeks)return 4;
 return 0;
}''',encoding='ascii')
   r=run_msvc(f'cl /nologo "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
