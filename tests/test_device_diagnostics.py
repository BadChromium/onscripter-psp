from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class DeviceDiagnosticTest(unittest.TestCase):
    def test_audio_trace_samples_the_final_hardware_buffer(self):
        backend = (ROOT / 'third_party/sdl-psp/src/audio/psp/SDL_pspaudio.c').read_text()
        self.assertIn('pspDiagAudioHardwarePcm(mixbuf, this->spec.size);', backend)
        helper = (ROOT / 'PSPDiagnostic.cpp').read_text()
        self.assertIn('hardware_samples=', helper)
        self.assertIn('hardware_peak=', helper)
        self.assertIn('hardware_squares=', helper)
    def test_trace_covers_native_movie_and_audio_boundaries(self):
        backend = (ROOT / 'third_party/libpspav/src/pspav.c').read_text()
        for stage in ['PMF open', 'MPEG module', 'MPEG init', 'MPEG create', 'MPEG header', 'InitReader', 'InitVideo', 'InitDecoder']:
            self.assertIn('"'+stage, backend)
        bridge = (ROOT / 'PSPPmfPlayer.cpp').read_text()
        self.assertIn('pspDiagMovieResult(result)', bridge)
        self.assertIn('pspDiagFramePresented', bridge)
        event = (ROOT / 'ONScripterLabel_event.cpp').read_bytes()
        self.assertIn(b'pspDiagAudioPcm', event)
        audio = ROOT / 'third_party/sdl-psp/src/audio/psp/SDL_pspaudio.c'
        self.assertTrue(audio.exists())
        self.assertIn('pspDiagAudioOutput', audio.read_text())

    def test_device_report_has_file_checks_and_audio_snapshots(self):
        source = ROOT / 'PSPDiagnostic.cpp'
        self.assertTrue(source.exists(), 'Diagnostic report implementation is missing')
        text = source.read_text()
        for token in ['PMF_DIAG.txt', 'sceKernelDevkitVersion', 'getcwd', 'fopen', 'sceIoOpen', 'pspDiagAudioSnapshot', 'pspDiagFileCheck']:
            self.assertIn(token, text)

if __name__ == '__main__':
    unittest.main()
