"""Execute the vendored SDL slice expressions against gap regressions."""
from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[1]

class SdlSliceCoverageTest(unittest.TestCase):
    def test_parent_build_links_and_cleans_patched_sdl_object(self):
        makefile = (REPO / 'Makefile.PSP').read_text()
        self.assertIn('$(PSP_TARGET): pmf-lib $(SDL_VIDEO_OBJ)', makefile)
        self.assertIn('LIBS += $(SDL_VIDEO_OBJ)', makefile)
        self.assertIn('$(RM) $(SDL_VIDEO_OBJ)', makefile)
        self.assertIn('-MMD -MP', makefile)

    def test_scaled_slices_share_boundaries(self):
        source = (REPO / 'third_party/sdl-psp/src/video/psp/SDL_pspvideo.c').read_text()
        expressions = []
        for index in [0, 1]:
            match = re.search(r'vertices\[' + str(index) + r'\]\.x = ([^;]+);', source)
            self.assertIsNotNone(match)
            expression = match.group(1).replace('dstrect->x', 'dx').replace('dstrect->w', 'dw').replace('srcrect->w', 'sw').replace('vertices[0].x', 'left').replace('/', '//')
            expressions.append(expression)
        for sw, dw, dx in [(360, 480, 0), (640, 480, 0), (360, 360, 60), (480, 480, 0), (77, 133, 7)]:
            with self.subTest(source=sw, destination=dw, origin=dx):
                edges = []
                for s in range((sw + 31) // 32):
                    variables = dict(sw=sw, dw=dw, dx=dx, slice=s, PSP_SLICE_SIZE=32)
                    left = eval(expressions[0], {'__builtins__': {}}, variables)
                    right = min(eval(expressions[1], {'__builtins__': {}}, dict(variables, left=left)), dx+dw)
                    edges.append((left, right))
                self.assertEqual(edges[0][0], dx)
                self.assertEqual(edges[-1][1], dx+dw)
                for previous, following in zip(edges, edges[1:]):
                    self.assertEqual(previous[1], following[0], (sw, dw, previous, following))

if __name__ == '__main__':
    unittest.main()
