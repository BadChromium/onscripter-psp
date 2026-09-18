#ifndef PSP_FAST_PIXELS_H
#define PSP_FAST_PIXELS_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
inline uint16_t pspSwap565(uint16_t p)
{
    return (uint16_t)(((p & 0xf800u) >> 11) | (p & 0x07e0u) | ((p & 0x001fu) << 11));
}
inline void pspSwap565Rect(void *dst, size_t dst_pitch, const void *src,
                           size_t src_pitch, int width, int height)
{
    for (int y=0;y<height;++y){
        uint16_t *d=(uint16_t *)((unsigned char *)dst+y*dst_pitch);
        const uint16_t *s=(const uint16_t *)((const unsigned char *)src+y*src_pitch);
        for (int x=0;x<width;++x) d[x]=pspSwap565(s[x]);
    }
}
inline uint16_t pspAbgrTo565(uint32_t p)
{
    return (uint16_t)(((p & 0x000000f8u) << 8) | ((p & 0x0000fc00u) >> 5) | ((p & 0x00f80000u) >> 19));
}
inline void pspShade565Row(uint16_t *pixels, int count, unsigned int r,
                            unsigned int g, unsigned int b)
{
    r >>= 3; g >>= 2; b >>= 3;
    if (!(r|g|b)){
        memset(pixels,0,(size_t)count*sizeof(uint16_t));
        return;
    }
    for (int x=0;x<count;++x){
        unsigned int v=pixels[x];
        pixels[x]=(uint16_t)(((((v>>11)&31)*r>>5)<<11)|
                             ((((v>>5)&63)*g>>6)<<5)|((v&31)*b>>5));
    }
}
inline void pspBlend565Row(uint16_t *dst, const uint16_t *src,
                           const unsigned char *alpha, int width, int global_alpha)
{
    if (!global_alpha) return;
    for (int x=0;x<width;++x){
        if (x+4<=width){
            uint32_t block;
            memcpy(&block,alpha+x,sizeof(block));
            if (!block){x+=3;continue;}
            if (block==0xffffffffu && global_alpha==256){
                for(int j=0;j<4;++j){
                    uint32_t s=(src[x+j]|(uint32_t)src[x+j]<<16)&0x07e0f81f;
                    uint32_t d=(dst[x+j]|(uint32_t)dst[x+j]<<16)&0x07e0f81f;
                    // Exact legacy weight 31/32, not an opaque memcpy.
                    uint32_t q=(s+((d-s)>>5))&0x07e0f81f;
                    dst[x+j]=(uint16_t)(q|q>>16);
                }
                x+=3;continue;
            }
        }
        unsigned int weight=(alpha[x]*global_alpha)>>11;
        if (!weight) continue;
        uint32_t s=(src[x]|(uint32_t)src[x]<<16)&0x07e0f81f;
        uint32_t d=(dst[x]|(uint32_t)dst[x]<<16)&0x07e0f81f;
        uint32_t result=(d+((s-d)*weight>>5))&0x07e0f81f;
        dst[x]=(uint16_t)(result|result>>16);
    }
}
#endif
