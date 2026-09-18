# Narrow SDL PSP video override

Upstream: https://github.com/pspdev/SDL-legacy at `a1f2392fd46137815ada13ff9fdbae21219f49e5`.
Original-file hashes: upstream-files.json. License: COPYING (LGPL).

Only SDL_pspvideo.c is compiled; source-tree headers support that compilation. The installed SDK supplies public SDL headers and the rest of libSDL.a. The override object is linked before libSDL.a, so the archive's original SDL_pspvideo.o is not selected.

Local fix: calculate each scaled strip's right endpoint from the next absolute boundary, rather than adding a separately rounded width to its rounded left endpoint. At 360 -> 480 scaling, the old expressions produce adjacent spans (42,84) and (85,127), leaving a visible column. The correction yields shared boundaries. This is a framebuffer scaling correction, not independently timed animation panels.

Verified against the recorded before/after PMF marker cards in PPSSPP, and by executable expression coverage tests for several source/destination sizes. Parent Makefile uses dependency files and removes this object on clean.
