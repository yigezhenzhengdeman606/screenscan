$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
python -m PyInstaller --noconfirm --clean --windowed --onedir --name ScreenScan --collect-all zxingcpp --copy-metadata PySide6-Essentials --copy-metadata shiboken6 --copy-metadata Pillow --copy-metadata zxing-cpp main.py
if ($LASTEXITCODE -ne 0) { throw '打包失败' }
Copy-Item README.md, LICENSE, THIRD_PARTY_NOTICES.md, VALIDATION.md -Destination dist/ScreenScan
Copy-Item licenses -Destination dist/ScreenScan/licenses -Recurse -Force
Compress-Archive -Path dist/ScreenScan -DestinationPath dist/ScreenScan-v0.1.0-windows-x64.zip -Force
Write-Host '已生成 dist/ScreenScan-v0.1.0-windows-x64.zip'
