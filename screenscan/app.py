import ctypes
import sys
from ctypes import wintypes

from PIL import Image
from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Qt, Signal, QUrl
from PySide6.QtGui import (QAction, QColor, QDesktopServices, QIcon, QImage,
                           QPainter, QPen, QPixmap, QRegion)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QMenu, QMessageBox, QPushButton, QSizeGrip, QSystemTrayIcon, QTextEdit,
    QVBoxLayout, QWidget)

from .core import decode, web_url

STYLE = """
QWidget { color: #e8edf5; font-family: 'Microsoft YaHei UI'; font-size: 12px; }
QDialog { background: #151e2e; }
QPushButton { background: #29364d; border: 0; border-radius: 5px; padding: 6px 10px; }
QPushButton:hover { background: #3c526e; }
QPushButton:disabled { color: #728096; }
QTextEdit { background: #0d1420; border: 1px solid #33445c; padding: 8px; }
QMenu { background: #151e2e; }
QMenu::item:selected { background: #33445c; }
"""


def app_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor('#151e2e'))
    painter = QPainter(pixmap)
    painter.setPen(QPen(QColor('#38e0ae'), 5))
    for x, y, dx, dy in [(12, 12, 1, 1), (52, 12, -1, 1),
                          (12, 52, 1, -1), (52, 52, -1, -1)]:
        painter.drawLine(x, y, x + dx * 14, y)
        painter.drawLine(x, y, x, y + dy * 14)
    painter.drawLine(18, 32, 46, 32)
    painter.end()
    return QIcon(pixmap)


def capture_parts(rect):
    """Capture each monitor separately so Qt handles its own DPI scaling."""
    images = []
    for screen in QApplication.screens():
        part = rect.intersected(screen.geometry())
        if part.isEmpty():
            continue
        local = part.topLeft() - screen.geometry().topLeft()
        pixmap = screen.grabWindow(0, local.x(), local.y(), part.width(), part.height())
        if pixmap.isNull():
            raise RuntimeError('屏幕捕获失败，请检查远程桌面或受保护窗口。')
        image = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB888)
        images.append(Image.frombytes('RGB', (image.width(), image.height()),
            bytes(image.constBits()), 'raw', 'RGB', image.bytesPerLine()))
    if not images:
        raise RuntimeError('扫描框未覆盖可用屏幕，请将它拖回屏幕内。')
    return images


class Signals(QObject):
    finished = Signal(list, str, int)


class DecodeTask(QRunnable):
    def __init__(self, images, generation):
        super().__init__()
        self.images, self.generation = images, generation
        self.signals = Signals()

    def run(self):
        try:
            results = list(dict.fromkeys(text for image in self.images for text in decode(image)))
            self.signals.finished.emit(results, '', self.generation)
        except Exception as exc:
            self.signals.finished.emit([], str(exc), self.generation)


class ResultDialog(QDialog):
    def __init__(self, results, parent):
        super().__init__(parent)
        self.setWindowTitle('ScreenScan · 扫码结果')
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.resize(520, 330)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'识别到 {len(results)} 个二维码 · 内容仅保留在本次窗口中'))
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        self.result.setPlainText('\n\n'.join(results))
        layout.addWidget(self.result)
        row = QHBoxLayout()
        copy = QPushButton('复制内容')
        copy.clicked.connect(lambda: QApplication.clipboard().setText(self.result.toPlainText()))
        row.addWidget(copy)
        open_button = QPushButton('在浏览器打开')
        url = web_url(results[0]) if len(results) == 1 else None
        open_button.setEnabled(url is not None)
        open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        row.addWidget(open_button)
        resume = QPushButton('继续扫描')
        resume.clicked.connect(self.accept)
        row.addWidget(resume)
        layout.addLayout(row)


