// Decode and convert in one final, mixer-owned allocation: no WAV copies.
#include <limits.h>
static Mix_Chunk *onsDecodePcmChunk(OVInfo *ovi,int channel,
                                  void (*progress)(void *)=NULL,void *context=NULL)
{
    SDL_AudioCVT cvt=ovi->cvt;
    long source_bytes=ovi->decoded_length;
    if(source_bytes<=0||cvt.len_mult<1||source_bytes>INT_MAX/cvt.len_mult){
        SDL_SetError("Invalid or excessive decoded audio size");return NULL;
    }
    Uint32 capacity=(Uint32)source_bytes*cvt.len_mult;
    Uint8 *pcm=(Uint8 *)SDL_malloc(capacity);
    if(!pcm){SDL_SetError("Out of memory allocating PCM buffer");return NULL;}
    pspDiagLog("VOICE buffer channel=%d capacity=%u multiplier=%d",channel,capacity,cvt.len_mult);
    long actual=0;
    if (!progress) actual=decodeOggVorbis(ovi,pcm,source_bytes,false);
    else while (actual<source_bytes){
        long request=source_bytes-actual;
        if(request>8192)request=8192;
        long decoded=decodeOggVorbis(ovi,pcm+actual,request,false);
        if(decoded<0||decoded>request){actual=-1;break;}
        if(decoded==0)break;
        actual+=decoded;
        progress(context);
        if(decoded<request)break;
    }
    pspDiagLog("VOICE decoded channel=%d actual=%ld expected=%ld",channel,actual,source_bytes);
    if(actual<=0||actual>source_bytes){
        SDL_free(pcm);SDL_SetError("Invalid decoded audio length");return NULL;
    }
    cvt.buf=pcm;cvt.len=(int)actual;
    if(cvt.needed && SDL_ConvertAudio(&cvt)<0){SDL_free(pcm);return NULL;}
    int length=cvt.needed?cvt.len_cvt:cvt.len;
    if(length<=0||(Uint32)length>capacity){
        SDL_free(pcm);SDL_SetError("Invalid converted audio length");return NULL;
    }
    Mix_Chunk *chunk=Mix_QuickLoad_RAW(pcm,(Uint32)length);
    if(!chunk){SDL_free(pcm);return NULL;}
    // QuickLoad borrows PCM by default. Transfer it to Mix_FreeChunk exactly once.
    chunk->allocated=1;
    return chunk;
}
