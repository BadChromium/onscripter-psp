# Engine Integration

## Script Encoding And Header

This engine build uses `-DONS_CN_CP936` in `Makefile.PSP`. Scripts are read as CP936 bytes; do not transcode `0.txt` to Shift-JIS.

The native chapter header is:

```onscripter
;$V4000G1500S480,272
```

`G1500` sets the global variable boundary to 1500. `S480,272` sets the logical screen to 480x272 and bypasses the legacy `PDA_PSP` 9/8 enlargement.

## PMF Background Sprite Interface

Parent emitters should assign a looping PMF background as an ordinary sprite:

```onscripter
lsp 5,":v;movie/ha01_01.pmf",0,0
```

`lsph` is also accepted for hidden assignment:

```onscripter
lsph 5,":v;movie/ha01_01.pmf",0,0
vsp 5,1
```

The `:v;` tag means "native PMF video sprite". Relative paths after the semicolon are resolved against `getcwd()` on the script thread before starting the PSP decoder worker. Worker threads do not inherit the native current directory; passing a relative path directly returned `SCE_KERNEL_ERROR_NOCWD` (`0x8002032c`) in PPSSPP. Device-qualified paths remain qualified, and no `umd0:` or `ms0:` device is hard-coded. Overlong or unresolvable paths are rejected rather than truncated.


Only one PMF sprite layer is supported in this build; the parent-facing rule is "only one PMF sprite layer". Assigning another `:v;` sprite while a different PMF sprite is active is rejected and leaves the existing layer intact. Reassigning the same slot replaces and restarts the PMF. `vsp` shows or hides the assigned sprite without stopping the decoder. `msp` moves it like a normal sprite. `csp 5`, `csp -1`, reset, and engine exit stop and join the decoder layer.

The legacy blocking interface is unchanged:

```onscripter
mpegplay "movie/test.pmf",0
```

The PMF sprite path decodes video only and does not touch the BGM or SDL_mixer channel lifecycle. Looping currently restarts the libpspav one-shot decode after EOF; the decoder modules are initialized and shut down per source cycle rather than rewound in place.
