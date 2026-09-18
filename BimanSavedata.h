#ifndef BIMAN_SAVEDATA_H
#define BIMAN_SAVEDATA_H
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <errno.h>
#ifdef _WIN32
#include <direct.h>
#else
#include <unistd.h>
#endif

// Return 1 for persistent data, 0 for an ordinary asset, -1 on overflow.
static int bimanSavePath(const char *archive,const char *name,char *out,size_t cap){
 const char *suffix="CFG",*leaf=0;char slot[3]={0};
 if(strlen(name)==9 && !strncmp(name,"save",4) && name[4]>='1' && name[4]<='8'){
  if(!strcmp(name+5,".dat"))leaf="DATA.BIN";
  else if(!strcmp(name+5,".bmp"))leaf="SHOT.BMP";
  if(leaf){slot[0]='0';slot[1]=name[4];suffix=slot;}
 }
 const char *names[]={"envdata","gloval.sav","global.sav","kidoku.dat","NScrflog.dat","NScrllog.dat"};
 const char *files[]={"ENV.DAT","GLOBAL.DAT","GLOBAL.DAT","KIDOKU.DAT","FILELOG.DAT","LABELLOG.DAT"};
 for(int i=0;i<6;i++)if(!strcmp(name,names[i]))leaf=files[i];
 if(!leaf)return 0;
 char cwd[512]={0};
 if(!archive || !archive[0]){getcwd(cwd,sizeof cwd);archive=cwd;}
 const char *device=!strncmp(archive,"ef0:",4)?"ef0:":"ms0:";
 int n=snprintf(out,cap,"%s/PSP/SAVEDATA/BIMN90011%s/%s",device,suffix,leaf);
 return n<0 || (size_t)n>=cap?-1:1;
}
static FILE *bimanRead(const char *path){
 FILE *f=::fopen(path,"rb");if(f)return f;
 char bak[600];if(snprintf(bak,sizeof bak,"%s.BAK",path)>=(int)sizeof bak)return 0;
 return ::fopen(bak,"rb");
}
static int bimanCommit(const char *path,const char *tmp){
 char bak[600];if(snprintf(bak,sizeof bak,"%s.BAK",path)>=(int)sizeof bak)return -1;
 FILE *f=::fopen(path,"rb");bool had=f!=0;if(f)fclose(f);
 if(had){if(remove(bak)!=0 && errno!=ENOENT)return -1;if(rename(path,bak)!=0)return -1;}
 if(rename(tmp,path)!=0){if(had)rename(bak,path);return -1;}
 remove(bak);return 0;
}
static int bimanAtomicWrite(const char *path,const void *data,size_t size){
 char tmp[600];if(snprintf(tmp,sizeof tmp,"%s.TMP",path)>=(int)sizeof tmp)return -1;
 FILE *f=::fopen(tmp,"wb");if(!f)return -1;
 bool ok=fwrite(data,1,size,f)==size;if(fflush(f)!=0)ok=false;if(fclose(f)!=0)ok=false;
 if(!ok){remove(tmp);return -1;}
 return bimanCommit(path,tmp);
}

static int bimanMkdir(const char *path){
 struct stat st;if(stat(path,&st)==0)return (st.st_mode&S_IFDIR)?0:-1;
#ifdef _WIN32
 return _mkdir(path);
#else
 return mkdir(path,0777);
#endif
}
// Copy larger artwork with bounded scratch memory, retaining checked replacement.
static int bimanInstall(const char *source,const char *dest,long limit=65536){
 FILE *f=::fopen(source,"rb");if(!f)return -1;
 if(fseek(f,0,SEEK_END)!=0){fclose(f);return -1;}
 long size=ftell(f);if(size<=0 || size>limit){fclose(f);return -1;}rewind(f);
 char tmp[600];if(snprintf(tmp,sizeof tmp,"%s.TMP",dest)>=(int)sizeof tmp){fclose(f);return -1;}
 void *data=malloc(8192);if(!data){fclose(f);return -1;}
 FILE *out=::fopen(tmp,"wb");if(!out){free(data);fclose(f);return -1;}
 bool ok=true;long left=size;
 while(left>0){size_t n=left>8192?8192:(size_t)left;
  if(fread(data,1,n,f)!=n || fwrite(data,1,n,out)!=n){ok=false;break;}left-=n;
 }
 if(fclose(f)!=0)ok=false;
 if(fflush(out)!=0)ok=false;
 if(fclose(out)!=0)ok=false;
 free(data);if(!ok){remove(tmp);return -1;}
 return bimanCommit(dest,tmp);
}
static int bimanPrepare(const char *archive,const char *path,bool refreshMetadata=true){
 char dir[512],root[512],source[600],dest[600];
 if(strlen(path)>=sizeof dir)return -1;strcpy(dir,path);char *end=strrchr(dir,'/');if(!end)return -1;*end=0;
 const char *folder=strrchr(dir,'/');if(!folder || strncmp(++folder,"BIMN90011",9))return -1;
 const char *suffix=folder+9;if(strcmp(suffix,"CFG") && !(strlen(suffix)==2 && suffix[0]=='0' && suffix[1]>='1' && suffix[1]<='8'))return -1;
 strcpy(root,dir);*strrchr(root,'/')=0;
 if(bimanMkdir(root)!=0 || bimanMkdir(dir)!=0)return -1;
 snprintf(source,sizeof source,"%sui/savedata/%s.SFO",archive,suffix);snprintf(dest,sizeof dest,"%s/PARAM.SFO",dir);
 FILE *existing=refreshMetadata ? 0 : ::fopen(dest,"rb");
 if(existing)fclose(existing);else if(bimanInstall(source,dest)!=0)return -1;
 snprintf(source,sizeof source,"%sui/savedata/%s",archive,!strcmp(suffix,"CFG")?"ICON_SYSTEM.PNG":"ICON0.PNG");snprintf(dest,sizeof dest,"%s/ICON0.PNG",dir);
 if(bimanInstall(source,dest)!=0)return -1;
 snprintf(source,sizeof source,"%sui/savedata/PIC1.PNG",archive);snprintf(dest,sizeof dest,"%s/PIC1.PNG",dir);
 return bimanInstall(source,dest,512*1024);
}
#endif
