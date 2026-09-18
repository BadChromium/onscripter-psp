import unittest
from test_cp936_runtime import REPO
import test_audio_completion as completion
class ReplaceMemoryTest(unittest.TestCase):
 def test_actual_psp_loader_releases_before_allocate_except_preload(self):
  s=(REPO/'ONScripterLabel_sound.cpp').read_text();a=s.index('int ONScripterLabel::playOGG(');b=s.index('int ONScripterLabel::playExternalMusic',a)
  completion.AudioCompletionTest.compile_run(self,r'''
#include "ONSAudioGeneration.h"
#include <string.h>
#define PSP 1
#define SOUND_OTHER 0
#define SOUND_OGG 1
#define SOUND_OGG_STREAMING 2
#define SOUND_PRELOAD 4
struct OVInfo{bool completion_posted;unsigned playback_generation;long decoded_length;};
struct Mix_Chunk{};
ONSAudioGeneration ons_music_generation,ons_wave_generation[54];
Mix_Chunk prior,next;bool freed=false,halted=false,allocation_order_ok=false;int mode=0;unsigned old_token;
void SDL_LockAudio(){}void SDL_UnlockAudio(){}
int Mix_HaltChannel(int){halted=true;return 0;}
void Mix_FreeChunk(Mix_Chunk*c){if(c==&prior)freed=true;}
void pspDiagLog(const char*,...){}void Mix_VolumeMusic(int){}
void Mix_HookMusic(void(*)(void*,unsigned char*,int),void*){}
void oggcallback(void*,unsigned char*,int){}
class ONScripterLabel{public:
int pmf_sprite_no=-1;static void pumpPmfDuringDecode(void*){}
Mix_Chunk*wave_sample[54];OVInfo*music_ovi;int music_volume;
OVInfo*openOggVorbis(unsigned char*,long,int&ch,int&rate){ch=1;rate=44100;return new OVInfo();}
void closeOggVorbis(OVInfo*o){delete o;}
int playWave(Mix_Chunk*c,int,bool,int){return c?0:-1;}
int playOGG(int,unsigned char*,long,bool,int);
};
ONScripterLabel *owner;
Mix_Chunk*onsDecodePcmChunk(OVInfo*,int ch,void(*)(void*),void*){
 if(mode==1)allocation_order_ok=!freed&&!halted&&owner->wave_sample[ch]==&prior&&ons_wave_generation[ch].matches(old_token);
 else allocation_order_ok=freed&&halted&&owner->wave_sample[ch]==NULL&&!ons_wave_generation[ch].matches(old_token);
 return mode==2?NULL:&next;
}
'''+s[a:b]+r'''
int main(){ONScripterLabel ons;owner=&ons;unsigned char buf[8]={0};
for(mode=0;mode<3;++mode){
 freed=halted=allocation_order_ok=false;ons.wave_sample[0]=&prior;ons.wave_sample[1]=&next;
 old_token=ons_wave_generation[0].begin();unsigned other=ons_wave_generation[1].begin();
 ons.playOGG(SOUND_OGG|(mode==1?SOUND_PRELOAD:0),buf,8,false,0);
 if(!allocation_order_ok)return mode+1;
 if(ons.wave_sample[1]!=&next||!ons_wave_generation[1].matches(other))return 4;
}return 0;}
''')
if __name__=='__main__':unittest.main()
