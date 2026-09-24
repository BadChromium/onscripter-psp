# Asset and movie preparation

These are host-side conversion practices, not new runtime commands or a general
source-engine emulator. Use only material you have permission to process.

## Finite movie timing

`tools/pmf_prepare.py` provides two standard-library Python helpers:

```python
from tools.pmf_prepare import timeline_from_pts, fix_end_timestamp

# Synthetic example: presentation timestamps in a 1/50-second time base.
plan = timeline_from_pts([100, 110, 180], 20, "1/50")
assert plan["output_frames"] == 60
```

Use decoded frame PTS and the final frame's duration, not frame count divided by
an assumed frame rate. PTS must be strictly increasing in presentation order;
a nonzero origin is normalized. Missing durations and duplicate timestamps need
explicit investigation, not silent guesses. The output rate is 30000/1001 fps;
nearest-frame rounding uses Python's ties-to-even rule. Durations are returned
as exact rational strings. This helper plans duration only: it does not choose
which source frames to duplicate or drop.

After conversion, decode and count the actual encoded frames. For the supported
**Mps2Pmf profile only**, pass that verified frame count to
`fix_end_timestamp(raw_bytes, frame_count)`. It returns new bytes without
modifying the input. Write them to a separate output, preserving the original.

The supported container has a 2048-byte header, an exact declared payload size,
a 90000-tick start timestamp, and zero upper words in both end fields. The
helper writes `start + frame_count * 3003` into the low words at offsets 92 and
118, rejecting overflow. This avoids writing duration alone as an absolute end
PTS. Structural checks do **not** identify the encoder or validate the MPEG
payload: callers must establish this profile independently. Do not apply it to
arbitrary PSMF files, other frame rates or audio-bearing profiles without their
own validation. It does not repair damaged media or promise every encoded frame
will be displayed by the runtime.

When validating with FFmpeg, use `-fps_mode passthrough` on raw decoded output so
implicit synchronization does not invent extra frames. Check duration, ordered
frame appearance, final-frame behavior and return to the scene separately.
Host decoding, emulator presentation and physical-device playback are different
gates; a successful native return code does not prove exact frame delivery.

### Audio ownership

Inspect every source stream. If converting to video-only PMF, record an explicit
audio policy. Do not silently discard audible movie audio, or play it twice when
an equivalent scenario sound is also active. Waveform similarity alone does not
establish the original engine's mixing policy. Keep directly opened PMFs loose,
not hidden inside a script archive.

## Images and anchors

- Reconstruct split images on the **declared canvas**, not the maximum fragment
  extent. Transparent right/bottom padding affects centre and bottom anchors.
- Validate fragment bounds and dimensions before composition. Compare the old
  visible region against the corresponding reconstructed crop before claiming
  that only padding changed.
- Preserve directory-qualified identities: a face and standing sprite may have
  the same basename without being interchangeable.
- Distinguish ordinary RGBA images from legacy ONS `:a;` colour/inverse-alpha
  side-by-side images. Encode each new image once; do not repack existing UI.
- Retain a resource assigned while hidden so a later show-only command can use
  it. Geometry reset, visibility reset and filename reset need separate rules.

## Script and memory safeguards

Keep branch-local resource state separate until a verified join. Namespace
asset paths and labels when composing chapters, but rewrite only commands,
never dialogue text. Preserve voice order, repeated calls and raw identifiers.
Reject unsupported control flow instead of guessing a route.

Long sounds loaded as effects can require much more PCM memory than their
compressed file size suggests. An existing music stream can be reused only
where source semantics prove that the music channel is otherwise idle; reject
overlap rather than silently stopping music. This is a script-level technique,
not a general streaming-effects implementation.

Use synthetic fixtures for public regressions. Keep scenarios, fonts, artwork,
audio, extraction keys, local paths and device logs out of this repository.
The helpers do not implement source-engine keyframe effects or certify a full
ported game's choices, persistence, audiovisual fidelity or hardware behavior.