class Scanner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ScreenScan')
        self.setWindowIcon(app_icon())
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(370, 300)
        self.resize(440, 430)
        self.running = True
        self.busy = False
        self.generation = 0
        self.drag_offset = None
        self.dialog = None
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        header = QHBoxLayout()
        title = QLabel('▣  ScreenScan')
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header.addWidget(title)
        header.addStretch()
        self.pause = QPushButton('暂停')
        self.pause.clicked.connect(self.toggle)
        header.addWidget(self.pause)
        minimize = QPushButton('—')
        minimize.setToolTip('隐藏到托盘；Ctrl+Alt+Q 呼出')
        minimize.clicked.connect(self.hide_scanner)
        header.addWidget(minimize)
        close = QPushButton('×')
        close.clicked.connect(self.close)
        header.addWidget(close)
        layout.addLayout(header)
        self.aperture = QWidget()
        self.aperture.setMinimumSize(240, 180)
        layout.addWidget(self.aperture, 1)
        self.status = QLabel('将二维码完整放入框内 · 拖动顶部移动')
        self.status.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.status)
        footer = QHBoxLayout()
        self.hint = QLabel('本地识别  ·  右下角调整大小')
        footer.addWidget(self.hint)
        footer.addStretch()
        footer.addWidget(QSizeGrip(self))
        layout.addLayout(footer)
        self.timer = QTimer(self)
        self.timer.setInterval(450)
        self.timer.timeout.connect(self.scan)
        self.timer.start()
        self.tray = QSystemTrayIcon(app_icon(), self)
        self.tray.setToolTip('ScreenScan · Ctrl+Alt+Q')
        menu = QMenu(self)
        show_action = QAction('显示扫描框', self)
        show_action.triggered.connect(self.show_scanner)
        menu.addAction(show_action)
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.show_scanner()
            if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()
        self.hotkey_registered = False
        if sys.platform == 'win32':
            self.hotkey_registered = bool(ctypes.windll.user32.RegisterHotKey(
                int(self.winId()), 1, 0x4000 | 0x0002 | 0x0001, ord('Q')))
        if not self.hotkey_registered:
            self.hint.setText('快捷键不可用 · 可从托盘呼出')
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center() - self.rect().center())
        QTimer.singleShot(0, self.update_mask)

    def update_mask(self):
        self.layout().activate()
        # A real window-region hole: desktop stays visible and receives mouse input.
        self.setMask(QRegion(self.rect()).subtracted(QRegion(self.aperture.geometry())))
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'aperture'):
            self.update_mask()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#151e2e'))
        frame = self.aperture.geometry().adjusted(-3, -3, 3, 3)
        painter.setPen(QPen(QColor('#38e0ae' if self.running else '#718096'), 2))
        painter.drawRect(frame)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        self.drag_offset = None

    def set_running(self, running):
        self.running = running
        self.generation += 1
        self.pause.setText('暂停' if running else '继续')
        self.status.setText('将二维码完整放入框内 · 拖动顶部移动' if running else '已暂停 · 点击继续扫描')
        self.update()

    def toggle(self):
        self.set_running(not self.running)

    def hide_scanner(self):
        if QSystemTrayIcon.isSystemTrayAvailable() or self.hotkey_registered:
            self.set_running(False)
            self.hide()
        else:
            self.showMinimized()

    def show_scanner(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if self.dialog:
            self.dialog.raise_()
        else:
            self.set_running(True)

    def scan(self):
        if not self.running or self.busy or not self.isVisible() or self.isMinimized():
            return
        rect = self.aperture.geometry().translated(self.mapToGlobal(self.rect().topLeft()))
        try:
            images = capture_parts(rect)
        except Exception as exc:
            self.status.setText(str(exc))
            return
        self.busy = True
        self.task = DecodeTask(images, self.generation)
        self.task.signals.finished.connect(self.decoded)
        self.pool.start(self.task)

    def decoded(self, results, error, generation):
        self.busy = False
        if generation != self.generation or not self.running:
            return
        if error:
            self.status.setText('识别失败：' + error)
        elif results:
            self.set_running(False)
            QApplication.beep()
            self.dialog = ResultDialog(results, self)
            self.dialog.finished.connect(self.result_closed)
            self.dialog.show()

    def result_closed(self, result):
        self.dialog.deleteLater()
        self.dialog = None
        if result == QDialog.DialogCode.Accepted:
            self.set_running(True)

    def nativeEvent(self, event_type, message):
        if sys.platform == 'win32':
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == 1:
                self.show_scanner() if not self.isVisible() else self.hide_scanner()
                return True, 0
        return super().nativeEvent(event_type, message)

    def closeEvent(self, event):
        self.timer.stop()
        self.set_running(False)
        if self.hotkey_registered:
            ctypes.windll.user32.UnregisterHotKey(int(self.winId()), 1)
        self.tray.hide()
        self.pool.waitForDone()
        event.accept()
        QApplication.instance().quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('ScreenScan')
    app.setStyleSheet(STYLE)
    app.setWindowIcon(app_icon())
    scanner = Scanner()
    scanner.show()
    return app.exec()
