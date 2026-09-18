import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class PmfIntegrationContractTest(unittest.TestCase):
    def test_mpeg_loads_shared_avcodec_before_mpegbase(self):
        backend = (REPO / 'third_party/libpspav/src/pspav.c').read_text()
        init = backend.split('int pspavInit(', 1)[1].split('void pspavLoad()', 1)[0]
        self.assertIn('sceUtilityLoadModule(PSP_MODULE_AV_AVCODEC)', init)
        self.assertLess(init.index('sceUtilityLoadModule(PSP_MODULE_AV_AVCODEC)'), init.index('sceUtilityLoadModule(PSP_MODULE_AV_MPEGBASE)'))
        self.assertLess(init.index('sceUtilityLoadModule(PSP_MODULE_AV_AVCODEC)'), init.index('if (playAudio)'))
        self.assertIn('if (avcodec_module_owned)', backend)
        self.assertIn('if (mpeg_module_owned)', backend)
        self.assertIn('0x80111102', backend)
    def test_release_bridge_has_no_probe_file_writes(self):
        bridge = (REPO / "PSPPmfPlayer.cpp").read_text(encoding="utf-8")
        self.assertNotIn("psp_pmf_probe.log", bridge)
        self.assertNotIn("pspPmfWriteProbe", bridge)
        self.assertNotIn("sceIoWrite", bridge)

    def test_bridge_restores_sdl_framebuffer_after_pmf(self):
        bridge = (REPO / "PSPPmfPlayer.cpp").read_text(encoding="utf-8")
        after_backend = bridge.split("pspavPlayVideoFileOnce", 1)[1]
        self.assertIn("screen_surface->flags & SDL_HWSURFACE", after_backend)
        self.assertIn("sceGeEdramGetAddr()", after_backend)
        self.assertIn("SDL_UpdateRect(screen_surface", after_backend)

    def test_parent_build_always_checks_vendored_pmf_library(self):
        makefile = (REPO / "Makefile.PSP").read_text(encoding="utf-8")
        self.assertIn(".PHONY: pmf-lib", makefile)
        self.assertIn("$(PSP_TARGET): pmf-lib", makefile)
        self.assertIn("$(MAKE) -C third_party/libpspav", makefile)

    def test_video_only_path_does_not_reserve_or_decode_audio(self):
        backend = (
            REPO / "third_party" / "libpspav" / "src" / "pspav.c"
        ).read_text(encoding="utf-8")
        once = re.search(
            r"static int pspavPlayVideoFileMode\(.*?\n\}(?=\n\nint pspavPlayVideoFileOnce)",
            backend,
            re.DOTALL,
        )
        self.assertIsNotNone(once)
        self.assertIn("playAudio = 0", once.group(0))
        self.assertIn("return pspavPlayVideoFileMode(path,callbacks,0);", backend)
        self.assertIn("return pspavPlayVideoFileMode(path,callbacks,1);", backend)

        play = re.search(
            r"int pspavPlay\(\).*?\n\}(?=\n\nSceVoid pspavShutdown)",
            backend,
            re.DOTALL,
        )
        self.assertIsNotNone(play)
        self.assertIn("if (playAudio){\n        retVal = InitAudio();", play.group(0))
        self.assertIn("if (audioInitialized) ShutdownAudio();", play.group(0))

        decoder = (
            REPO / "third_party" / "libpspav" / "src" / "pspav_decoder.c"
        ).read_text(encoding="utf-8")
        self.assertIn("if (playAudio &&", decoder)

    def test_psp_mpegplay_uses_one_shot_pmf_without_stopping_bgm(self):
        bridge_path = REPO / "PSPPmfPlayer.cpp"
        self.assertTrue(bridge_path.is_file(), "PSP PMF bridge is missing")
        bridge = bridge_path.read_text(encoding="utf-8")
        self.assertIn("pspavPlayVideoFileOnce", bridge)
        self.assertNotIn("Mix_HaltMusic", bridge)

        command = (REPO / "ONScripterLabel_command.cpp").read_text(
            encoding="shift_jis", errors="surrogateescape"
        )
        body = re.search(
            r"int ONScripterLabel::mpegplayCommand\(\)\s*\{(?P<body>.*?)\n\}",
            command,
            re.DOTALL,
        )
        self.assertIsNotNone(body)
        psp_branch = re.search(
            r"#if defined\(PSP\)(?P<psp>.*?)#else(?P<other>.*?)#endif",
            body.group("body"),
            re.DOTALL,
        )
        self.assertIsNotNone(psp_branch, "mpegplayCommand has no PSP-specific branch")
        self.assertNotIn("stopBGM", psp_branch.group("psp"))
        self.assertIn("playMPEG", psp_branch.group("psp"))
        self.assertIn("stopBGM", psp_branch.group("other"))

        makefile = (REPO / "Makefile.PSP").read_text(encoding="utf-8")
        self.assertIn("PSPPmfPlayer$(OBJSUFFIX)", makefile)
        self.assertIn("-lpspmpeg", makefile)

        backend_path = REPO / "third_party" / "libpspav" / "src" / "pspav.c"
        self.assertTrue(backend_path.is_file(), "vendored libpspav backend is missing")
        backend = backend_path.read_text(encoding="utf-8")
        self.assertIn("int pspavPlayVideoFileOnce", backend)
        self.assertIn('strcasecmp(ext, ".mps") == 0', backend)
        self.assertIn("sceIoClose(pspavfd)", backend)


if __name__ == "__main__":
    unittest.main()
