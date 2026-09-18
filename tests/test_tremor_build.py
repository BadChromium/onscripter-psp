from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]

class TremorBuildTest(unittest.TestCase):
    def test_engine_uses_rebuilt_type_safe_tremor(self):
        make = (REPO / 'Makefile.PSP').read_text()
        self.assertNotIn('-lvorbisidec', make)
        self.assertIn('$(TREMOR_LIB)', make)
        self.assertIn('$(MAKE) -C third_party/tremor', make)
        self.assertIn('$(PSP_TARGET): pmf-lib $(SDL_VIDEO_OBJ) tremor-lib', make)
        self.assertIn('$(MAKE) -C third_party/tremor clean', make)
        source = (REPO / 'third_party/tremor/sharedbook.c').read_text()
        self.assertEqual(source.count('ogg_int32_t point=0;'), 2)
        local = (REPO / 'third_party/tremor/Makefile').read_text()
        self.assertNotIn('-Wno-error=incompatible-pointer-types', local)

if __name__ == '__main__':
    unittest.main()
