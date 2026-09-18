import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

VCVARS64 = Path(
    "C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat"
)


def chapter_cp936_pairs():
    # Generated codec domain, not a copyrighted game fixture.
    pairs = set()
    for high in range(0x81, 0xff):
        for low in range(0x40, 0xff):
            if low == 0x7f:
                continue
            try:
                bytes([high, low]).decode("cp936")
            except UnicodeDecodeError:
                continue
            pairs.add((high << 8) | low)
    return pairs


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


class Cp936RuntimeTest(unittest.TestCase):
    def test_generated_cp936_domain_counts(self):
        pairs = chapter_cp936_pairs()
        sjis_missed = {
            code
            for code in pairs
            if not ((((code >> 8) & 0xE0) == 0xE0) or (((code >> 8) & 0xE0) == 0x80))
        }
        self.assertEqual(len(pairs), 21791)
        self.assertEqual(len(sjis_missed), 10749)

    def test_compiled_codec_helper_classifies_and_maps_generated_cp936_glyphs(self):
        pairs = sorted(chapter_cp936_pairs())
        self.assertEqual(len(pairs), 21791)

        with tempfile.TemporaryDirectory(dir=REPO) as tmp_name:
            tmp = Path(tmp_name)
            expected = tmp / "expected_cp936.tsv"
            expected.write_text(
                "".join(
                    f"{code:04x} {ord(code.to_bytes(2, 'big').decode('cp936')):04x}\n"
                    for code in pairs
                ),
                encoding="ascii",
            )
            harness = tmp / "codec_harness.cpp"
            harness.write_text(
                textwrap.dedent(
                    r"""
                    #include <stdio.h>
                    #include <stdlib.h>

                    void initONSCodeToUTF16();
                    unsigned short convONSCodeToUTF16(unsigned short in);
                    bool onsIsTwoByteLead(unsigned char ch);

                    int main(int argc, char **argv) {
                        if (argc != 2) return 2;
                        initONSCodeToUTF16();
                        if (onsIsTwoByteLead(0x80)) return 3;
                        if (!onsIsTwoByteLead(0x81)) return 4;
                        if (!onsIsTwoByteLead(0xb0)) return 5;
                        if (!onsIsTwoByteLead(0xfe)) return 6;
                        if (onsIsTwoByteLead('A')) return 7;

                        FILE *fp = fopen(argv[1], "r");
                        if (!fp) return 8;
                        unsigned int code = 0, expected = 0;
                        int count = 0;
                        while (fscanf(fp, "%x %x", &code, &expected) == 2) {
                            unsigned short actual = convONSCodeToUTF16((unsigned short)code);
                            if (actual != expected) {
                                fprintf(stderr, "map mismatch %04x got %04x expected %04x\n",
                                        code, actual, expected);
                                fclose(fp);
                                return 9;
                            }
                            count++;
                        }
                        fclose(fp);
                        return count == 21791 ? 0 : 10;
                    }
                    """
                ),
                encoding="ascii",
            )
            exe = tmp / "codec_harness.exe"
            command = (
                f'cl /nologo /DBIMAN_CN_CP936 /I"{REPO}" '
                f'"{REPO / "sjis2utf16.cpp"}" "{harness}" /Fe:"{exe}"'
            )
            build = run_msvc(command, REPO)
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            run = subprocess.run(
                [str(exe), str(expected)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
