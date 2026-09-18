import unittest
from test_cp936_runtime import REPO
import test_audio_completion as completion
class ReaderEofRaceTest(unittest.TestCase):
 def test_abort_between_status_check_and_eof_store_is_preserved(self):
  src=(REPO/'third_party/libpspav/src/pspav_reader.c').read_text()
  a=src.index('        if (D->m_TotalBytes >= D->m_StreamSize')
  b=src.index('    }\n\n    sceKernelSignalSema',a)
  block=src[a:b]
  completion.AudioCompletionTest.compile_run(self,r'''
#include <stdio.h>
enum{ReaderThreadData__READER_OK=0,ReaderThreadData__READER_EOF=1,ReaderThreadData__READER_ABORT=2};
bool enabled=true,inject=false,pending=false;
struct Status{int value;operator int(){int snapshot=value;
 if(inject){inject=false;if(enabled)value=ReaderThreadData__READER_ABORT;else pending=true;}
 return snapshot;}
 Status& operator=(int x){value=x;return *this;}
};
struct ReaderThreadData{int m_TotalBytes,m_StreamSize;Status m_Status;};
ReaderThreadData *active;
int sceKernelCpuSuspendIntr(){int old=enabled;enabled=false;return old;}
void sceKernelCpuResumeIntr(int state){enabled=state;if(enabled&&pending){active->m_Status.value=ReaderThreadData__READER_ABORT;pending=false;}}
void markEof(ReaderThreadData*D){
'''+block+r'''
}
int main(){ReaderThreadData d={100,100,{0}};active=&d;
markEof(&d);if(d.m_Status.value!=ReaderThreadData__READER_EOF)return 1;
d.m_Status.value=ReaderThreadData__READER_ABORT;markEof(&d);if(d.m_Status.value!=2)return 2;
d.m_Status.value=0;inject=true;markEof(&d);
if(d.m_Status.value!=2){printf("abort overwritten by EOF: status=%d",d.m_Status.value);return 3;}
if(!enabled||pending)return 4;
enabled=false;d.m_Status.value=0;markEof(&d);if(enabled||d.m_Status.value!=1)return 5;
enabled=true;d.m_TotalBytes=99;d.m_Status.value=0;markEof(&d);if(d.m_Status.value!=0)return 6;
return 0;}
''')
if __name__=='__main__':unittest.main()
