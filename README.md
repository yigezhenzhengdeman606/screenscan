# ScreenScan

Windows 屏幕二维码扫描工具。打开后出现悬浮扫描框，将框拖到二维码周围即可读取内容，无需拿手机扫码。

## 使用

1. 下载 `ScreenScan-v0.1.0-windows-x64.zip`，完整解压。
2. 进入 ScreenScan 文件夹，双击 `ScreenScan.exe`。请保留旁边的 `_internal` 文件夹。
3. 拖动顶部或底部移动扫描框，拖动右下角调整大小，让二维码及其白色边缘完整出现在透明区域内。
4. 识别成功后自动暂停，结果窗口支持复制；单个 HTTP/HTTPS 链接可点击按钮打开浏览器。
5. 点击“继续扫描”开始下一次扫描；关闭结果窗口后保持暂停。

顶部“—”隐藏到系统托盘。点击托盘图标或按 **Ctrl+Alt+Q** 呼出/隐藏；若快捷键被其他程序占用，会显示提示，可使用托盘。顶部“×”退出程序。

## 功能与边界

- 窗口置顶、拖动、缩放；中间区域透明且允许鼠标穿透。
- 每 450ms 尝试捕获扫描区域，后台识别二维码；支持反色和旋转二维码、同一屏幕内多个二维码。
- 屏幕捕获只用于即时扫码，不录制视频，不上传、不保存截图或扫码历史。复制内容会进入系统剪贴板；点击打开链接后浏览器会联网。
- 首版面向 Windows 10/11 x64。每个显示器单独捕获以适配缩放；请把整个二维码放在一台显示器内，暂不拼接跨屏二维码。
- 微信登录、付款等二维码仍需对应应用授权。本工具只能读取二维码内容。
- 受保护视频、锁屏、安全桌面或部分远程桌面窗口可能无法截图。
- v0.1.0 未做数字签名；它是免安装版本，目前没有安装向导或自动更新。

## 开发

安装 Python 3.12 x64，在本目录运行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

测试：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
# 在可交互的 Windows 桌面验证真实屏幕捕获和界面：
.\.venv\Scripts\python.exe -m tests.smoke_ui
```

打包（PowerShell）：

```powershell
$env:PATH = "$PWD\.venv\Scripts;$env:PATH"
.\build.ps1
```

输出为 `dist/ScreenScan-v0.1.0-windows-x64.zip`，包含 Python、Qt 和扫码运行依赖，使用者无需安装 Python。保持目录式打包，允许替换 Qt 动态库；第三方许可证见 `THIRD_PARTY_NOTICES.md` 和 `licenses/`。

## 上传 GitHub

创建名为 ScreenScan 的空仓库，然后将本目录内的源码上传（包括 `.github`，不要上传 `.venv`、`build`、`dist`）。使用 Git 时：

```powershell
git init
git add .
git commit -m "Initial ScreenScan Windows application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ScreenScan.git
git push -u origin main
```

已附 GitHub Actions：push/PR 会运行解码测试并打包，在 Actions 页面下载构建产物。创建版本标签会自动发布 GitHub Release：

```powershell
git tag v0.1.0
git push origin v0.1.0
```

也可以手动创建 Release，将已生成的 Windows ZIP 作为附件上传。网页上传时留意 `.github/workflows/windows.yml` 是否包含在仓库中。

## 技术与许可

界面使用 [Qt for Python](https://doc.qt.io/qtforpython-6/)，识别使用 [ZXing-C++](https://github.com/zxing-cpp/zxing-cpp/tree/master/wrappers/python)。项目自有代码使用 MIT 许可，第三方库遵循各自许可证。
