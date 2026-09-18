#ifndef PSPAV_MP3_H
#define PSPAV_MP3_H

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C"{
#endif


void pspavPlayMP3File(char* filename, void* buffer, int buffer_size);
bool pspavIsMP3Active();
bool pspavIsMP3Paused();
void pspavStopMP3Playback();
void pspavResumeOrPauseMP3Playback();
void pspavPauseMP3Playback();
void pspavResumeMP3Playback();


#ifdef __cplusplus
}
#endif

#endif
