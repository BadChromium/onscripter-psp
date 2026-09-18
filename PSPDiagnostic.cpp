#include "PSPDiagnostic.h"
#include "PSPGameConfig.h"
#include <pspkernel.h>
#include <pspiofilemgr.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <SDL.h>
#include <SDL_mixer.h>

static char log_path[1024] = "PMF_DIAG.txt";
static int log_lock = -1;
static volatile unsigned int audio_calls, audio_bytes, audio_samples, audio_clipped;
static volatile unsigned long long audio_square_sum;
static volatile int audio_peak, audio_last_decoded;
static volatile unsigned int output_calls, output_errors, presented_frames;
static volatile int output_last_result, display_last_result;
static volatile unsigned int hardware_samples, hardware_clipped;
static volatile unsigned long long hardware_squares;
static volatile int hardware_peak;

extern "C" void pspDiagLog(const char *format, ...)
{
    char message[1536];
    va_list args;
    va_start(args, format);
    vsnprintf(message, sizeof(message), format, args);
    va_end(args);
    if (log_lock >= 0) sceKernelWaitSema(log_lock, 1, NULL);
    FILE *file = fopen(log_path, "a");
    if (file) {
        fprintf(file, "%u %s\n", (unsigned int)sceKernelGetSystemTimeLow(), message);
        fclose(file);
    }
    if (log_lock >= 0) sceKernelSignalSema(log_lock, 1);
}

extern "C" void pspDiagInit(void)
{
    char cwd[768] = {0};
    if (getcwd(cwd, sizeof(cwd))) {
        if (!strncmp(cwd, "disc0:", 6) || !strncmp(cwd, "umd0:", 5))
            snprintf(log_path, sizeof(log_path), "ms0:/PSP/%s_ISO.log", onsPspGameId);
        else snprintf(log_path, sizeof(log_path), "%s/PMF_DIAG.txt", cwd);
    }
    log_lock = sceKernelCreateSema("pmf_diag_log", 0, 1, 1, NULL);
    FILE *file = fopen(log_path, "w");
    if (file) fclose(file);
    pspDiagLog("BUILD=PSP-DIAG-03G-AV2 devkit=0x%08x cwd=%s log_lock=%d", (unsigned int)sceKernelDevkitVersion(), cwd, log_lock);
    pspDiagLog("free_memory=%u max_block=%u", sceKernelTotalFreeMemSize(), sceKernelMaxFreeMemSize());
}

extern "C" void pspDiagFileCheck(const char *path)
{
    char cwd[768] = {0}, absolute[1024] = {0};
    getcwd(cwd, sizeof(cwd));
    snprintf(absolute, sizeof(absolute), "%s/%s", cwd, path);
    FILE *file = fopen(path, "rb");
    int open_errno = errno;
    unsigned char magic[8] = {0};
    long size = -1;
    if (file) {
        fread(magic, 1, sizeof(magic), file);
        fseek(file, 0, SEEK_END);
        size = ftell(file);
        fclose(file);
    }
    pspDiagLog("FILE path=%s libc_open=%d errno=%d size=%ld magic=%02x%02x%02x%02x", path, file != NULL, open_errno, size, magic[0],magic[1],magic[2],magic[3]);
    SceUID fd = sceIoOpen(path, PSP_O_RDONLY, 0);
    pspDiagLog("FILE native_relative=%d hex=0x%08x", fd, (unsigned int)fd);
    if (fd >= 0) sceIoClose(fd);
    fd = sceIoOpen(absolute, PSP_O_RDONLY, 0);
    pspDiagLog("FILE native_absolute=%d hex=0x%08x path=%s", fd, (unsigned int)fd, absolute);
    if (fd >= 0) sceIoClose(fd);
}

extern "C" void pspDiagAudioPcm(const void *buffer, int bytes, long decoded)
{
    // No file I/O or locks in the real-time mixer callback.
    audio_calls++;
    audio_last_decoded = decoded;
    if (decoded <= 0) return;
    int count = (decoded < bytes ? decoded : bytes) / 2;
    const short *pcm = (const short *)buffer;
    unsigned long long squares = 0;
    unsigned int clipped = 0;
    int peak = 0;
    for (int i=0; i<count; i++) {
        int value = pcm[i];
        int magnitude = value < 0 ? -value : value;
        squares += (long long)value * value;
        if (magnitude > peak) peak = magnitude;
        if (magnitude >= 32760) clipped++;
    }
    audio_bytes += decoded;
    audio_samples += count;
    audio_square_sum += squares;
    audio_clipped += clipped;
    if (peak > audio_peak) audio_peak = peak;
}

extern "C" void pspDiagAudioHardwarePcm(const void *buffer, int bytes)
{
    const short *pcm = (const short *)buffer;
    unsigned long long squares = 0;
    unsigned int clipped = 0;
    int peak = 0;
    for (int i = 0; i < bytes / 2; i++) {
        int value = pcm[i];
        int magnitude = value < 0 ? -value : value;
        squares += (long long)value * value;
        if (magnitude > peak) peak = magnitude;
        if (magnitude >= 32760) clipped++;
    }
    hardware_samples += bytes / 2;
    hardware_squares += squares;
    hardware_clipped += clipped;
    if (peak > hardware_peak) hardware_peak = peak;
}

extern "C" void pspDiagAudioOutput(int result)
{
    output_calls++;
    output_last_result = result;
    if (result < 0) output_errors++;
}

extern "C" void pspDiagAudioSnapshot(const char *stage)
{
    int freq = 0, channels = 0;
    Uint16 format = 0;
    int opened = Mix_QuerySpec(&freq, &format, &channels);
    pspDiagLog("AUDIO_HW stage=%s hardware_samples=%u hardware_squares=%llu hardware_peak=%d hardware_clipped=%u", stage, hardware_samples, hardware_squares, hardware_peak, hardware_clipped);
    pspDiagLog("AUDIO stage=%s opened=%d status=%d freq=%d channels=%d format=0x%04x callbacks=%u decoded_bytes=%u samples=%u squares=%llu peak=%d clipped=%u last_decode=%d outputs=%u output_errors=%u output_last=0x%08x", stage, opened, SDL_GetAudioStatus(), freq, channels, format, audio_calls, audio_bytes, audio_samples, audio_square_sum, audio_peak, audio_clipped, audio_last_decoded, output_calls, output_errors, (unsigned int)output_last_result);
}

extern "C" void pspDiagMovieReset(void)
{
    presented_frames = 0;
    display_last_result = 0;
}
extern "C" void pspDiagFramePresented(int result)
{
    presented_frames++;
    display_last_result = result;
}
extern "C" void pspDiagMovieResult(int result)
{
    pspDiagLog("MOVIE result=%d hex=0x%08x presented_frames=%u display_last=0x%08x free_memory=%u max_block=%u", result, (unsigned int)result, presented_frames, (unsigned int)display_last_result, sceKernelTotalFreeMemSize(), sceKernelMaxFreeMemSize());
}
