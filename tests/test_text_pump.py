import unittest,tempfile,subprocess
from pathlib import Path
from test_cp936_runtime import REPO,run_msvc
class TextPumpTest(unittest.TestCase):
 def test_typewriter_delay_services_pmf_without_changing_delay(self):
  s=(REPO/'ONScripterLabel_text.cpp').read_text(encoding='latin1');a=s.rindex('            event_mode = WAIT_SLEEP_MODE;');b=s.index('            return RET_WAIT | RET_NOREAD;',a)+len('            return RET_WAIT | RET_NOREAD;')
  # Include any service inserted immediately after the event-mode assignment.
  block=s[a:b]
  body=r'''
#define PSP 1
#define WAIT_SLEEP_MODE 1
#define RET_WAIT 2
#define RET_NOREAD 4
class ONScripterLabel{public:
int event_mode=0,default_text_speed[1]={20},text_speed_no=0,delay=0,pumps=0;
struct {int wait_time;} sentence_font;
void advancePhase(int n){delay=n;}
static void pumpPmfDuringDecode(void*p){++static_cast<ONScripterLabel*>(p)->pumps;}
int renderDelay(){
'''+block+r'''
}};
int main(){ONScripterLabel o;o.sentence_font.wait_time=20;o.renderDelay();
if(o.pumps!=1||o.delay!=20||o.event_mode!=WAIT_SLEEP_MODE)return 1;
o.sentence_font.wait_time=-1;o.renderDelay();return o.pumps==2&&o.delay==20?0:2;}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'test.cpp';e=Path(d)/'test.exe';p.write_text(body)
   r=run_msvc(f'cl /nologo /EHsc /O2 "{p}" /Fe:"{e}"',cwd=d);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   r=subprocess.run([str(e)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
