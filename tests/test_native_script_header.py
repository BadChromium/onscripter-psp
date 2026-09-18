import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VCVARS64 = Path(
    "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat"
)


def run_msvc(command, cwd):
    if not VCVARS64.exists():
        return subprocess.CompletedProcess(
            args=[], returncode=40, stdout="", stderr=f"missing {VCVARS64}"
        )
    full = f'call "{VCVARS64}" >nul && {command}'
    return subprocess.run(
        full,
        cwd=cwd,
        text=True,
        encoding="mbcs",
        capture_output=True,
        check=False,
        shell=True,
    )


class NativeScriptHeaderTest(unittest.TestCase):
    def test_compiled_script_handler_reads_native_header_and_global_border(self):
        self.check_native_header(272)

    def test_compiled_script_handler_reads_270p_header(self):
        self.check_native_header(270)

    def check_native_header(self, height):
        with tempfile.TemporaryDirectory(dir=REPO) as tmp_name:
            tmp = Path(tmp_name)
            script_dir = tmp / "game"
            script_dir.mkdir()
            (script_dir / "0.txt").write_bytes(
                f";$V4000G1500S480,{height}\r\n*define\r\n*start\r\nend\r\n".encode("ascii")
            )
            harness = tmp / "header_harness.cpp"
            harness.write_text(
                textwrap.dedent(
                    r"""
                    #include <stdio.h>
                    #include "ScriptHandler.h"

                    int main(int argc, char **argv) {
                        if (argc != 2) return 2;
                        ScriptHandler h;
                        if (h.readScript(argv[1]) != 0) return 3;
                        if (h.screen_size != ScriptHandler::SCREEN_SIZE_SCRIPT) return 4;
                        if (h.script_width != 480) return 5;
                        if (h.script_height != EXPECTED_HEIGHT) return 6;
                        if (h.global_variable_border != 1500) return 7;
                        return 0;
                    }
                    """
                ),
                encoding="ascii",
            )
            exe = tmp / "header_harness.exe"
            command = (
                f'cl /nologo /DEXPECTED_HEIGHT={height} /I"{REPO}" "{REPO / "ScriptHandler.cpp"}" '
                f'"{REPO / "sjis2utf16.cpp"}" "{harness}" /Fe:"{exe}"'
            )
            build = run_msvc(command, REPO)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(exe), str(script_dir).replace("\\", "/") + "/"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_psp_scaling_is_bypassed_only_for_script_native_mode(self):
        parser = (REPO / "ScriptParser.cpp").read_text(encoding="utf-8", errors="ignore")
        label = (REPO / "ONScripterLabel.cpp").read_text(encoding="utf-8", errors="ignore")
        makefile = (REPO / "Makefile.PSP").read_text(encoding="utf-8")

        self.assertIn("SCREEN_SIZE_SCRIPT", parser)
        self.assertIn("screen_ratio1 = 1;", parser)
        self.assertIn("screen_ratio2 = 1;", parser)
        self.assertIn("screen_width  = script_h.script_width;", parser)
        self.assertIn("script_h.screen_size != ScriptHandler::SCREEN_SIZE_SCRIPT", label)
        self.assertIn("screen_width   = screen_width  * 9 / 8;", label)
        self.assertIn("-DONS_CN_CP936", makefile)


if __name__ == "__main__":
    unittest.main()
