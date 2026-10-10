import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('manage', ROOT / 'scripts' / 'manage.py')
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'custom scripts'
        self.folder.mkdir()

    def test_roundtrip_without_existing_files(self):
        manage.install(self.folder)
        self.assertTrue((self.folder / manage.MANIFEST).exists())
        manage.uninstall(self.folder)
        for name in (*manage.FILES, 'userSetup.py', manage.MANIFEST):
            self.assertFalse((self.folder / name).exists())

    def test_restores_modules_and_preserves_later_startup_edits(self):
        original = b'# existing setup\r\nprint("hello")\r\n'
        setup = self.folder / 'userSetup.py'
        setup.write_bytes(original)
        originals = {name: ('# previous ' + name + '\n').encode() for name in manage.FILES}
        for name, data in originals.items(): (self.folder / name).write_bytes(data)
        manage.install(self.folder)
        setup.write_bytes(setup.read_bytes() + b'\n# later unrelated edit\n')
        manage.uninstall(self.folder)
        self.assertEqual(setup.read_bytes(), original + b'\n# later unrelated edit\n')
        for name, data in originals.items(): self.assertEqual((self.folder / name).read_bytes(), data)

    def test_modified_module_refuses_all_removals(self):
        manage.install(self.folder)
        target = self.folder / manage.FILES[0]
        target.write_bytes(target.read_bytes() + b'\n# local edit\n')
        setup_before = (self.folder / 'userSetup.py').read_bytes()
        with self.assertRaises(ValueError): manage.uninstall(self.folder)
        self.assertEqual((self.folder / 'userSetup.py').read_bytes(), setup_before)
        self.assertTrue((self.folder / manage.FILES[1]).exists())

    def test_modified_hook_refuses_all_removals(self):
        manage.install(self.folder)
        setup = self.folder / 'userSetup.py'
        setup.write_bytes(setup.read_bytes().replace(b'arnold_qt_canvas_auto.start()', b'arnold_qt_canvas_auto.stop()'))
        with self.assertRaises(ValueError): manage.uninstall(self.folder)
        self.assertTrue((self.folder / manage.FILES[0]).exists())

    def test_duplicate_install_is_idempotent(self):
        manage.install(self.folder)
        before = (self.folder / 'userSetup.py').read_bytes()
        manage.install(self.folder)
        self.assertEqual((self.folder / 'userSetup.py').read_bytes(), before)
        self.assertEqual(len(list(self.folder.glob('.arnold-qt-backup-*'))), 1)

    def test_legacy_hook_is_not_adopted(self):
        (self.folder / 'userSetup.py').write_text('# BEGIN Arnold Qt canvas\n')
        with self.assertRaises(ValueError): manage.install(self.folder)
        self.assertFalse((self.folder / manage.FILES[0]).exists())

    def test_invalid_startup_is_rejected_before_copying(self):
        setup = self.folder / 'userSetup.py'
        setup.write_text('invalid python !!!\n')
        with self.assertRaises(SyntaxError): manage.install(self.folder)
        self.assertFalse((self.folder / manage.FILES[0]).exists())
        self.assertFalse(list(self.folder.glob('.arnold-qt-backup-*')))

    def test_missing_manifest_never_removes_files(self):
        target = self.folder / manage.FILES[0]
        target.write_text('# unrelated\n')
        with self.assertRaises(ValueError): manage.uninstall(self.folder)
        self.assertTrue(target.exists())

if __name__ == '__main__': unittest.main()
