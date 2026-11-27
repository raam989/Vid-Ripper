"""Vid-Ripper asztali build: Windows (hordozható mappa + zip), Linux (AppImage tar.gz-ben),
Mac (.app + zip). Ugyanazt a vidripper.py-t építi, a rendszernek megfelelően.

Használat (a vidripper.py melletti mappából):
    python build_desktop.py
Előfeltétel: pip install pyinstaller pillow sounddevice "yt-dlp[curl-cffi]"
Windowson az ffmpeg.exe és ffprobe.exe a program mellé kerül: add meg a mappájukat az
FFMPEG_DIR környezeti változóval (a GitHub Actions ezt magától megcsinálja).
Ugyanígy az mpv.exe: MPV_DIR (a lejátszó ezt használja).
"""
import os
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "vidripper.py")
NAME = "Vid-Ripper"
DIST = os.path.join(HERE, "dist")


def run(cmd):
    print(">", " ".join(cmd), flush=True)
    code = subprocess.call(cmd, cwd=HERE)
    if code != 0:
        sys.exit(f"A lépés nem sikerült (kilépési kód: {code}).")


def app_version():
    text = open(SCRIPT, encoding="utf-8").read()
    m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "x"


def make_icon(kind):
    """Az icon.png-ből a rendszernek való ikon. Visszaadja az útvonalát, vagy None."""
    png = os.path.join(HERE, "icon.png")
    if not os.path.exists(png) or kind == "linux":
        return None
    from PIL import Image
    img = Image.open(png).convert("RGBA")
    out = os.path.join(HERE, "icon.ico" if kind == "win" else "icon.icns")
    if kind == "win":
        img.save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    else:
        img.save(out)
    return out


def copy_licenses(dest, ffmpeg_dir=None):
    """A saját licenc, a harmadik féltől származó részek listája és a licencszövegek
    (GPL stb.) a csomagba. Nyilvános terjesztésnél ezeknek a program mellett kell lenniük."""
    os.makedirs(dest, exist_ok=True)
    for name in ("LICENSE", "THIRD_PARTY_LICENSES.md"):
        src = os.path.join(HERE, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dest, name + (".txt" if name == "LICENSE" else "")))
    lic = os.path.join(HERE, "licenses")
    if os.path.isdir(lic):
        for fn in os.listdir(lic):
            shutil.copy2(os.path.join(lic, fn), dest)
    if ffmpeg_dir:  # a gyan.dev csomagjában az ffmpeg saját LICENSE fájlja a bin mellett van
        for cand in (os.path.join(ffmpeg_dir, "..", "LICENSE"),
                     os.path.join(ffmpeg_dir, "..", "LICENSE.txt")):
            if os.path.exists(cand):
                shutil.copy2(cand, os.path.join(dest, "ffmpeg-LICENSE.txt"))
                break


def zip_dir(src, dest):
    base = os.path.dirname(src)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(src):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, base))


def main():
    if not os.path.exists(SCRIPT):
        sys.exit("Nem találom a vidripper.py fájlt: " + SCRIPT)
    kind = "mac" if sys.platform == "darwin" else ("win" if sys.platform.startswith("win")
                                                   else "linux")
    version = app_version()
    print(f"Vid-Ripper {version} építése ({kind})")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
           "--name", NAME, "--collect-all", "yt_dlp", "--collect-all", "curl_cffi",
           "--collect-all", "PIL", "--collect-all", "sounddevice",
           "--collect-all", "tkinterdnd2"]
    icon = make_icon(kind)
    if icon:
        cmd += ["--icon", icon]
    for extra in ("icon.png", "kofi.png"):  # az ablakikonhoz és a Támogatás ikonhoz
        path = os.path.join(HERE, extra)
        if os.path.exists(path):
            cmd += ["--add-data", path + os.pathsep + "."]
    cmd.append(SCRIPT)
    run(cmd)

    os.makedirs(DIST, exist_ok=True)
    if kind == "mac":
        app = os.path.join(DIST, NAME + ".app")
        copy_licenses(os.path.join(app, "Contents", "Resources", "licenses"))
        out = os.path.join(DIST, f"Vid-Ripper-{version}-Mac.zip")
        run(["ditto", "-c", "-k", "--keepParent", app, out])
        # telepítő: bemásolja az appot és leszedi a karantén jelölést (Gatekeeper)
        inst = os.path.join(HERE, "install_mac.sh")
        if os.path.exists(inst):
            shutil.copy2(inst, DIST)
    elif kind == "win":
        folder = os.path.join(DIST, NAME)
        # a segédprogramok az _internal/tools mappába kerülnek: a fő mappában csak az exe látszik
        tools = os.path.join(folder, "_internal", "tools")
        os.makedirs(tools, exist_ok=True)
        ff = os.environ.get("FFMPEG_DIR")
        if ff and os.path.isdir(ff):
            for exe in ("ffmpeg.exe", "ffprobe.exe"):
                src = os.path.join(ff, exe)
                if os.path.exists(src):
                    shutil.copy2(src, tools)
        else:
            print("Figyelem: nincs FFMPEG_DIR, az ffmpeg.exe nem kerül a programmal együtt.")
        mp = os.environ.get("MPV_DIR")
        if mp and os.path.isdir(mp):
            for fn in os.listdir(mp):
                if fn.lower() == "mpv.exe" or fn.lower().endswith(".dll"):
                    shutil.copy2(os.path.join(mp, fn), tools)
        else:
            print("Figyelem: nincs MPV_DIR, az mpv.exe nem kerül a programmal együtt (a lejátszó nem működik).")
        copy_licenses(os.path.join(folder, "_internal", "licenses"), ff)
        # az "adatok" mappát az app első indításkor maga hozza létre (rejtve)
        out = os.path.join(DIST, f"Vid-Ripper-{version}-Windows.zip")
        zip_dir(folder, out)
    else:
        out = build_linux(version)
    print("\nKész:", out)


