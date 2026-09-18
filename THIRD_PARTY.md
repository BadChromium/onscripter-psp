# Third-party sources

Preserve the notices in each source file when redistributing modifications.

| Component | Source / revision | Licence |
|---|---|---|
| ONScripter PSP | PSP-Archive/ONScripter-for-PSP, ddc2d04a17a2db09bc770bee61578ba04e1eed25 | GPL-2.0-or-later; COPYING |
| libpspav | https://github.com/pspdev/libpspav | MIT; third_party/libpspav/LICENSE |
| SDL PSP source subset | See third_party/sdl-psp/upstream-files.json | LGPL-2.1-or-later; third_party/sdl-psp/COPYING and file notices |
| SDL_ttf | https://github.com/pspdev/SDL_ttf/tree/65da6a18b7b7f89ac67473e11311a21c1ea22de0 | See preserved SDL_ttf.c notice |
| Tremor | https://gitlab.xiph.org/xiph/tremor, 7c30a66346199f3f09017a09567c6c8a3a0eedc8 | BSD-style; third_party/tremor/COPYING |
| tiny-AES-c | https://github.com/kokke/tiny-AES-c, 23856752fbd139da0b8ca6e471a13d5bcc99a08d | Unlicense; vendor/tiny-aes/unlicense.txt |

The savedata mode-1 MAC uses a public PSP protocol constant, also present in PPSSPP's ext/libkirk/kirk_engine.c. It is not an account credential or a user-specific encryption key. No PPSSPP code is vendored here.

The PSPDEV container supplies additional linked dependencies (including SDL_image, SDL_mixer, FreeType, libmad, libogg, zlib, libpng and libjpeg). They are not vendored by this repository. Anyone distributing linked binaries must also satisfy the applicable dependency licences and corresponding-source requirements; this source-only publication does not by itself discharge those obligations.
