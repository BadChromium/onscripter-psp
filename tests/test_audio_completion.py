import unittest,tempfile,subprocess
from pathlib import Path
from test_cp936_runtime import REPO,run_msvc
class AudioCompletionTest(unittest.TestCase):
 def compile_run(self,body):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'test.cpp';p.write_text(body);exe=Path(d)/'test.exe'
   r=run_msvc(f'cl /nologo /EHsc /I"{REPO}" "{p}" /Fe:"{exe}"',d)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   r=subprocess.run([str(exe)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_real_ogg_callback_posts_only_one_completion(self):
  s=(REPO/'ONScripterLabel_event.cpp').read_text();a=s.index('extern "C" void oggcallback');b=s.index('extern "C" Uint32 timerCallback',a)
  self.compile_run(r'''
#include <stdint.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char Uint8;typedef uint32_t Uint32;
struct OVInfo{bool completion_posted;Uint32 playback_generation;};
struct SDL_Event{int type;struct{int code;void *data1;void *data2;}user;};
#define ONS_SOUND_EVENT 1
#define ONS_OGG_COMPLETION 0x4f4747
int posts=0;bool fail=false;
int SDL_PushEvent(SDL_Event*){if(fail)return -1;++posts;return 0;}
long decodeOggVorbis(OVInfo*,Uint8*,int,bool){return 0;}
void pspDiagAudioPcm(Uint8*,int,long){}
'''+s[a:b]+r'''
int main(){OVInfo o={false,1};Uint8 buf[8]={0};
for(int i=0;i<32;i++)oggcallback(&o,buf,8);
if(posts!=1){printf("expected one EOF event, got %d",posts);return 1;}
OVInfo next={false,2};fail=true;oggcallback(&next,buf,8);fail=false;oggcallback(&next,buf,8);
if(posts!=2)return 2;return 0;}
''')
 def test_real_voice_loader_uses_actual_decoded_length(self):
  s=(REPO/'ONScripterLabel_sound.cpp').read_text();a=s.index('int ONScripterLabel::playOGG(');b=s.index('int ONScripterLabel::playExternalMusic',a)
  self.compile_run(r'''
#include "ONSAudioGeneration.h"
#include <string.h>
struct OVInfo{long decoded_length;bool completion_posted;unsigned playback_generation;};
struct Mix_Chunk{};char WAVE_HEADER[44];long actual=4,header_size=0,rw_size=0;
#define SOUND_OTHER 0
#define SOUND_OGG 1
#define SOUND_OGG_STREAMING 2
ONSAudioGeneration ons_music_generation;
void pspDiagLog(const char*,...){}
long decodeOggVorbis(OVInfo*,unsigned char*,long,bool){return actual;}
typedef void SDL_RWops;
void* SDL_RWFromMem(void*,long n){rw_size=n;return 0;}
Mix_Chunk* Mix_LoadWAV_RW(void*,int){static Mix_Chunk c;return &c;}
void Mix_VolumeMusic(int){}void Mix_HookMusic(void(*)(void*,unsigned char*,int),void*){}
void oggcallback(void*,unsigned char*,int){}
class ONScripterLabel{public:
OVInfo *music_ovi;int music_volume;
OVInfo* openOggVorbis(unsigned char*,long,int&ch,int&rate){ch=1;rate=44100;OVInfo* o=new OVInfo();o->decoded_length=8;return o;}
void setupWaveHeader(unsigned char*,int,int,long n){header_size=n;}
void closeOggVorbis(OVInfo*o){delete o;}
int playWave(Mix_Chunk*,int,bool,int){return 0;}
int playOGG(int,unsigned char*,long,bool,int);
};
'''+s[a:b]+r'''
int main(){ONScripterLabel ons;unsigned char b[8]={0};ons.playOGG(SOUND_OGG,b,8,false,0);
if(header_size!=4||rw_size!=48)return 1;
header_size=rw_size=0;actual=0;ons.playOGG(SOUND_OGG,b,8,false,0);
if(header_size||rw_size)return 2;return 0;}
''')
 def test_real_dispatch_rejects_stale_voice_and_music(self):
  impl=(REPO/'ONSAudioEvents.inc').read_text()
  self.compile_run(r'''
#include "ONSAudioGeneration.h"
#include <stdint.h>
#define ONS_MIX_CHANNELS 50
#define ONS_MIX_EXTRA_CHANNELS 4
#define ONS_SOUND_EVENT 1
#define ONS_WAVE_EVENT 2
#define ONS_OGG_COMPLETION 0x4f4747
struct Mix_Chunk{};
struct SDL_Event{int type;struct{int code;void*data1;}user;};
class ONScripterLabel{public:bool isCurrentAudioEvent(const SDL_Event&);};
int Mix_HaltChannel(int){return 0;}void SDL_LockAudio(){}void SDL_UnlockAudio(){}
int Mix_PlayChannel(int ch,Mix_Chunk*,int){return ch;}
'''+impl+r'''
int main(){ONScripterLabel ons;Mix_Chunk chunk;
onsPlayChannel(0,&chunk,0);SDL_Event old={ONS_WAVE_EVENT,{0,(void*)(uintptr_t)ons_wave_generation[0].token()}};
onsPlayChannel(0,&chunk,0);if(ons.isCurrentAudioEvent(old))return 1;
old.user.data1=(void*)(uintptr_t)ons_wave_generation[0].token();if(!ons.isCurrentAudioEvent(old))return 2;
ons_wave_generation[0].retire();if(ons.isCurrentAudioEvent(old))return 3;
SDL_Event music={ONS_SOUND_EVENT,{ONS_OGG_COMPLETION,(void*)(uintptr_t)ons_music_generation.begin()}};
ons_music_generation.begin();if(ons.isCurrentAudioEvent(music))return 4;
return 0;}
''')
  s=(REPO/'ONScripterLabel_event.cpp').read_text()
  self.assertIn('if(!isCurrentAudioEvent(event))continue;',s)
  self.assertIn('if(!isCurrentAudioEvent(event)) return;',s)
 def test_generation_rejects_replaced_and_duplicate_completion(self):
  self.assertTrue((REPO/'ONSAudioGeneration.h').exists())
  self.compile_run(r'''
#include "ONSAudioGeneration.h"
int main(){ONSAudioGeneration g;unsigned a=g.begin();if(!g.matches(a))return 1;
unsigned b=g.begin();if(g.matches(a)||!g.matches(b))return 2;
g.retire();if(g.matches(b))return 3;
return 0;}
''')
