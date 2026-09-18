import unittest
from pathlib import Path
import test_audio_completion as helper
REPO=Path(__file__).resolve().parents[1]
class HandoverTest(unittest.TestCase):
 def test_actual_lsp_preserves_only_compatible_live_movie_frame(self):
  s=(REPO/'ONScripterLabel_command.cpp').read_text();a=s.index('int ONScripterLabel::lspCommand()');b=s.index('int ONScripterLabel::loopbgmstopCommand()',a)
  helper.AudioCompletionTest().compile_run(r'''
#include <assert.h>
#include <string.h>
#define RET_CONTINUE 0
struct Pos{int x=0,y=0;};
struct AnimationInfo{enum{TRANS_PMF=9,TRANS_ALPHA=1};bool visible=true;int trans_mode=TRANS_PMF,trans=256;void*image_surface=(void*)1;Pos pos;int frame=123;const char*name="";void setImageName(const char*n){name=n;}void fill(int,int,int,int){frame=0;}};
struct ScriptHandler{enum{END_COMMA=1};int calls=0,x=0,y=0;bool hidden=false,pmf=true;bool isName(const char*){return hidden;}int readInt(){return calls++==0?5:(calls==2?x:y);}const char*readStr(){return pmf?":v;next.pmf":":a;next.png";}int getEndStatus(){return 0;}};
struct Dirty{void add(Pos){}};
class ONScripterLabel{public:ScriptHandler script_h;AnimationInfo sprite_info[6];Dirty dirty_rect;int pmf_sprite_no=5,pmf_sprite_last_serial=7,screen_ratio1=1,screen_ratio2=1,setups=0,starts=0,stops=0,result=0;
void stopPmfSprite(int){++stops;pmf_sprite_no=-1;pmf_sprite_last_serial=0;}
void parseTaggedString(AnimationInfo*a){a->trans_mode=script_h.pmf?AnimationInfo::TRANS_PMF:AnimationInfo::TRANS_ALPHA;}
void setupAnimationInfo(AnimationInfo*a){++setups;a->frame=0;}
int startPmfSprite(int,AnimationInfo*){++starts;return result;}
int lspCommand();};
'''+s[a:b]+r'''
int main(){
{ONScripterLabel x;x.lspCommand();assert(x.setups==0 && x.sprite_info[5].frame==123);assert(x.starts==1 && x.stops==1);}
{ONScripterLabel x;x.script_h.pmf=false;x.lspCommand();assert(x.setups==1 && x.starts==0);}
{ONScripterLabel x;x.sprite_info[5].visible=false;x.lspCommand();assert(x.setups==1);}
{ONScripterLabel x;x.pmf_sprite_last_serial=0;x.lspCommand();assert(x.setups==1);}
{ONScripterLabel x;x.script_h.x=4;x.lspCommand();assert(x.setups==1);}
{ONScripterLabel x;x.result=-1;x.lspCommand();assert(x.sprite_info[5].frame==0);}
return 0;}
''')
if __name__=='__main__':unittest.main()
