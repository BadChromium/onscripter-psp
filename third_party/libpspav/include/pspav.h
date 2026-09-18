#ifndef PSPAV_H
#define PSPAV_H

#include "pspav_entry.h"

#ifdef __cplusplus
extern "C"{
#endif

unsigned char pspavPlayGamePMF(PSPAVEntry* e, PSPAVCallbacks* callbacks, int x, int y);
int pspavPlayVideoFileOnce(const char* path, PSPAVCallbacks* callbacks);
int pspavPlayVideoFileLoop(const char* path, PSPAVCallbacks* callbacks);
void pspavPlayVideoFile(const char* path, PSPAVCallbacks* callbacks);

#ifdef __cplusplus
}
#endif

#endif
