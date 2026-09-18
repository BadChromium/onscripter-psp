import unittest,tempfile,subprocess
from pathlib import Path
from test_cp936_runtime import REPO,run_msvc
class PumpSchedulerTest(unittest.TestCase):
 def test_actual_pump_yields_throttles_and_restores_refresh_flag(self):
  s=(REPO/'ONScripterLabel_animation.cpp').read_text();a=s.index('void ONScripterLabel::pumpPmfDuringDecode');b=s.index('int ONScripterLabel::updatePmfSpriteFrame',a)
  body=r'''
#define PSP 1
#define REFRESH_CURSOR_MODE 4
typedef unsigned int Uint32;
Uint32 ticks=100;int yields=0,flushes=0;bool yielded=false;
Uint32 SDL_GetTicks(){return ticks;}void SDL_Delay(int n){if(n==1){++yields;yielded=true;}}
struct Sprite{bool visible;int pos;};
class ONScripterLabel{public:
int pmf_sprite_no=0,pmf_sprite_last_serial=0;bool all_sprite_hide_flag=false,pmf_refresh_only=false,draw_cursor_flag=false;Sprite sprite_info[1]={{true,0}};
void updatePmfSpriteFrame(){if(yielded){++pmf_sprite_last_serial;yielded=false;}}
void flushDirect(int,int){if(pmf_refresh_only)++flushes;}
int refreshMode(){return 1;}
static void pumpPmfDuringDecode(void*);
};
'''+s[a:b]+r'''
int main(){ONScripterLabel o;o.pumpPmfDuringDecode(&o);
if(yields!=1||flushes!=1||o.pmf_refresh_only)return 1;
ticks=150;o.pumpPmfDuringDecode(&o);if(yields!=1)return 2;
ticks=170;o.pmf_refresh_only=true;o.pumpPmfDuringDecode(&o);
if(yields!=2||flushes!=2||!o.pmf_refresh_only)return 3;
ticks=300;o.all_sprite_hide_flag=true;o.pumpPmfDuringDecode(&o);if(yields!=2)return 4;
o.all_sprite_hide_flag=false;o.pmf_sprite_no=-1;o.pumpPmfDuringDecode(&o);return yields==2?0:5;}
'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'test.cpp';e=Path(d)/'test.exe';p.write_text(body)
   r=run_msvc(f'cl /nologo /EHsc /O2 "{p}" /Fe:"{e}"',cwd=d);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   r=subprocess.run([str(e)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
