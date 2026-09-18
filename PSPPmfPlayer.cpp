#include "PSPPmfPlayer.h"
#include "PSPPmfPath.h"
#include "PSPFastPixels.h"
#include "PSPPmfTiming.h"
#include "PSPBackgroundCache.h"
#include "PSPDiagnostic.h"

#include <malloc.h>
#include <string.h>
#include <unistd.h>

#include <pspctrl.h>
#include <pspdisplay.h>
#include <pspge.h>
#include <pspkernel.h>
#include <psputils.h>

#include <pspav.h>

static const int PMF_BUFFER_WIDTH = 512;
static const int PMF_SCREEN_WIDTH = 480;
static const int PMF_SCREEN_HEIGHT = 272;
static const int PMF_PIXEL_BYTES = 4;
static const int PMF_FRAME_BYTES =
    PMF_BUFFER_WIDTH * PMF_SCREEN_HEIGHT * PMF_PIXEL_BYTES;
static const int ONS_DOUBLE_BUFFER_BYTES =
    PMF_BUFFER_WIDTH * PMF_SCREEN_HEIGHT * 2 * 2;

static bool pmf_click_enabled;
static void *pmf_framebuffer;

static volatile bool pmf_layer_stop_requested = false;
static volatile bool pmf_layer_running = false;
static SceUID pmf_layer_thread = -1;
static SceUID pmf_layer_lock = -1;
static char pmf_layer_path[256];
static unsigned char *pmf_layer_frame[2] = { NULL, NULL };
static int pmf_layer_write_index = 0;
static int pmf_layer_latest_index = -1;
static int pmf_layer_serial = 0;
static unsigned int pmf_layer_publish_time_us = 0;
static int pmf_layer_last_serial_copied = 0;
static int pmf_layer_last_pts = -1;
static int pmf_layer_last_delay_ms = 33;
static int pmf_layer_base_pts = 0;
static unsigned int pmf_layer_base_time_us = 0;
static bool pmf_layer_have_base = false;

static int pspPmfMinInt(int a, int b)
{
    return (a < b) ? a : b;
}

static void pspPmfLayerLock()
{
    if (pmf_layer_lock >= 0)
        sceKernelWaitSema(pmf_layer_lock, 1, NULL);
}

static void pspPmfLayerUnlock()
{
    if (pmf_layer_lock >= 0)
        sceKernelSignalSema(pmf_layer_lock, 1);
}

static PSPAV_PadState pspPmfGetPadState()
{
    if (!pmf_click_enabled) return PAD_NONE;

    SceCtrlData pad;
    sceCtrlPeekBufferPositive(&pad, 1);
    return pad.Buttons ? PAD_USER_CANCEL : PAD_NONE;
}

static PSPAV_PadState pspPmfLayerGetPadState()
{
    return pmf_layer_stop_requested ? PAD_USER_CANCEL : PAD_NONE;
}

static void pspPmfClearScreen(unsigned int color)
{
    (void)color;
}

static void pspPmfFlipScreen()
{
    sceDisplayWaitVblankStart();
}

static void pspPmfFlushTexture(void *texture)
{
    sceKernelDcacheWritebackInvalidateRange(texture, PMF_FRAME_BYTES);
}

static void *pspPmfGetRawTexture(void *texture)
{
    return texture;
}

static void *pspPmfCreateTexture(int width, int height)
{
    (void)width;
    (void)height;
    void *pixels = memalign(64, PMF_FRAME_BYTES);
    if (pixels) memset(pixels, 0, PMF_FRAME_BYTES);
    return pixels;
}

static void pspPmfFreeTexture(void *texture)
{
    free(texture);
}

static void pspPmfDrawTexture(void *texture, int x, int y)
{
    (void)x;
    (void)y;
    memcpy(pmf_framebuffer, texture, PMF_FRAME_BYTES);
    sceKernelDcacheWritebackAll();
    int display_result = sceDisplaySetFrameBuf(pmf_framebuffer, PMF_BUFFER_WIDTH,
                          PSP_DISPLAY_PIXEL_FORMAT_8888,
                          PSP_DISPLAY_SETBUF_IMMEDIATE);
    pspDiagFramePresented(display_result);
}

