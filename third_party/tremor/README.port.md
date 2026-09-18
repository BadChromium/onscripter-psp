# PSP Tremor build

Source: https://gitlab.xiph.org/xiph/tremor.git at `7c30a66346199f3f09017a09567c6c8a3a0eedc8`.
Applied C/header changes from the PSP packages `master...sezero.patch`, SHA-256 `5bd4ac5916bda07e6f9dbdcd1633ac7073c7972b874b04ca59d5edde65afc847`.
Patch URL: https://raw.githubusercontent.com/pspdev/psp-packages/master/tremor/master...sezero.patch
License: COPYING (BSD-style).

Local correction: change the two codebook `point` locals in sharedbook.c to `ogg_int32_t`, matching the output pointer accepted by VFLOAT_MULTI/VFLOAT_ADD. On PSP, `ogg_int32_t` is `long`, not `int`; equal storage sizes do not make these pointers alias-compatible.

The installed SDK tremor 1.2.1git-6 produced heavily saturated PCM from a low-level 440 Hz OGG in an independent PSP decoder control. Rebuilding full-accuracy source without this type correction still failed. Changing only those two types in that full-accuracy control restored 440 Hz, RMS about 2903, and zero clipping. Do not suppress incompatible-pointer diagnostics to build this code.

The local Makefile uses full-accuracy integer arithmetic. Physical-PSP CPU/memory suitability remains a device gate. No floating-point Vorbis decoder is substituted. Parent builds recheck this archive and clean it explicitly.
