import time
import unittest
from unittest.mock import patch

import qrcode
from PySide6.QtWidgets import QApplication, QDialog

from screenscan.app import Scanner, STYLE


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(STYLE)

    def test_async_decode_and_controls(self):
        scanner = Scanner()
        scanner.timer.stop()
        scanner.show()
        self.app.processEvents()
        try:
            self.assertFalse(scanner.mask().contains(scanner.aperture.geometry().center()))
            scanner.resize(520, 460)
            self.app.processEvents()
            self.assertFalse(scanner.mask().contains(scanner.aperture.geometry().center()))
            image = qrcode.make('https://example.com/test').convert('RGB')
            with patch('screenscan.app.capture_parts', return_value=[image]):
                scanner.scan()
            deadline = time.monotonic() + 5
            while scanner.dialog is None and time.monotonic() < deadline:
                self.app.processEvents()
                time.sleep(0.01)
            self.assertIsNotNone(scanner.dialog)
            self.assertEqual(scanner.dialog.result.toPlainText(), 'https://example.com/test')
            self.assertFalse(scanner.running)
            scanner.dialog.done(QDialog.DialogCode.Accepted)
            self.app.processEvents()
            self.assertTrue(scanner.running)
            scanner.set_running(False)
            scanner.decoded(['old result'], '', scanner.generation - 1)
            self.assertIsNone(scanner.dialog)
        finally:
            scanner.close()


if __name__ == '__main__':
    unittest.main()