static void pspPmfSetTextureAlpha(void *texture, int alpha)
{
    (void)texture;
    (void)alpha;
}

static void pspPmfLayerPaceFrame(int timestamp)
{
    unsigned int now = sceKernelGetSystemTimeLow();


    if (!pmf_layer_have_base ||
        timestamp < pmf_layer_base_pts ||
        (pmf_layer_last_pts >= 0 && timestamp < pmf_layer_last_pts)){
        pmf_layer_base_time_us = now;
        pmf_layer_base_pts = timestamp;
        pmf_layer_have_base = true;
    }

    if (pmf_layer_last_pts >= 0){
        int delta_pts = timestamp - pmf_layer_last_pts;
        if (delta_pts > 0 && delta_pts < 90000){
            int delay_ms = (delta_pts * 1000) / 90000;
            if (delay_ms < 1) delay_ms = 1;
            if (delay_ms > 100) delay_ms = 100;
            pmf_layer_last_delay_ms = delay_ms;
        }
    }

    long long target_delta_us =
        ((long long)(timestamp - pmf_layer_base_pts) * 1000000LL) / 90000LL;
    long long target_us = (long long)pmf_layer_base_time_us + target_delta_us;
    long long delay_us = target_us - (long long)now;
    if (delay_us > 0 && delay_us < 500000LL)
        sceKernelDelayThread((unsigned int)delay_us);

    pmf_layer_last_pts = timestamp;
}

static int pspPmfLayerPublishTexture(void *texture, int x, int y, int timestamp)
{
    (void)x;
    (void)y;

    if (pmf_layer_stop_requested) return -1;

    pspPmfLayerPaceFrame(timestamp);
    if (pmf_layer_stop_requested) return -1;

    int next_index = 1 - pmf_layer_write_index;
    if (!pmf_layer_frame[next_index]) return -1;

    sceKernelDcacheWritebackInvalidateRange(texture, PMF_FRAME_BYTES);
    pspPmfLayerLock();
    memcpy(pmf_layer_frame[next_index], texture, PMF_FRAME_BYTES);
    pmf_layer_write_index = next_index;
    pmf_layer_latest_index = next_index;
    pmf_layer_serial++;
    pmf_layer_publish_time_us = sceKernelGetSystemTimeLow();
    pspPmfLayerUnlock();

    return 0;
}

static int pspPmfLayerThread(SceSize args, void *argp)
{
    (void)args;
    (void)argp;

    PSPAVCallbacks callbacks;
    callbacks.getPadState = pspPmfLayerGetPadState;
    callbacks.clearScreen = pspPmfClearScreen;
    callbacks.flipScreen = pspPmfFlipScreen;
    callbacks.flushTexture = pspPmfFlushTexture;
    callbacks.getRawTexture = pspPmfGetRawTexture;
    callbacks.createTexture = pspPmfCreateTexture;
    callbacks.freeTexture = pspPmfFreeTexture;
    callbacks.drawTexture = pspPmfDrawTexture;
    callbacks.setTextureAlpha = pspPmfSetTextureAlpha;
    callbacks.publishTexture = pspPmfLayerPublishTexture;
    callbacks.directTimestampPacing = 0;

    pmf_layer_running = true;
    while (!pmf_layer_stop_requested){
        pmf_layer_have_base = false;
        pmf_layer_last_pts = -1;
        int result = pspavPlayVideoFileLoop(pmf_layer_path, &callbacks);
        if (result < 0 && !pmf_layer_stop_requested){
            pspDiagLog("PMF layer playback failed path=%s result=%d",
                       pmf_layer_path, result);
            sceKernelDelayThread(100000);
        }
    }
    pmf_layer_running = false;

    sceKernelExitThread(0);
    return 0;
}

static Uint32 pspPmfMapSurfacePixel(SDL_PixelFormat *format,
                                    Uint8 r, Uint8 g, Uint8 b)
{
    Uint32 pixel = (((Uint32)(r >> format->Rloss)) << format->Rshift) |
                   (((Uint32)(g >> format->Gloss)) << format->Gshift) |
                   (((Uint32)(b >> format->Bloss)) << format->Bshift);
    if (format->Amask)
        pixel |= ((Uint32)(0xff >> format->Aloss)) << format->Ashift;
    return pixel;
}

