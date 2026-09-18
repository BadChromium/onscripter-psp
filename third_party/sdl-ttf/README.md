# PSP SDL_ttf shaded-glyph correction

Source: https://github.com/pspdev/SDL_ttf/tree/65da6a18b7b7f89ac67473e11311a21c1ea22de0
Tag: `2.0.11-psp`, the source selected by psp-packages sdl-ttf.
Original SDL_ttf.c SHA256: `4293e2106cf010fffe5d6e44955b5bd0e661a7c4e6bc6ec1e39b9003c8367aac`.
The source's original license notice is retained.

Only source change: in TTF_RenderGlyph_Shaded, copy `glyph->pixmap.rows` instead of `glyph->bitmap.rows`. Find_Glyph loads CACHED_PIXMAP, so the monochrome bitmap may be uncached with zero rows. The original loop then returns a correctly sized but empty glyph surface.

Makefile.PSP builds this C object and links it instead of the SDK libSDL_ttf. Fonts, script bytes, Unicode mapping, and glyph metrics are unchanged. Host regression extracts and executes the actual copy loop with an uncached monochrome bitmap and nonempty pitched pixmap. See tests/test_shaded_glyph.py. It failed against upstream source and passed after the one-line fix.

PPSSPP diagnostic evidence: analysis/h01_02h-pmf-build/dialogue-diagnostic. Original glyph bitmaps contained zero nonzero pixels; corrected Chinese glyphs contain ink and are visible both in a static scene and over a looping PMF during an untimed input wait. Instrumentation remains in the diagnostic engine, not this clean candidate.
