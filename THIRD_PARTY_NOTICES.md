# Third-party notices

ScreenScan original source is MIT licensed. The Windows distribution also includes:

| Component | License | Upstream source |
| --- | --- | --- |
| Python 3.12 | PSF License | https://www.python.org/downloads/source/ |
| PySide6 Essentials / Shiboken6 6.8.3 | LGPLv3 (open source distribution) | https://code.qt.io/cgit/pyside/pyside-setup.git/tag/?h=v6.8.3 |
| Qt 6.8.3 runtime modules | LGPLv3 and module-specific notices | https://download.qt.io/archive/qt/6.8/6.8.3/submodules/ |
| ZXing-C++ 2.3.0 | Apache-2.0 | https://github.com/zxing-cpp/zxing-cpp/tree/v2.3.0 |
| Pillow 11.2.1 | MIT-CMU and bundled library notices | https://github.com/python-pillow/Pillow/tree/11.2.1 |
| PyInstaller bootloader | GPL with distribution exception | https://github.com/pyinstaller/pyinstaller/tree/v6.13.0 |

License texts are supplied in `licenses/`; Pillow's text includes bundled codec notices. Python's license is also included. Dependency metadata accompanies the binary under `_internal`.

Qt and PySide remain separate dynamic libraries in `_internal`. Users may replace them with compatible modified builds. ScreenScan does not restrict reverse engineering for debugging modifications to LGPL libraries. Build instructions and all application source are provided in the companion source archive / GitHub repository. Qt source and notices are available at the upstream links above; keep this file and licenses with redistributed copies.

Development-only qrcode, packaging tools and their dependencies are not imported by ScreenScan at runtime.
