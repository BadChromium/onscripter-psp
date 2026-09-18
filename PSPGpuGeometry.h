#ifndef PSP_GPU_GEOMETRY_H
#define PSP_GPU_GEOMETRY_H
static inline int pspGpuWindowFits(int x,int y,int w,int h){
 return x>=0&&y>=0&&x<=480&&y<=272&&w>0&&h>0&&w<=480-x&&h<=272-y;
}
static inline int pspGpuSliceEnd(int x,int end){return end-x>32?x+32:end;}
#endif
