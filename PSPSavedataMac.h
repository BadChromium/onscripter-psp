#ifndef PSP_SAVEDATA_MAC_H
#define PSP_SAVEDATA_MAC_H
#include <stddef.h>
#include <string.h>
#define CBC 0
#define CTR 0
#define ECB 1
#include "vendor/tiny-aes/aes.c"
// Fixed, positive, block-aligned SFO inputs; AES-CMAC mode 1, no firmware imports.
static int onsPspMode1Mac(const unsigned char *data,size_t size,unsigned char out[16]){
 if(!data || !out || !size || size%16)return -1;
 static const unsigned char key[16]={152,2,196,230,236,158,158,47,252,99,76,228,47,187,70,104};
 struct AES_ctx ctx;AES_init_ctx(&ctx,key);
 unsigned char subkey[16]={0},state[16]={0};AES_ECB_encrypt(&ctx,subkey);
 unsigned char carry=0;for(int i=15;i>=0;--i){unsigned char next=subkey[i]>>7;subkey[i]=(unsigned char)((subkey[i]<<1)|carry);carry=next;}
 if(carry)subkey[15]^=0x87;
 for(size_t off=0;off<size;off+=16){
  for(int i=0;i<16;++i)state[i]^=data[off+i];
  if(off+16==size)for(int i=0;i<16;++i)state[i]^=subkey[i];
  AES_ECB_encrypt(&ctx,state);
 }
 memcpy(out,state,16);return 0;
}
#endif
