# Third-party software

Vid-Ripper itself is released under the MIT License (see `LICENSE`). The ready-made
packages on the Releases page also contain the following third-party software, each under
its own license. Full license texts that are not included in the component itself are in
the `licenses` folder.

## Bundled in every package (Mac, Windows, Linux)

| Component | License | Source |
|---|---|---|
| Python | PSF License | https://www.python.org/downloads/source/ |
| Tcl/Tk | Tcl/Tk License (BSD-style) | https://www.tcl-lang.org/software/tcltk/ |
| yt-dlp | The Unlicense (public domain) | https://github.com/yt-dlp/yt-dlp |
| curl_cffi (with curl-impersonate, libcurl, BoringSSL, nghttp2, brotli, zstd) | MIT and the respective upstream licenses | https://github.com/lexiforest/curl_cffi |
| cffi | MIT | https://github.com/python-cffi/cffi |
| certifi | MPL-2.0 (`licenses/MPL-2.0.txt`) | https://github.com/certifi/python-certifi |
| Pillow (with libjpeg-turbo, libpng, zlib, libtiff, libwebp, FreeType and others) | MIT-CMU and the respective upstream licenses | https://github.com/python-pillow/Pillow |
| python-sounddevice | MIT | https://github.com/spatialaudio/python-sounddevice |
| PortAudio | MIT | https://github.com/PortAudio/portaudio |
| tkinterdnd2 (with tkdnd) | MIT, BSD | https://github.com/Eliav2/tkinterdnd2 |
| PyInstaller bootloader | GPL-2.0 with the PyInstaller exception (`licenses/GPL-2.0.txt`) | https://github.com/pyinstaller/pyinstaller |

## Windows package only

| Component | License | Source |
|---|---|---|
| FFmpeg (ffmpeg.exe, ffprobe.exe), "release essentials" build by gyan.dev | GPL-3.0 (`licenses/GPL-3.0.txt`, and `ffmpeg-LICENSE.txt` from the build when present) | https://www.gyan.dev/ffmpeg/builds/ and https://ffmpeg.org/download.html |
| mpv (mpv.exe and its libraries), build by shinchiro | GPL-2.0 or later (`licenses/GPL-2.0.txt`, `licenses/GPL-3.0.txt`) | https://github.com/shinchiro/mpv-winbuild-cmake and https://github.com/mpv-player/mpv |
| Vulkan loader (vulkan-1.dll, only when the mpv build needs it) | Apache-2.0 (`licenses/Apache-2.0.txt`) | https://github.com/KhronosGroup/Vulkan-Loader |

## Linux package only

| Component | License | Source |
|---|---|---|
| FFmpeg (ffmpeg, ffprobe) and its libraries, from Ubuntu 22.04 | GPL-2.0 or later / LGPL-2.1 or later (`licenses/GPL-2.0.txt`, `licenses/LGPL-2.1.txt`) | `apt source ffmpeg` on Ubuntu 22.04, or https://packages.ubuntu.com/jammy/ffmpeg |
| mpv and its libraries, from Ubuntu 22.04 | GPL-2.0 or later (`licenses/GPL-2.0.txt`) | `apt source mpv` on Ubuntu 22.04, or https://packages.ubuntu.com/jammy/mpv |
| Other shared libraries copied next to ffmpeg and mpv by linuxdeploy | their respective licenses, as packaged by Ubuntu 22.04 | https://packages.ubuntu.com/jammy/ |

The Mac package does not contain FFmpeg or mpv. On a Mac they are installed separately,
for example with Homebrew (`brew install ffmpeg mpv`).

FFmpeg and mpv run as separate programs; Vid-Ripper only starts them. The exact source
code of the bundled FFmpeg and mpv builds is available from the links above. If a link
stops working, open an issue on this repository and the source will be provided.
