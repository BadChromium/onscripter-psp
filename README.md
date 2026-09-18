# ONScripter PSP

A PSP-focused ONScripter development project targeting the native **480×272** display and **480×270 (270p)** games. Its initial source snapshot comes from the Biman port. This repository contains the engine, local library changes and regression tests, **not the game**. No scenario, artwork, audio, font, save data or ISO is included.

## Status and contributions

**Early development snapshot, not yet a drop-in engine for arbitrary games.** Script-native dimensions are parsed from headers such as `;$V4000G1500S480,272` or `;$V4000G1500S480,270`. The 480×270 header path has a host regression test; its physical display placement and rendering still need dedicated PSP validation.

This project **uses generative AI (GenAI)** for development, debugging, tests and documentation. Generated code can contain mistakes. Anyone is welcome to improve it through issues, reviews, fixes, tests, documentation and pull requests. Please report reproducible behavior and distinguish physical PSP results from emulator results.

Reusable helpers now use functional names: `PSPSavedata.h` (routing and checked writes), `PSPSavedataDescription.h` (SFO detail updates), `ONSSaveText.h` (text conversion), `PSPSavedataMac.h` (mode-1 integrity), and `ONSMaskGain.h` (mask transitions). None are unused game assets.

Build each game with a unique identity, for example `make -f Makefile.PSP GAME_ID=TEST00001 PSP_EBOOT_TITLE="My Game"`. IDs must be four uppercase letters and five digits. `ONSP00001` is reserved here for engine development; do not share it between distributed games. Run `make -f Makefile.PSP clean` before switching identity or encoding because compiler flags are not tracked as make dependencies.

Generalization is not complete: the current savedata adapter supports eight slots, requires matching `ui/savedata/{CFG,01..08}.SFO` templates plus `ICON_SYSTEM.PNG`, `ICON0.PNG` and `PIC1.PNG`, and its description updater expects the legacy fixed SFO layout. Changing GAME_ID does not generate or update those templates: their embedded save-directory identity must match the build. CP936 remains the default (`ONS_CN_CP936`). Generic metadata generation and broader save-slot support are future work. The accepted originating-game distribution remains untouched.

## Changes

- Native 480×272 script layout and CP936 text support.
- PSP PMF playback and GPU integration, voice-buffer lifecycle improvements and background caching.
- PSP savedata integration with a configurable game identity, dialogue controls and diagnostic logging.
- Disc startup in `disc0:/PSP_GAME/USRDIR`; disc diagnostics write to `ms0:/PSP/<GAME_ID>_ISO.log`.

The source snapshot retains diagnostic instrumentation from the hardware-tested build. Startup and warm/cold save loading were reported working on PSP03g with 6.20 PRO-C2 / Inferno. This is not certification for every PSP or a full hardware playthrough. The build requests extended RAM; PSP-1000 is not a supported target at present.

## Build

Requires PSPSDK, the PSP SDL 1.2 stack and its image/mixer/font dependencies. A pinned PSPDEV container is the tested environment. From this repository in a Linux shell (or WSL with the repository on a mounted drive):

```sh
docker run --rm -v "$PWD:/src" -w /src \
  pspdev/pspdev@sha256:b22811072ea0721d7f6c666a5a279b6def2b0cd95892b819d9570f8ffc4452c0 \
  sh -c 'make -f Makefile.PSP -j4'
```

Output: `EBOOT.PBP` and `onscripter.elf`. The PBP has plain development metadata and no game artwork. Supply your own legally obtained compatible game data; this repository does not recreate the distributed game ISO by itself. The Makefile builds the bundled library modifications from source.

After building, run `python -m unittest discover -s tests`. Tests require Python 3; compiled host harnesses also require their indicated host compiler (some use Windows Visual Studio 2022 Community). The CP936 fixture is generated rather than copied from a game; a private-workspace import-fixup test is excluded. Hardware testing is separate from this suite.

For disc packaging, the accepted game used `genisoimage -xa -iso-level 3 -allow-lowercase -allow-multidot -omit-version-number`. Non-XA images caused selective file-open failures on the tested PSP. Keep directly opened movies/support files outside NSA archives.

## Sources and credits

- Original [ONScripter by Ogapee](https://onscripter.osdn.jp/), with original copyright notices preserved.
- Direct base: [PSP-Archive/ONScripter-for-PSP](https://github.com/PSP-Archive/ONScripter-for-PSP), revision `ddc2d04a17a2db09bc770bee61578ba04e1eed25`.
- [PSPDEV](https://github.com/pspdev): toolchain, SDL PSP stack and [libpspav](https://github.com/pspdev/libpspav).
- [Xiph Tremor](https://gitlab.xiph.org/xiph/tremor) and [tiny-AES-c](https://github.com/kokke/tiny-AES-c).

See [THIRD_PARTY.md](THIRD_PARTY.md) and bundled notices for library provenance. Related projects: [ONScripterYuri](https://github.com/YuriSizuku/OnscripterYuri) and [ONScripter-Jh](https://github.com/jh10001/ONScripter-Jh). These are references, not claimed ancestors or incorporated code in this snapshot.

## Testing reports

Please report PSP model, firmware/ISO driver, steps, expected and actual behavior, and a diagnostic log if available. Review logs before uploading: they can contain file paths and gameplay details. Do not attach copyrighted game files or personal saves to public issues.

## License

The ONScripter-derived engine is **GPL-2.0-or-later**; see [COPYING](COPYING) and per-file notices. Bundled third-party components retain their own licences. Modified engine files in this snapshot include the PSP/Biman adaptations described above; upstream authorship notices are retained.

The maintainer requests that this project not be commercially exploited. **This is a non-binding preference, not an additional licence restriction.** GPL rights, including commercial use, remain unchanged. The engine licence grants no rights to separately copyrighted game assets.
