#ifndef ONS_AUDIO_GENERATION_H
#define ONS_AUDIO_GENERATION_H
#include <stdint.h>
class ONSAudioGeneration{
 uint32_t id;bool active;
public:
 ONSAudioGeneration():id(0),active(false){}
 uint32_t begin(){if(!++id)++id;active=true;return id;}
 void retire(){active=false;}
 uint32_t token()const{return id;}
 bool matches(uint32_t token)const{return active&&token!=0&&token==id;}
};
#endif
