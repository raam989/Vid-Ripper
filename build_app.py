import os
import subprocess
import sys
import venv

# Ezt a fájlt ugyanabba a mappába kell tenni, ahol a vidripper.py, a translations.py és az icon.png van
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "vidripper.py")


def app_name():
    """A fejlesztői változat (a verzióban "-dev") külön app: Vid-Ripper Dev."""
    import re
    try:
        text = open(SCRIPT, encoding="utf-8").read()
    except OSError:
        return "Vid-Ripper"
    m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.M)
    return "Vid-Ripper Dev" if m and "-dev" in m.group(1) else "Vid-Ripper"


NAME = app_name()
ICON_PNG = os.path.join(HERE, "icon.png")
ICON_ICNS = os.path.join(HERE, "icon.icns")
ENV = os.path.join(HERE, "phdl-env")
ENV_PY = os.path.join(ENV, "bin", "python")

PYTHON_ORG = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"


def run(cmd):
    print(">", " ".join(cmd), flush=True)
    p = subprocess.Popen(cmd, cwd=HERE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    for line in p.stdout:
        print(line, end="", flush=True)
    return p.wait()


if "Thonny.app" in sys.executable:
    sys.exit(
        "Ezt a scriptet nem a Thonny belső Pythonjával kell futtatni, mert abból "
        "hiányzik a Tk könyvtár, és emiatt nem lehet belőle appot csomagolni.\n\n"
        "Telepítsd a Pythont a python.org oldalról, majd futtasd Terminalból:\n"
        f"{PYTHON_ORG} {os.path.join(HERE, 'build_app.py')}")

if not os.path.exists(SCRIPT):
    sys.exit("Nem találom a vidripper.py fájlt itt: " + SCRIPT +
             "\nEzt a fájlt ugyanabba a mappába told, ahol a vidripper.py van.")

if not os.path.exists(os.path.join(HERE, "translations.py")):
    print("Figyelem: nem találom a translations.py fájlt a vidripper.py mellett, az app csak "
          "magyarul lesz elérhető.\n")

has_icon = os.path.exists(ICON_PNG)
if not has_icon:
    print("Figyelem: nem találom az icon.png fájlt, az app ikon nélkül készül el.\n"
          "Másold az icon.png-t a vidripper.py mellé, ha ikont szeretnél.\n")

print("1/3  Virtuális környezet létrehozása...")
if not os.path.exists(ENV_PY):
    venv.create(ENV, with_pip=True)

print("\n2/3  Csomagok telepítése...")
if run([ENV_PY, "-m", "pip", "install", "pyinstaller", "pillow",
        "sounddevice", "yt-dlp[curl-cffi]",
        # linkek behúzása; a 0.7-től van benne Tk 9-hez való tkdnd (a python.org-os
        # Python 3.13+ Tk 9-et használ, a régebbi tkinterdnd2 azzal nem töltődik be)
        "tkinterdnd2>=0.7"]) != 0:
    sys.exit("A csomagok telepítése nem sikerült, nézd meg a fenti hibát.")

if run([ENV_PY, "-c",
        "import tkinter; print('Tk verzió:', tkinter.TkVersion)"]) != 0:
    sys.exit("Ebben a Pythonban nem működik a tkinter, használd a python.org-os Pythont.")

# az icon.png-ből macOS-es .icns ikon készül (a Pillow tudja)
if has_icon:
    print("\nIkon előkészítése (icon.png -> icon.icns)...")
    if run([ENV_PY, "-c",
            "import sys; from PIL import Image; "
            "Image.open(sys.argv[1]).convert('RGBA').save(sys.argv[2])",
            ICON_PNG, ICON_ICNS]) != 0:
        print("Az .icns ikon készítése nem sikerült, az app ikon nélkül készül el.")
        has_icon = False

print("\n3/3  App összeállítása (ez 2-5 percig is eltarthat, közben fut a kiírás)...")
cmd = [ENV_PY, "-m", "PyInstaller", "--noconfirm", "--windowed",
       "--name", NAME,
       "--collect-all", "yt_dlp",
       "--collect-all", "curl_cffi",
       "--collect-all", "PIL",
       "--collect-all", "tkinterdnd2"]  # a tkdnd natív könyvtárai is kellenek
if has_icon:
    cmd += ["--icon", ICON_ICNS,
            # az ablak- és Dock-ikonhoz az app mellé csomagolt PNG kell
            "--add-data", ICON_PNG + os.pathsep + "."]
KOFI_PNG = os.path.join(HERE, "kofi.png")  # nem kötelező: a Támogatás melletti ikon
if os.path.exists(KOFI_PNG):
    cmd += ["--add-data", KOFI_PNG + os.pathsep + "."]
cmd.append(SCRIPT)
code = run(cmd)
if code != 0:
    sys.exit("Az összeállítás nem sikerült, nézd meg a fenti hibát.")

app = os.path.join(HERE, "dist", NAME + ".app")
print("\nKész! Az app itt van:", app)
if sys.platform == "darwin":
    subprocess.run(["open", "-R", app])
