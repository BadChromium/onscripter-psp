/* Exact CPU-composited native RGB565 texture; GU only presents it. */
#include "PSPGpuGeometry.h"
int SDL_PSP_PresentExactMovie(const void *pixels){
 if(!current_video||!SDL_VideoSurface||!pixels||
    SDL_VideoSurface->w!=480||SDL_VideoSurface->h!=272||
    !IS_SWSURFACE(SDL_VideoSurface->flags))return 0;
 sceKernelDcacheWritebackAll();
 sceGuStart(GU_DIRECT,list);
 sceGuDisable(GU_BLEND);sceGuDisable(GU_DEPTH_TEST);sceGuDisable(GU_ALPHA_TEST);
 sceGuDisable(GU_STENCIL_TEST);sceGuDisable(GU_DITHER);
 sceGuEnable(GU_TEXTURE_2D);sceGuEnable(GU_SCISSOR_TEST);
 sceGuScissor(0,0,480,272);
 sceGuTexFunc(GU_TFX_REPLACE,GU_TCC_RGB);
 sceGuTexFilter(GU_NEAREST,GU_NEAREST);sceGuTexWrap(GU_CLAMP,GU_CLAMP);
 sceGuDrawBuffer(GU_PSM_8888,(void*)((unsigned int)current_video->hidden->vram_base&0xffffff),512);
 sceGuTexMode(GU_PSM_5650,0,0,0);
 sceGuTexImage(0,512,512,512,pixels);
 sceGuTexSync();sceGuTexFlush();
 for(int a=0;a<480;){
  int b=pspGpuSliceEnd(a,480);
  struct texVertex *v=(struct texVertex*)sceGuGetMemory(2*sizeof(struct texVertex));
  v[0].u=a;v[0].v=0;v[0].x=a;v[0].y=0;v[0].z=0;
  v[1].u=b;v[1].v=272;v[1].x=b;v[1].y=272;v[1].z=0;
  sceGuDrawArray(GU_SPRITES,GU_TEXTURE_16BIT|GU_VERTEX_16BIT|GU_TRANSFORM_2D,2,0,v);
  a=b;
 }
 sceGuFinish();sceGuSync(0,0);
 return 1;
}
