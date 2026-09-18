#ifndef PSP_EXACT_MOVIE_H
#define PSP_EXACT_MOVIE_H
#include <stdint.h>
#include <string.h>
#include "PSPGpuGeometry.h"
inline void pspExactMovieSpan(uint16_t *out,const uint32_t *movie,const uint16_t *background,int count){
 for(int x=0;x<count;++x){
  uint32_t p=movie[x];
  uint32_t s=((p>>3)&31u)|((p>>5)&2016u)|((p>>8)&63488u);
  uint32_t d=background[x];
  s=(s|(s<<16))&0x07e0f81fu;d=(d|(d<<16))&0x07e0f81fu;
  uint32_t q=(s+((d-s)>>5))&0x07e0f81fu;
  out[x]=(uint16_t)(q|(q>>16));
 }
}
inline int pspExactMovieFrame(uint16_t *out,const uint32_t *movie,const uint16_t *background,const uint16_t *overlay,int x,int y,int w,int h){
 if(!pspGpuWindowFits(x,y,w,h))return 0;
 for(int row=0;row<272;++row){
  int i=row*512;
  if(row<y||row>=y+h)pspExactMovieSpan(out+i,movie+i,background+i,480);
  else{
   pspExactMovieSpan(out+i,movie+i,background+i,x);
   memcpy(out+i+x,overlay+i+x,w*sizeof(uint16_t));
   int end=x+w;
   pspExactMovieSpan(out+i+end,movie+i+end,background+i+end,480-end);
  }
 }
 return 1;
}
#endif
