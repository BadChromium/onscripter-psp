// Main-script-thread GPU presentation. Decoder publication is protected by its semaphore.
#include "PSPBackgroundCache.h"
#include "PSPGpuGeometry.h"
#include "PSPExactMovie.h"
extern "C" int SDL_PSP_PresentExactMovie(const void*);
static Uint16 *pmf_gpu_background=NULL,*pmf_gpu_overlay=NULL,*pmf_gpu_output=NULL;
static bool pmf_gpu_ready=false;
static int pmf_gpu_serial=-1;
void pspPmfLayerInvalidateGpu(){pmf_gpu_ready=false;pmf_gpu_serial=-1;}
void pspPmfLayerReleaseGpu(){
    free(pmf_gpu_background);free(pmf_gpu_overlay);free(pmf_gpu_output);
    pmf_gpu_background=pmf_gpu_overlay=pmf_gpu_output=NULL;
    pspPmfLayerInvalidateGpu();
}
int pspPmfLayerPresentGpu(PSPBackgroundCache *background,SDL_Surface *screen,
                        const SDL_Rect *window,const unsigned char *text_alpha){
    if(!screen||screen->w!=480||screen->h!=272||screen->format->BytesPerPixel!=2||
       screen->format->Rmask!=0x001f||screen->format->Gmask!=0x07e0||screen->format->Bmask!=0xf800||
       !pspGpuWindowFits(window->x,window->y,window->w,window->h))return 0;
    if(!pmf_gpu_ready){
        // Refuse rather than erase text outside the opaque window.
        if(text_alpha)for(int y=0;y<272;++y)for(int x=0;x<480;++x)
            if((x<window->x||x>=window->x+window->w||y<window->y||y>=window->y+window->h)&&text_alpha[y*480+x])return 0;
        if(!pmf_gpu_background)pmf_gpu_background=(Uint16*)memalign(16,512*272*2);
        if(!pmf_gpu_overlay)pmf_gpu_overlay=(Uint16*)memalign(16,512*272*2);
        if(!pmf_gpu_output)pmf_gpu_output=(Uint16*)memalign(16,512*272*2);
        if(!pmf_gpu_background||!pmf_gpu_overlay||!pmf_gpu_output)return 0;
        if(!background->restore(pmf_gpu_background,1024,480,272))return 0;
        pspSwap565Rect(pmf_gpu_background,1024,pmf_gpu_background,1024,480,272);
        if(SDL_LockSurface(screen)<0)return 0;
        for(int y=0;y<272;++y)memcpy(pmf_gpu_overlay+y*512,(unsigned char*)screen->pixels+y*screen->pitch,480*2);
        SDL_UnlockSurface(screen);
        pmf_gpu_ready=true;
        pspDiagLog("PMF GPU scene cache prepared");
    }
    pspPmfLayerLock();
    int latest=pmf_layer_latest_index;
    if(latest<0){pspPmfLayerUnlock();return 0;}
    if(pmf_gpu_serial==pmf_layer_serial){pspPmfLayerUnlock();return 1;}
    pspExactMovieFrame(pmf_gpu_output,(const uint32_t*)pmf_layer_frame[latest],pmf_gpu_background,pmf_gpu_overlay,window->x,window->y,window->w,window->h);
    int result=SDL_PSP_PresentExactMovie(pmf_gpu_output);
    if(result){pmf_gpu_serial=pmf_layer_serial;pmf_layer_last_serial_copied=pmf_layer_serial;}
    pspPmfLayerUnlock();
    return result;
}
