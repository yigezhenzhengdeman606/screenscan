"""Run on an interactive Windows desktop: real QR -> screen capture -> result UI."""
import sys
import time
from pathlib import Path

import qrcode
from PIL.ImageQt import ImageQt
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QLabel

from screenscan.app import Scanner, STYLE, capture_parts
from screenscan.core import decode

app = QApplication(sys.argv)
app.setStyleSheet(STYLE)
payload = 'https://example.com/ScreenScan-test'
qr = qrcode.make(payload).convert('RGB').resize((270, 270))
background = QLabel()
background.setPixmap(QPixmap.fromImage(ImageQt(qr)))
background.setFixedSize(270, 270)
background.show()
scanner = Scanner()
scanner.timer.stop()
scanner.show()
app.processEvents()
hole = scanner.aperture.geometry().translated(scanner.pos())
background.move(hole.center().x() - 135, hole.center().y() - 135)
scanner.raise_()
for _ in range(10):
    app.processEvents()
    time.sleep(0.05)
assert not scanner.mask().contains(scanner.aperture.geometry().center()), 'Aperture must be a real hole'
parts = capture_parts(hole)
if len(sys.argv) > 1:
    parts[0].save(str(Path(sys.argv[1]).with_name('capture-debug.png')))
    QApplication.primaryScreen().grabWindow(0).save(str(Path(sys.argv[1]).resolve()))
assert any(payload in decode(image) for image in parts), 'Live capture failed'
scanner.scan()
deadline = time.monotonic() + 8
while scanner.dialog is None and time.monotonic() < deadline:
    app.processEvents()
    time.sleep(0.05)
assert scanner.dialog is not None, 'Worker did not deliver result'
assert payload in scanner.dialog.result.toPlainText()
assert not scanner.running, 'Must pause on success'
scanner.dialog.accept()
app.processEvents()
assert scanner.running, 'Continue must resume'
scanner.set_running(False)
scanner.decoded(['stale result'], '', scanner.generation - 1)
assert scanner.dialog is None, 'Stale results must be ignored'
scanner.resize(520, 460)
app.processEvents()
assert not scanner.mask().contains(scanner.aperture.geometry().center())
if len(sys.argv) > 1:
    QApplication.primaryScreen().grabWindow(0).save(str(Path(sys.argv[1]).resolve()))
scanner.close()
background.close()
print('PASS: live screen capture, transparent aperture, asynchronous result, pause/resume, stale-result guard, resize')
