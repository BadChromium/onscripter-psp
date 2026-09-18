"""Compile actual routing code for independent game identities."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from test_cp936_runtime import REPO, run_msvc

class SavedataIdentityTest(unittest.TestCase):
    def test_separate_game_namespaces_and_invalid_identity(self):
        for game_id in ('TEST00001', 'TEST00002', '../BAD001'):
            with self.subTest(game_id=game_id), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                source = folder / 'routing.cpp'
                source.write_text('''
#define ONS_PSP_GAME_ID "%s"
#include "PSPSavedata.h"
int main() {
 char path[512];
 if (onsPspSavePath("ms0:/game/", "image.png", path, sizeof(path)) != 0) return 1;
 if (!onsPspValidGameId())
   return onsPspSavePath("ms0:/game/", "save1.dat", path, sizeof(path)) == -1 ? 0 : 2;
 if (onsPspSavePath("ms0:/game/", "save1.dat", path, sizeof(path)) != 1) return 3;
 if (strcmp(path,"ms0:/PSP/SAVEDATA/" ONS_PSP_GAME_ID "01/DATA.BIN")) return 4;
 if (onsPspSavePath("ef0:/game/", "envdata", path, sizeof(path)) != 1) return 5;
 if (strcmp(path,"ef0:/PSP/SAVEDATA/" ONS_PSP_GAME_ID "CFG/ENV.DAT")) return 6;
 if (onsPspSavePath("ms0:/game/", "save1.dat", path, 4) != -1) return 7;
 return 0;
}
''' % game_id, encoding='ascii')
                exe = folder / 'routing.exe'
                build = run_msvc(f'cl /nologo /I"{REPO}" "{source}" /Fe:"{exe}"', folder)
                self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
                run = subprocess.run([str(exe)], capture_output=True)
                self.assertEqual(run.returncode, 0)

if __name__ == '__main__':
    unittest.main()
