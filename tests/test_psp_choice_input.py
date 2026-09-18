from pathlib import Path
import unittest
class PSPInputDefaults(unittest.TestCase):
 def test_psp_startup_honors_script_button_controls(self):
  source=(Path(__file__).resolve().parents[1]/'onscripter.cpp').read_text()
  initialization=source[source.index('ONScripterLabel ons;'):source.index('// Parse options')]
  self.assertNotIn('ons.enableButtonShortCut()',initialization,'Forced shortcuts disable useescspc/getenter and make Cross advance')
  self.assertIn('ons.disableRescale()',initialization)
  self.assertIn('"-force-button-shortcut"',source,'Explicit legacy CLI override remains supported')
 def test_button_results_are_logged_for_physical_diagnosis(self):
  source=(Path(__file__).resolve().parents[1]/'ONScripterLabel_command.cpp').read_text()
  self.assertIn('UI_WAIT button=%d text=%d',source)
if __name__=='__main__':unittest.main()
