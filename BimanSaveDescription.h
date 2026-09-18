#ifndef BIMAN_SAVE_DESCRIPTION_H
#define BIMAN_SAVE_DESCRIPTION_H
#include <stddef.h>
#include <string.h>
extern unsigned short convONSCodeToUTF16(unsigned short);
extern unsigned short convONSSingleByteToUTF16(unsigned char);
// Match gettext: remove rendered line wraps, preserve visible characters.
static size_t bimanDescriptionUTF8(const char *text,size_t length,char *out,size_t cap){
 if(!cap)return 0;size_t n=0;
 for(size_t i=0;i<length;){
  unsigned char ch=(unsigned char)text[i++];if(!ch)break;if(ch=='\n'||ch=='\r')continue;
  unsigned short u;
  if(ch>=0x81 && ch<=0xfe){
   if(i>=length)break;unsigned char trail=(unsigned char)text[i];
   if(trail<0x40 || trail>0xfe || trail==0x7f)u=0xfffd;
   else{++i;u=convONSCodeToUTF16((ch<<8)|trail);if(!u)u=0xfffd;}
  }else u=convONSSingleByteToUTF16(ch);
  size_t k=u<0x80?1:u<0x800?2:3;if(n+k>=cap)break;
  if(k==1)out[n++]=(char)u;
  else if(k==2){out[n++]=(char)(0xc0|(u>>6));out[n++]=(char)(0x80|(u&63));}
  else{out[n++]=(char)(0xe0|(u>>12));out[n++]=(char)(0x80|((u>>6)&63));out[n++]=(char)(0x80|(u&63));}
 }
 out[n]=0;return n;
}
#endif
