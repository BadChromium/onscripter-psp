"""Synthetic container tests; no copyrighted media or external encoders."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))


class HeaderTests(unittest.TestCase):
    def test_end_includes_start_and_only_changes_end_fields(self):
        from pmf_prepare import fix_end_timestamp
        raw = bytearray(4096)
        raw[:4] = b'PSMF'
        raw[8:12] = (2048).to_bytes(4, 'big')
        raw[12:16] = (2048).to_bytes(4, 'big')
        raw[84:90] = (90000).to_bytes(6, 'big')
        raw[2048:] = b'\xab' * 2048
        original = bytes(raw)
        result = fix_end_timestamp(original, 60)
        expected = bytearray(original)
        for offset in (92, 118):
            expected[offset:offset + 4] = (270180).to_bytes(4, 'big')
        self.assertEqual(result, bytes(expected))
        self.assertEqual(bytes(raw), original)
        self.assertEqual(fix_end_timestamp(result, 60), result)

    def test_rejects_invalid_or_unsupported_profiles(self):
        from pmf_prepare import fix_end_timestamp
        valid = bytearray(4096)
        valid[:4] = b'PSMF'
        valid[8:12] = (2048).to_bytes(4, 'big')
        valid[12:16] = (2048).to_bytes(4, 'big')
        valid[84:90] = (90000).to_bytes(6, 'big')
        cases = [b'', bytes(valid[:2048])]
        for offset, value in [(0, b'NOPE'), (8, (4096).to_bytes(4, 'big')),
                              (84, bytes(6)), (90, b'\x01'), (116, b'\x01')]:
            bad = bytearray(valid)
            bad[offset:offset + len(value)] = value
            cases.append(bytes(bad))
        for raw in cases:
            with self.subTest(raw_length=len(raw)), self.assertRaises(ValueError):
                fix_end_timestamp(raw, 60)
        for frames in [0, -1, True, 1.5, 2**32]:
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                fix_end_timestamp(bytes(valid), frames)


class TimelineTests(unittest.TestCase):
    def test_uses_pts_span_and_last_frame_duration_not_frame_count(self):
        from pmf_prepare import timeline_from_pts
        # Three irregularly spaced frames covering two seconds, with an offset.
        plan = timeline_from_pts([100, 110, 180], 20, '1/50')
        self.assertEqual(plan['source_frames'], 3)
        self.assertEqual(plan['source_seconds'], '2')
        self.assertEqual(plan['output_frames'], 60)
        self.assertEqual(plan['output_seconds'], '1001/500')
        self.assertEqual(plan['output_fps'], '30000/1001')

    def test_rejects_ambiguous_or_empty_timing(self):
        from pmf_prepare import timeline_from_pts
        for pts, duration, base in [([], 1, '1/30'), ([0, 0], 1, '1/30'),
                                    ([2, 1], 1, '1/30'), ([0], 0, '1/30'),
                                    ([0], 1, '0'), ([0], 1, '-1'),
                                    ([0.5], 1, '1/30'), ([True], 1, '1/30'),
                                    ([0], 1, '1/1000000')]:
            with self.subTest(pts=pts, duration=duration, base=base):
                with self.assertRaises(ValueError):
                    timeline_from_pts(pts, duration, base)


if __name__ == '__main__':
    unittest.main()
