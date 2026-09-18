#ifndef BIMAN_DESCRIPTION_PSP_H
#define BIMAN_DESCRIPTION_PSP_H
#include "BimanSaveDescription.h"
#include "BimanSavedata.h"
#include "PSPDiagnostic.h"
#include "BimanMode1Mac.h"
#include <malloc.h>

static unsigned int bimanSfoRead32(const unsigned char *p){return p[0]|(p[1]<<8)|(p[2]<<16)|((unsigned int)p[3]<<24);}
static void bimanSfoWrite32(unsigned char *p,unsigned int n){for(int i=0;i<4;i++){p[i]=n&255;n>>=8;}}
static int bimanDescriptionError(const char *stage){pspDiagLog("SAVE_DESC fail stage=%s errno=%d",stage,errno);return -1;}
// Diagnostic revision: retain the same update algorithm; record its failing boundary.
static int bimanWriteDescription(const char *archive,int slot,const char *text,size_t length){
 pspDiagLog("SAVE_DESC begin slot=%d input_bytes=%u",slot,(unsigned int)length);
 if(slot<1 || slot>8)return bimanDescriptionError("slot");
 char name[16],path[512];snprintf(name,sizeof name,"save%d.dat",slot);
 if(bimanSavePath(archive,name,path,sizeof path)!=1)return bimanDescriptionError("path");
 char *leaf=strrchr(path,'/');if(!leaf)return bimanDescriptionError("leaf");strcpy(leaf+1,"PARAM.SFO");
 FILE *f=::fopen(path,"rb");if(!f)return bimanDescriptionError("open");
 unsigned char *data=(unsigned char*)memalign(16,4912);if(!data){fclose(f);return bimanDescriptionError("alloc");}
 size_t got=fread(data,1,4912,f);int next=got==4912?fgetc(f):0;
 pspDiagLog("SAVE_DESC read bytes=%u next=%d ferror=%d errno=%d",(unsigned int)got,next,ferror(f),errno);
 bool ok=got==4912 && next==EOF;fclose(f);
 if(!ok || memcmp(data,"\0PSF",4) || bimanSfoRead32(data+4)!=0x101 || bimanSfoRead32(data+8)!=148 || bimanSfoRead32(data+12)!=264 || bimanSfoRead32(data+16)!=8){free(data);return bimanDescriptionError("layout");}
 int detail=-1,params=-1,detailEntry=-1;
 for(int i=0;i<8;i++){
  unsigned char *entry=data+20+16*i;unsigned int key=entry[0]|(entry[1]<<8),cap=bimanSfoRead32(entry+8),off=bimanSfoRead32(entry+12);
  if(key>=116 || off>4648 || cap>4648-off){free(data);return bimanDescriptionError("field_bounds");}
  const char *k=(const char*)data+148+key;if(!memchr(k,0,116-key)){free(data);return bimanDescriptionError("key");}
  if(!strcmp(k,"SAVEDATA_DETAIL") && cap==1024){detail=264+off;detailEntry=20+16*i;}
  if(!strcmp(k,"SAVEDATA_PARAMS") && cap==128)params=264+off;
 }
 if(detail<0 || params<0){free(data);return bimanDescriptionError("missing_field");}
 memset(data+detail,0,1024);
 size_t n=bimanDescriptionUTF8(text,length,(char*)data+detail,1024);
 bimanSfoWrite32(data+detailEntry+4,(unsigned int)n+1);
 pspDiagLog("SAVE_DESC converted utf8_bytes=%u",(unsigned int)n);
 memset(data+params+16,0,16);
 unsigned char hash[16];
 int rc=bimanMode1Mac(data,4912,hash);pspDiagLog("SAVE_DESC local_mode1 rc=%d",rc);
 if(rc>=0){memcpy(data+params+16,hash,16);rc=bimanAtomicWrite(path,data,4912);pspDiagLog("SAVE_DESC commit rc=%d errno=%d",rc,errno);}
 pspDiagLog("SAVE_DESC end rc=%d",rc);free(data);return rc<0?-1:0;
}
#endif
