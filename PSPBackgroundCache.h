#ifndef PSP_BACKGROUND_CACHE_H
#define PSP_BACKGROUND_CACHE_H
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
// Exact already-composited RGB565 background. No alpha approximation.
class PSPBackgroundCache {
    unsigned char *pixels;
    int width, height;
    bool valid;
    PSPBackgroundCache(const PSPBackgroundCache&);
    PSPBackgroundCache& operator=(const PSPBackgroundCache&);
public:
    PSPBackgroundCache():pixels(NULL),width(0),height(0),valid(false) {}
    ~PSPBackgroundCache(){free(pixels);}
    void invalidate(){valid=false;}
    bool capture(const void *src,size_t pitch,int w,int h){
        valid=false;
        if(!src||w<=0||h<=0||w>4096||h>4096||pitch<(size_t)w*2)return false;
        if(!pixels||width!=w||height!=h){
            unsigned char *p=(unsigned char*)malloc((size_t)w*h*2);
            if(!p)return false;
            free(pixels);pixels=p;width=w;height=h;
        }
        for(int y=0;y<h;++y)memcpy(pixels+(size_t)y*w*2,(const unsigned char*)src+y*pitch,(size_t)w*2);
        valid=true;return true;
    }
    bool restore(void *dst,size_t pitch,int w,int h)const{
        if(!valid||!dst||width!=w||height!=h||pitch<(size_t)w*2)return false;
        for(int y=0;y<h;++y)memcpy((unsigned char*)dst+y*pitch,pixels+(size_t)y*w*2,(size_t)w*2);
        return true;
    }
};
#endif