static int pspPmfDisplayPixelFormat(const SDL_PixelFormat *format)
{
    if (format->BitsPerPixel == 32) return PSP_DISPLAY_PIXEL_FORMAT_8888;
    if (format->Amask == 0x8000) return PSP_DISPLAY_PIXEL_FORMAT_5551;
    if (format->Rmask == 0x0f00 && format->Gmask == 0x00f0)
        return PSP_DISPLAY_PIXEL_FORMAT_4444;
    return PSP_DISPLAY_PIXEL_FORMAT_565;
}

static unsigned int pmf_once_count = 0;
static int pspPmfOneShotPublishTexture(void *texture, int x, int y, int timestamp)
{
    // One display owner; dedicated fixed-origin one-shot PTS clock.
    // Publish callback also selects current AU timestamps in the decoder.
    // One-shot has no seeks. Pin its first PTS instead of rebasing on
    // occasional nonmonotone decoder timestamps as the loop player does.
    if (!pmf_layer_have_base) {
        pmf_layer_base_pts = timestamp;
        pmf_layer_base_time_us = sceKernelGetSystemTimeLow();
        pmf_layer_have_base = true;
    }
    // Keep the movie clock rather than accumulating rendering overruns.
    // Only direct one-shot presentation drops late frames; decode still runs.
    const long long due_us = ((long long)(timestamp - pmf_layer_base_pts) * 1000000LL) / 90000LL;
    unsigned int elapsed_us = sceKernelGetSystemTimeLow() - pmf_layer_base_time_us;
    long long delay_us = due_us - (long long)elapsed_us;
    if (delay_us > 0 && delay_us < 500000LL)
        sceKernelDelayThread((unsigned int)delay_us);
    if (delay_us < -40000LL) return 0;
    if ((pmf_once_count++ % 900) == 0)
        pspDiagLog("ONESHOT frame=%u pts=%d base_pts=%d base_us=%u", pmf_once_count, timestamp, pmf_layer_base_pts, pmf_layer_base_time_us);
    pspPmfClearScreen(0);
    pspPmfFlushTexture(texture);
    pspPmfDrawTexture(texture, x, y);
    pspPmfFlipScreen();
    return 0;
}

int pspPmfPlayVideoOnce(const char *filename, bool click_flag,
                        SDL_Surface *screen_surface)
{
    pspPmfLayerStop();

    pspDiagLog("MOVIE begin path=%s surface=%p", filename, screen_surface);
    pspDiagFileCheck(filename);
    pspDiagAudioSnapshot("before-movie");
    pspDiagMovieReset();
    PSPAVCallbacks callbacks;
    callbacks.getPadState = pspPmfGetPadState;
    callbacks.clearScreen = pspPmfClearScreen;
    callbacks.flipScreen = pspPmfFlipScreen;
    callbacks.flushTexture = pspPmfFlushTexture;
    callbacks.getRawTexture = pspPmfGetRawTexture;
    callbacks.createTexture = pspPmfCreateTexture;
    callbacks.freeTexture = pspPmfFreeTexture;
    callbacks.drawTexture = pspPmfDrawTexture;
    callbacks.setTextureAlpha = pspPmfSetTextureAlpha;
    callbacks.publishTexture = pspPmfOneShotPublishTexture;
    callbacks.directTimestampPacing = 1;

    pmf_once_count = 0;
    pmf_click_enabled = click_flag;
    pmf_framebuffer = (unsigned char *)sceGeEdramGetAddr()
                    + ONS_DOUBLE_BUFFER_BYTES;
    sceDisplaySetMode(0, 480, 272);

    int result = pspavPlayVideoFileOnce(filename, &callbacks);
    pspDiagMovieResult(result);
    pspDiagAudioSnapshot("after-movie");

    if (screen_surface){
        sceKernelDcacheWritebackAll();
        if (screen_surface->flags & SDL_HWSURFACE){
            int bytes_per_pixel = screen_surface->format->BytesPerPixel;
            int buffer_width = screen_surface->pitch / bytes_per_pixel;
            int pixel_format = pspPmfDisplayPixelFormat(screen_surface->format);
            sceDisplaySetFrameBuf(screen_surface->pixels, buffer_width,
                                  pixel_format, PSP_DISPLAY_SETBUF_IMMEDIATE);
            SDL_Flip(screen_surface);
        }
        else {
            sceDisplaySetFrameBuf(sceGeEdramGetAddr(), PMF_BUFFER_WIDTH,
                                  PSP_DISPLAY_PIXEL_FORMAT_8888,
                                  PSP_DISPLAY_SETBUF_IMMEDIATE);
            SDL_UpdateRect(screen_surface, 0, 0, 0, 0);
        }
    }
    return result;
}