APPRUN = """#!/bin/sh
# Vid-Ripper indító az AppImage-en belül
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/vid-ripper/Vid-Ripper" "$@"
"""

DESKTOP = """[Desktop Entry]
Type=Application
Name=Vid-Ripper
Comment=Videók letöltése
Exec=Vid-Ripper
Icon=vid-ripper
Categories=AudioVideo;Network;
Terminal=false
StartupWMClass=Vid-Ripper
"""


def build_linux(version):
    """Linux: egyetlen AppImage fájl, telepítés nélkül, dupla kattintással indul.
    Mellé kerül az mpv, az ffmpeg és az ffprobe a közös könyvtáraikkal (TOOLS_APPDIR, a
    linuxdeploy készíti); ha a gépen van saját ffmpeg vagy mpv, az app azt használja. Az AppImage egy tar.gz-be kerül, mert az megőrzi
    a futtatási jogot (a sima letöltés elveszítené, és akkor nem indulna kattintásra)."""
    folder = os.path.join(DIST, NAME)
    tools = os.path.join(folder, "_internal", "tools")
    os.makedirs(tools, exist_ok=True)
    mp = os.environ.get("TOOLS_APPDIR")
    if mp and os.path.isdir(os.path.join(mp, "usr")):
        dest = os.path.join(tools, "linux", "usr")
        shutil.copytree(os.path.join(mp, "usr"), dest, symlinks=True, dirs_exist_ok=True)
        # a C++ és gcc futtatókönyvtárat a gép sajátja adja: a régebbi mellécsomagolt
        # változat összeakadna a videókártya meghajtójával
        lib = os.path.join(dest, "lib")
        for fn in os.listdir(lib) if os.path.isdir(lib) else []:
            if fn.startswith(("libstdc++.so", "libgcc_s.so")):
                os.remove(os.path.join(lib, fn))
        for sub in ("share",):  # a kézikönyv és az ikonok nem kellenek
            shutil.rmtree(os.path.join(dest, sub), ignore_errors=True)
    else:
        print("Figyelem: nincs TOOLS_APPDIR, az mpv és az ffmpeg nem kerül a programmal együtt.")
    copy_licenses(os.path.join(folder, "_internal", "licenses"))

    tool = os.environ.get("APPIMAGETOOL")
    if not tool:
        out = os.path.join(DIST, f"Vid-Ripper-{version}-Linux.tar.gz")
        with tarfile.open(out, "w:gz") as t:
            t.add(folder, arcname=NAME)
        print("Figyelem: nincs APPIMAGETOOL, csak a program mappája készült el.")
        return out

    appdir = os.path.join(HERE, "build", "Vid-Ripper.AppDir")
    shutil.rmtree(appdir, ignore_errors=True)
    shutil.copytree(folder, os.path.join(appdir, "usr", "lib", "vid-ripper"), symlinks=True)
    with open(os.path.join(appdir, "AppRun"), "w") as f:
        f.write(APPRUN)
    os.chmod(os.path.join(appdir, "AppRun"), 0o755)
    with open(os.path.join(appdir, "vid-ripper.desktop"), "w") as f:
        f.write(DESKTOP)
    png = os.path.join(HERE, "icon.png")
    if os.path.exists(png):
        from PIL import Image
        Image.open(png).convert("RGBA").resize((256, 256)).save(
            os.path.join(appdir, "vid-ripper.png"))
    image = os.path.join(DIST, f"Vid-Ripper-{version}-x86_64.AppImage")
    env = dict(os.environ, ARCH="x86_64", APPIMAGE_EXTRACT_AND_RUN="1")
    print(">", tool, appdir, image, flush=True)
    if subprocess.call([tool, "--no-appstream", appdir, image], env=env) != 0:
        sys.exit("Az AppImage elkészítése nem sikerült.")
    os.chmod(image, 0o755)
    out = os.path.join(DIST, f"Vid-Ripper-{version}-Linux.tar.gz")
    with tarfile.open(out, "w:gz") as t:
        t.add(image, arcname=os.path.basename(image))
    return out


if __name__ == "__main__":
    main()
