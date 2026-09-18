import unittest,os
from pathlib import Path
import test_audio_completion as helper
REPO=Path(__file__).resolve().parents[1]
class MaskLifetimeTest(unittest.TestCase):
 def test_actual_effect_completion_releases_only_finished_masks(self):
  source=(Path(os.environ.get('MASK_ENGINE',str(REPO)))/'ONScripterLabel_effect.cpp').read_text();start=source.index('    effect_counter += effect_timer_resolution;');end=source.index('\nvoid ONScripterLabel::drawEffect',start);body=source[start:end]
  program=r'''#include <cassert>
#define PSP 1
#define RET_WAIT 1
#define RET_REREAD 2
#define RET_CONTINUE 0
#define REFRESH_NONE_MODE 0
#define IDLE_EVENT_MODE 0
struct Anim{void*image_surface=(void*)1;int freed=0;void deleteSurface(){image_surface=nullptr;freed++;}};
struct Effect{int effect=18,duration=100;Anim anim;};
struct Dirty{int bounding_box;}dirty_rect;
void SDL_BlitSurface(void*,int*,void*,int*){}
struct Engine{int effect_counter=0,effect_timer_resolution=1,event_mode=2;void*effect_dst_surface=nullptr;void*accumulation_surface=nullptr;
 void flush(int,void*unused=nullptr,bool flag=true){}
 int finish(int effect_no,Effect*effect){
'''+body+r'''
};
int main(){
 {Engine e;Effect f;assert(e.finish(18,&f)==3);assert(f.anim.image_surface&&f.anim.freed==0);e.effect_counter=99;assert(e.finish(18,&f)==0);assert(!f.anim.image_surface&&f.anim.freed==1);}
 {Engine e;Effect f;f.effect=15;e.effect_counter=99;assert(e.finish(15,&f)==0);assert(f.anim.freed==1);}
 {Engine e;Effect f;assert(e.finish(1,&f)==0);assert(f.anim.freed==1);}
 {Engine e;Effect f;f.effect=10;e.effect_counter=99;assert(e.finish(10,&f)==0);assert(f.anim.freed==0&&f.anim.image_surface);}
}
'''
  helper.AudioCompletionTest().compile_run(program)
if __name__=='__main__':unittest.main()
