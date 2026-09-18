#ifndef PSP_DIAGNOSTIC_H
#define PSP_DIAGNOSTIC_H
#ifdef __cplusplus
extern "C" {
#endif
void pspDiagInit(void);
void pspDiagLog(const char *format, ...);
void pspDiagFileCheck(const char *path);
void pspDiagAudioPcm(const void *buffer, int bytes, long decoded);
void pspDiagAudioOutput(int result);
void pspDiagAudioHardwarePcm(const void *buffer, int bytes);
void pspDiagAudioSnapshot(const char *stage);
void pspDiagMovieReset(void);
void pspDiagFramePresented(int result);
void pspDiagMovieResult(int result);
#ifdef __cplusplus
}
#endif
#endif