int pspPmfLayerStart(const char *filename)
{
    if (!filename || filename[0] == '\0') return -1;

    pspPmfLayerStop();

    // Capture the game directory here, before crossing into the worker thread.
    char cwd[1024] = {0};
    getcwd(cwd, sizeof(cwd));
    if (!pspPmfResolvePath(pmf_layer_path, sizeof(pmf_layer_path), filename, cwd)){
        pspDiagLog("PMF layer path resolution failed path=%s cwd=%s", filename, cwd);
        return -1;
    }

    pmf_layer_lock = sceKernelCreateSema("pmf_layer_lock", 0, 1, 1, NULL);
    if (pmf_layer_lock < 0){
        pspDiagLog("PMF layer lock create failed result=%d", pmf_layer_lock);
        return -2;
    }

    pmf_layer_frame[0] = (unsigned char *)memalign(64, PMF_FRAME_BYTES);
    pmf_layer_frame[1] = (unsigned char *)memalign(64, PMF_FRAME_BYTES);
    if (!pmf_layer_frame[0] || !pmf_layer_frame[1]){
        pspPmfLayerStop();
        return -3;
    }
    memset(pmf_layer_frame[0], 0, PMF_FRAME_BYTES);
    memset(pmf_layer_frame[1], 0, PMF_FRAME_BYTES);

    pmf_layer_stop_requested = false;
    pmf_layer_running = false;
    pmf_layer_write_index = 0;
    pmf_layer_latest_index = -1;
    pmf_layer_serial = 0;
    pmf_layer_last_serial_copied = 0;
    pmf_layer_last_pts = -1;
    pmf_layer_last_delay_ms = 33;
    pmf_layer_have_base = false;

    pmf_layer_thread = sceKernelCreateThread("pmf_layer_thread",
                                             pspPmfLayerThread,
                                             0x40, 0x10000,
                                             PSP_THREAD_ATTR_USER, NULL);
    if (pmf_layer_thread < 0){
        int result = pmf_layer_thread;
        pspPmfLayerStop();
        pspDiagLog("PMF layer thread create failed result=%d", result);
        return result;
    }

    int result = sceKernelStartThread(pmf_layer_thread, 0, NULL);
    if (result < 0){
        sceKernelDeleteThread(pmf_layer_thread);
        pmf_layer_thread = -1;
        pspPmfLayerStop();
        pspDiagLog("PMF layer thread start failed result=%d", result);
        return result;
    }

    pspDiagLog("PMF layer start path=%s", pmf_layer_path);
    return 0;
}

void pspPmfLayerStop()
{
    if (pmf_layer_thread >= 0){
        pmf_layer_stop_requested = true;
        sceKernelWaitThreadEnd(pmf_layer_thread, NULL);
        sceKernelDeleteThread(pmf_layer_thread);
    }
    pmf_layer_thread = -1;

    pmf_layer_running = false;
    pmf_layer_stop_requested = false;

    if (pmf_layer_frame[0]){
        free(pmf_layer_frame[0]);
        pmf_layer_frame[0] = NULL;
    }
    if (pmf_layer_frame[1]){
        free(pmf_layer_frame[1]);
        pmf_layer_frame[1] = NULL;
    }

    if (pmf_layer_lock >= 0){
        sceKernelDeleteSema(pmf_layer_lock);
        pmf_layer_lock = -1;
    }

    pmf_layer_path[0] = '\0';
    pspPmfLayerReleaseGpu();
    pmf_layer_write_index = 0;
    pmf_layer_latest_index = -1;
    pmf_layer_serial = 0;
    pmf_layer_last_serial_copied = 0;
    pmf_layer_last_pts = -1;
    pmf_layer_last_delay_ms = 33;
    pmf_layer_have_base = false;
}

