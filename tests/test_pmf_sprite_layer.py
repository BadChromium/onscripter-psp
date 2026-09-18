import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class PmfSpriteLayerTest(unittest.TestCase):
    def test_engine_integration_documents_exact_tagged_sprite_interface(self):
        doc = (REPO / "ENGINE_INTEGRATION.md").read_text(encoding="utf-8")
        self.assertIn('lsp 5,":v;movie/ha01_01.pmf",0,0', doc)
        self.assertIn("only one PMF sprite layer", doc)
        self.assertIn("csp", doc)
        self.assertIn("vsp", doc)

    def test_tag_parser_recognizes_video_sprite_without_static_image_load(self):
        anim_h = (REPO / "AnimationInfo.h").read_text(encoding="utf-8")
        anim_cpp = (REPO / "ONScripterLabel_animation.cpp").read_text(encoding="utf-8")
        self.assertIn("TRANS_PMF", anim_h)
        self.assertIn("buffer[0] == 'v'", anim_cpp)
        video_branch = re.search(
            r"buffer\[0\] == 'v'.*?anim->trans_mode = AnimationInfo::TRANS_PMF",
            anim_cpp,
            re.DOTALL,
        )
        self.assertIsNotNone(video_branch)

    def test_nonblocking_bridge_uses_worker_publish_callback_and_no_bgm_control(self):
        header = (REPO / "PSPPmfPlayer.h").read_text(encoding="utf-8")
        bridge = (REPO / "PSPPmfPlayer.cpp").read_text(encoding="utf-8")
        entry = (REPO / "third_party/libpspav/include/pspav_entry.h").read_text(
            encoding="utf-8"
        )
        video = (REPO / "third_party/libpspav/src/pspav_video.c").read_text(
            encoding="utf-8"
        )

        for token in [
            "pspPmfLayerStart",
            "pspPmfLayerStop",
            "pspPmfLayerCopyFrame",
            "pspPmfLayerIsRunning",
        ]:
            self.assertIn(token, header)
            self.assertIn(token, bridge)

        self.assertIn("sceKernelCreateThread", bridge)
        self.assertIn("sceKernelWaitThreadEnd", bridge)
        self.assertIn("pspavPlayVideoFileOnce", bridge)
        self.assertIn("while (!pmf_layer_stop_requested)", bridge)
        self.assertNotIn("Mix_HaltMusic", bridge)
        self.assertIn("publishTexture", entry)
        self.assertIn("av_callbacks->publishTexture", video)
        self.assertIn("return av_callbacks->publishTexture", video)

    def test_ons_sprite_lifetime_drives_layer_start_hide_show_clear_and_refresh(self):
        header = (REPO / "ONScripterLabel.h").read_text(encoding="utf-8")
        command = (REPO / "ONScripterLabel_command.cpp").read_text(
            encoding="utf-8", errors="ignore"
        )
        image = (REPO / "ONScripterLabel_image.cpp").read_text(encoding="utf-8")
        animation = (REPO / "ONScripterLabel_animation.cpp").read_text(encoding="utf-8")
        main = (REPO / "ONScripterLabel.cpp").read_text(encoding="utf-8")

        self.assertIn("pmf_sprite_no", header)
        self.assertIn("startPmfSprite", header)
        self.assertIn("stopPmfSprite", header)
        self.assertIn("updatePmfSpriteFrame", header)
        self.assertIn("startPmfSprite(no, &sprite_info[ no ])", command)
        self.assertIn("stopPmfSprite(no)", command)
        self.assertIn("stopPmfSprite(-1)", command)
        self.assertIn("updatePmfSpriteFrame()", image)
        self.assertIn("updatePmfSpriteFrame()", animation)
        self.assertIn("pspPmfLayerStop()", main)

    def test_publish_mode_removes_video_only_fixed_sleeps_and_display_flip(self):
        video = (REPO / "third_party/libpspav/src/pspav_video.c").read_text(
            encoding="utf-8"
        )
        render = re.search(r"int RenderFrame\(DecoderThreadData\* D\).*?\n\}", video, re.DOTALL)
        self.assertIsNotNone(render)
        publish_prefix = render.group(0).split("av_callbacks->publishTexture", 1)[0]
        publish_branch = render.group(0).split("av_callbacks->publishTexture", 1)[1]
        self.assertIn("sceKernelDelayThread(10000)", publish_branch)
        self.assertNotIn("sceKernelDelayThread(10000)", publish_prefix)
        self.assertNotIn("flipScreen", publish_prefix)


if __name__ == "__main__":
    unittest.main()
