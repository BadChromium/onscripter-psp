#ifndef PSP_PMF_PLAYER_H
#define PSP_PMF_PLAYER_H

#include <SDL/SDL.h>

int pspPmfPlayVideoOnce(const char *filename, bool click_flag,
                        SDL_Surface *screen_surface);
int pspPmfLayerStart(const char *filename);
void pspPmfLayerStop();
bool pspPmfLayerIsRunning();
int pspPmfLayerCopyFrame(SDL_Surface *surface, int *serial);
int pspPmfLayerNextDelay();
int pspPmfLayerWaitDelay();
class PSPBackgroundCache;
void pspPmfLayerInvalidateGpu();
void pspPmfLayerReleaseGpu();
int pspPmfLayerPresentGpu(PSPBackgroundCache*,SDL_Surface*,const SDL_Rect*,const unsigned char*);


#endif