bool pspPmfLayerIsRunning()
{
    return pmf_layer_thread >= 0 && pmf_layer_running && !pmf_layer_stop_requested;
}

int pspPmfLayerWaitDelay()
{
    pspPmfLayerLock();
    int delay = pmf_layer_last_delay_ms;
    if (pmf_layer_latest_index >= 0)
        delay = pspPmfDelayAfterPublish(delay,
            sceKernelGetSystemTimeLow()-pmf_layer_publish_time_us,
            pmf_layer_serial != pmf_layer_last_serial_copied);
    pspPmfLayerUnlock();
    return delay;
}

int pspPmfLayerNextDelay()
{
    int delay_ms = pmf_layer_last_delay_ms;
    if (delay_ms < 1) delay_ms = 1;
    if (delay_ms > 100) delay_ms = 100;
    return delay_ms;
}

int pspPmfLayerCopyFrame(SDL_Surface *surface, int *serial)
{
    if (!surface || !serial) return -1;

    pspPmfLayerLock();
    int latest_index = pmf_layer_latest_index;
    int latest_serial = pmf_layer_serial;
    if (latest_index < 0 || latest_serial == *serial)
    {
        pspPmfLayerUnlock();
        return 0;
    }
    if (!pmf_layer_frame[latest_index])
    {
        pspPmfLayerUnlock();
        return -1;
    }

    int copy_width = pspPmfMinInt(PMF_SCREEN_WIDTH, surface->w);
    int copy_height = pspPmfMinInt(PMF_SCREEN_HEIGHT, surface->h);
    int bpp = surface->format->BytesPerPixel;

    const bool fast565=bpp==2 && surface->format->Rmask==0xf800 &&
        surface->format->Gmask==0x07e0 && surface->format->Bmask==0x001f &&
        surface->format->Amask==0;
    SDL_LockSurface(surface);
    unsigned int *src_base = (unsigned int *)pmf_layer_frame[latest_index];
    for (int y = 0; y < copy_height; y++){
        unsigned int *src = src_base + y * PMF_BUFFER_WIDTH;
        unsigned char *dst =
            (unsigned char *)surface->pixels + y * surface->pitch;
        if (fast565){
            for (int x=0;x<copy_width;++x) ((Uint16 *)dst)[x]=pspAbgrTo565(src[x]);
            continue;
        }
        for (int x = 0; x < copy_width; x++){
            unsigned int pixel = src[x];
            Uint8 r = (Uint8)(pixel & 0xff);
            Uint8 g = (Uint8)((pixel >> 8) & 0xff);
            Uint8 b = (Uint8)((pixel >> 16) & 0xff);
            Uint32 mapped = pspPmfMapSurfacePixel(surface->format, r, g, b);

            if (bpp == 2)
                *(Uint16 *)(dst + x * bpp) = (Uint16)mapped;
            else if (bpp == 4)
                *(Uint32 *)(dst + x * bpp) = mapped;
            else if (bpp == 3){
#if SDL_BYTEORDER == SDL_BIG_ENDIAN
                dst[x * bpp + 0] = (Uint8)((mapped >> 16) & 0xff);
                dst[x * bpp + 1] = (Uint8)((mapped >> 8) & 0xff);
                dst[x * bpp + 2] = (Uint8)(mapped & 0xff);
#else
                dst[x * bpp + 0] = (Uint8)(mapped & 0xff);
                dst[x * bpp + 1] = (Uint8)((mapped >> 8) & 0xff);
                dst[x * bpp + 2] = (Uint8)((mapped >> 16) & 0xff);
#endif
            }
        }
    }
    SDL_UnlockSurface(surface);

    *serial = latest_serial;
    pmf_layer_last_serial_copied = latest_serial;
    pspPmfLayerUnlock();
    return 1;
}

#include "PSPPmfGpu.inc"
