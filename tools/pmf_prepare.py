"""Host-side helpers for the fixed 30000/1001-fps Mps2Pmf profile.

Not a general PSMF editor or an encoder. No runtime changes are required.
"""


from fractions import Fraction


def timeline_from_pts(pts, last_duration, time_base):
    """Plan nearest-frame CFR duration from decoded integer timestamps.

    PTS must be in presentation order. Rational strings avoid float rounding.
    Nonzero origins are normalized; missing last-frame duration is rejected.
    """
    pts = list(pts)
    if (not pts or any(type(p) is not int for p in pts)
            or any(b <= a for a, b in zip(pts, pts[1:]))
            or type(last_duration) is not int or last_duration <= 0):
        raise ValueError('Expected ordered integer PTS and positive final duration')
    base = Fraction(time_base)
    if base <= 0:
        raise ValueError('Time base must be positive')
    seconds = (pts[-1] - pts[0] + last_duration) * base
    rate = Fraction(30000, 1001)
    frames = round(seconds * rate)
    if frames < 1:
        raise ValueError('Timeline rounds to zero output frames')
    return {'source_frames': len(pts), 'source_seconds': str(seconds),
            'output_frames': frames, 'output_fps': str(rate),
            'output_seconds': str(frames / rate)}


def fix_end_timestamp(raw, frames):
    """Return a copy with absolute end timestamps, including the start PTS."""
    if (len(raw) <= 2048 or raw[:4] != b'PSMF'
            or int.from_bytes(raw[8:12], 'big') != 2048
            or int.from_bytes(raw[12:16], 'big') != len(raw) - 2048):
        raise ValueError('Expected a complete 2048-byte-header PSMF container')
    start = int.from_bytes(raw[84:90], 'big')
    if start != 90000 or raw[90:92] != b'\0\0' or raw[116:118] != b'\0\0':
        raise ValueError('Unsupported timestamp profile')
    if type(frames) is not int or frames <= 0:
        raise ValueError('Frame count must be a positive integer')
    end = start + frames * 3003
    if end >= 2**32:
        raise ValueError('End timestamp exceeds the supported 32-bit profile')
    result = bytearray(raw)
    for offset in (92, 118):
        result[offset:offset + 4] = end.to_bytes(4, 'big')
    return bytes(result)
