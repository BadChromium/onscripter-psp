from pathlib import Path
import subprocess,tempfile,unittest
from test_cp936_runtime import run_msvc,REPO
class PixelTest(unittest.TestCase):
 def test_rgb565_swap_exhaustive_and_pitched_rectangles(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'pixels.cpp';exe=p/'pixels.exe'
   src.write_text(r'''#include "PSPFastPixels.h"
#include <stdint.h>
int main(){
for(unsigned int p=0;p<65536;++p){
 unsigned int r=(p>>11)&31,g=(p>>5)&63,b=p&31;
 if(pspSwap565((uint16_t)p)!=((b<<11)|(g<<5)|r))return 1;
 if(pspSwap565(pspSwap565((uint16_t)p))!=p)return 2;
}
uint16_t src[21],dst[27];
for(int i=0;i<21;++i)src[i]=(uint16_t)(i*3173);
for(int i=0;i<27;++i)dst[i]=0xabcd;
pspSwap565Rect(dst+2,18,src+1,14,4,3);
for(int y=0;y<3;++y)for(int x=0;x<9;++x){
 uint16_t expected=x>=2&&x<6?pspSwap565(src[y*7+x-1]):0xabcd;
 if(dst[y*9+x]!=expected)return 3;
}
return 0;}''',encoding='ascii')
   r=run_msvc(f'cl /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
 def test_decoder_pixel_conversion_matches_existing_rgb565_mapping(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'decode.cpp';exe=p/'decode.exe'
   src.write_text(r'''#include "PSPFastPixels.h"
int main(){
for(unsigned int p=0;p<0x1000000;++p){
 unsigned int r=p&255,g=(p>>8)&255,b=(p>>16)&255;
 if(pspAbgrTo565(p)!=(((r>>3)<<11)|((g>>2)<<5)|(b>>3)))return 1;
}
return 0;}''',encoding='ascii')
   r=run_msvc(f'cl /O2 /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
 def test_shade565_matches_legacy_formula(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'shade.cpp';exe=p/'shade.exe'
   src.write_text(r'''#include "PSPFastPixels.h"
int main(){
unsigned int colors[]={0,0xffffff,0x808080,0xff0000,0x317bc7};
for(unsigned int c=0;c<5;++c)for(unsigned int v=0;v<65536;++v){
 uint16_t out=(uint16_t)v;
 unsigned int r=(colors[c]>>16)&255,g=(colors[c]>>8)&255,b=colors[c]&255;
 pspShade565Row(&out,1,r,g,b);
 unsigned int expected=((((v&0xf800)>>11)*(r>>3)>>5)<<11)|((((v&0x7e0)>>5)*(g>>2)>>6)<<5)|((v&31)*(b>>3)>>5);
 if(out!=expected)return 1;
}
return 0;}''',encoding='ascii')
   r=run_msvc(f'cl /O2 /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
 def test_blend_row_preserves_legacy_rounding_and_transparency(self):
  with tempfile.TemporaryDirectory(dir=REPO) as d:
   p=Path(d);src=p/'blend.cpp';exe=p/'blend.exe'
   src.write_text(r'''#include "PSPFastPixels.h"
int main(){
uint32_t rng=1;
for(int global=0;global<=256;++global)for(int a=0;a<256;++a)for(int k=0;k<16;++k){
 rng=rng*1664525u+1013904223u;uint16_t src=(uint16_t)rng;
 rng=rng*1664525u+1013904223u;uint16_t out=(uint16_t)rng;
 uint32_t s=(src|(uint32_t)src<<16)&0x07e0f81f;
 uint32_t d=(out|(uint32_t)out<<16)&0x07e0f81f;
 uint32_t expected=(d+((s-d)*((a*global)>>11)>>5))&0x07e0f81f;
 unsigned char alpha=(unsigned char)a;
 pspBlend565Row(&out,&src,&alpha,1,global);
 if(out!=(uint16_t)(expected|expected>>16))return 1;
}
uint16_t dst[7]={1,2,3,4,5,6,7}, src[7]={8,9,10,11,12,13,14};
unsigned char a[7]={0,0,0,0,0,0,0};
pspBlend565Row(dst,src,a,7,256);
for(int i=0;i<7;++i)if(dst[i]!=i+1)return 2;
// Exercise unaligned alpha pointers, mixed blocks, and short tails.
for(int offset=0;offset<4;++offset)for(int width=1;width<65;++width){
 uint16_t s[65],d[65],e[65]; unsigned char a[69];
 for(int i=0;i<69;++i)a[i]=(i%13<5)?0:(i%13<10?255:(unsigned char)(i*7));
 for(int i=0;i<65;++i){
  s[i]=(uint16_t)(i*17921); d[i]=e[i]=(uint16_t)(i*3917);
  if(i<width){
   uint32_t sp=(s[i]|(uint32_t)s[i]<<16)&0x07e0f81f;
   uint32_t dp=(d[i]|(uint32_t)d[i]<<16)&0x07e0f81f;
   uint32_t q=(dp+((sp-dp)*((a[i+offset]*256)>>11)>>5))&0x07e0f81f;
   e[i]=(uint16_t)(q|q>>16);
  }
 }
 pspBlend565Row(d,s,a+offset,width,256);
 for(int i=0;i<65;++i)if(d[i]!=e[i])return 3;
}
return 0;}''',encoding='ascii')
   r=run_msvc(f'cl /O2 /nologo /I"{REPO}" "{src}" /Fe:"{exe}"',p)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   self.assertEqual(subprocess.run([str(exe)]).returncode,0)
if __name__=='__main__':unittest.main()
