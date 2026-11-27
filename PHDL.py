import array
import hashlib
import hmac
import importlib
import io
import json
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import webbrowser
import zipfile
from datetime import datetime, timezone
from tkinter import ttk, filedialog
from tkinter import font as tkfont

APP_NAME = "Vid-Ripper"
APP_VERSION = "5.1.1"
SUPPORT_URL = "https://ko-fi.com/twosix989"
CREDIT = "app by 2six"
OLD_APP_NAME = "PH Downloader"  # a régi adatmappa neve, az átvitelhez


# ========== Platform: minden rendszerfüggő dolog egy helyen ==========
# A függvények hívásnál nézik a rendszert (nem importnál), így tesztelhetők és egy helyen
# kell módosítani, ha egy rendszeren valami másképp működik.
def is_mac():
    return sys.platform == "darwin"


def is_win():
    return sys.platform.startswith("win")


def hide_support_folders():
    """Windowson, a kész programnál az exe melletti _internal és adatok mappa rejtett lesz,
    így a mappában csak a Vid-Ripper.exe látszik. Máshol nem csinál semmit."""
    if not (is_win() and getattr(sys, "frozen", False)):
        return
    try:
        import ctypes
        set_attr = ctypes.windll.kernel32.SetFileAttributesW
        get_attr = ctypes.windll.kernel32.GetFileAttributesW
        for name in ("_internal", "adatok"):
            path = os.path.join(app_dir(), name)
            if not os.path.isdir(path):
                continue
            attrs = get_attr(path)
            if attrs != -1 and attrs != 0xFFFFFFFF and not attrs & 0x2:
                set_attr(path, attrs | 0x2)  # FILE_ATTRIBUTE_HIDDEN
    except Exception:
        pass


def enable_sharp_scaling():
    """Windowson nagyobb képernyő-skálázásnál (125%, 150%) a nem DPI-érzékeny program ablakát
    a rendszer pixelesen nagyítja, ezért homályos. A GDI-skálázásos mód (Windows 10, 1809-től)
    a szöveget és a rajzot a valódi felbontáson rajzolja, az elrendezés pedig ugyanaz marad.
    Az első ablak létrehozása ELŐTT kell hívni. Régebbi Windowson nem csinál semmit."""
    if not is_win():
        return False
    try:
        import ctypes
        fn = ctypes.windll.user32.SetProcessDpiAwarenessContext
        fn.argtypes = [ctypes.c_void_p]
        return bool(fn(ctypes.c_void_p(-5)))  # DPI_AWARENESS_CONTEXT_UNAWARE_GDISCALED
    except Exception:
        return False


def make_quiet_popen(base):
    """Windowson az ablak nélküli (windowed) programból indított ffmpeg/ffprobe külön fekete
    konzolablakot nyitna. Ez a Popen minden új folyamatot konzolablak nélkül indít."""
    CREATE_NO_WINDOW = 0x08000000

    class QuietPopen(base):
        def __init__(self, *args, **kwargs):
            kwargs["creationflags"] = kwargs.get("creationflags", 0) | CREATE_NO_WINDOW
            super().__init__(*args, **kwargs)

    return QuietPopen


if is_win():
    subprocess.Popen = make_quiet_popen(subprocess.Popen)  # subprocess.run is ezt használja


# ---------- nyelv ----------
# A felület szövegei magyarul vannak a kódban. Az angol és a német fordítás a translations.py
# fájlban van, ott a magyar szöveg a kulcs. A t() a kiválasztott nyelvű változatot adja
# vissza; ha egy szövegnek nincs fordítása, a magyar marad.
try:
    import translations as _translations
except Exception:
    _translations = None
LANGUAGES = {"hu": "Magyar", "en": "English", "de": "Deutsch"}  # a saját nyelvükön
LANG = "hu"
_TR = {}


def t(text):
    return _TR.get(text, text)


def set_language(code):
    global LANG, _TR
    LANG = code if code in LANGUAGES else "en"
    table = getattr(_translations, LANG.upper(), None) if LANG != "hu" else None
    _TR = table if isinstance(table, dict) else {}


def system_language():
    """A rendszer nyelve: hu, de vagy en. Minden más nyelvnél angol."""
    import locale
    codes = []
    try:
        if is_mac():
            out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"],
                                 capture_output=True, text=True, timeout=3).stdout
            codes += re.findall(r'"?([A-Za-z]{2,3})[-_"\s,]', out)
        elif is_win():
            import ctypes
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            codes.append(locale.windows_locale.get(lcid, ""))
    except Exception:
        pass
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        codes += (os.environ.get(var) or "").split(":")
    try:
        codes.append(locale.getlocale()[0] or "")
    except Exception:
        pass
    for code in codes:
        code = code.strip().lower()
        if not code or code in ("c", "posix") or code.startswith(("c.", "posix")):
            continue
        return code[:2] if code[:2] in LANGUAGES else "en"
    return "en"


# Macen a rendszer saját betűtípusa (SF), Windowson a Segoe UI, Linuxon a Helvetica (a Tk
# a rendszer betűire képezi le)
FONT_FAMILY = ".AppleSystemUIFont" if is_mac() else ("Segoe UI" if is_win() else "Helvetica")
MOD_KEY = "Command" if is_mac() else "Control"  # a gyorsbillentyűk módosítója
BROWSER_NAMES = (["safari"] if is_mac() else []) + ["chrome", "firefox", "edge", "brave"]


def linux_bundle_dir():
    """A Linuxos kész programban (AppImage) a mellécsomagolt segédprogramok mappája, vagy None."""
    if not (getattr(sys, "frozen", False) and sys.platform.startswith("linux")):
        return None
    return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "_internal", "tools")


def _prepare_linux_bundle():
    """A kész Linuxos programban a PyInstaller a saját könyvtárait teszi az LD_LIBRARY_PATH
    elejére. Az általunk indított programok (mpv, ffmpeg, fájlkezelő) ezt örökölnék, és rossz
    könyvtárakat töltenének be, ezért visszaállítjuk az eredetit. A beépített lejátszó
    hangjához a mellécsomagolt libportaudio-t használjuk, ha a gépen nincs."""
    tools = linux_bundle_dir()
    if not tools:
        return
    orig = os.environ.get("LD_LIBRARY_PATH_ORIG")
    if orig is not None:
        os.environ["LD_LIBRARY_PATH"] = orig
    else:
        os.environ.pop("LD_LIBRARY_PATH", None)
    pa = os.path.join(tools, "linux", "usr", "lib", "libportaudio.so.2")
    if os.path.exists(pa):
        import ctypes.util
        system_find = ctypes.util.find_library
        ctypes.util.find_library = lambda name: (system_find(name) or pa) \
            if name == "portaudio" else system_find(name)


_prepare_linux_bundle()

# A beépített lejátszó hangjához a sounddevice kell (Macen és Windowson a csomag hozza a
# hangkezelő könyvtárat, Linuxon a libportaudio2 csomag, a kész programban mellé van csomagolva)
try:
    import sounddevice
    HAS_AUDIO = True
except Exception:
    HAS_AUDIO = False


def mpv_hint():
    if is_mac():
        return t("Telepítés Macen: brew install mpv")
    if is_win():
        return t("Telepítés Windowson: töltsd le az mpv.exe-t (mpv.io), és tedd az app mellé.")
    return t("Telepítés: sudo apt install mpv")


def ffmpeg_hint():
    """Hogyan telepíthető az ffmpeg ezen a rendszeren (hibaüzenetekbe)."""
    if is_mac():
        return t("Telepítés Macen: brew install ffmpeg")
    if is_win():
        return (t("Telepítés Windowson: winget install ffmpeg, vagy tedd az ffmpeg.exe és az "
                "ffprobe.exe fájlt az app mellé."))
    return t("Telepítés Linuxon: sudo apt install ffmpeg (vagy a saját csomagkezelőddel).")


def app_dir():
    """Az app (futtatható fájl vagy forrásfájl) mappája."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def app_data_dir():
    """Ide kerülnek a beállítások, az előzmények és a letöltött yt-dlp frissítés.
    A PHDL_DATA_DIR környezeti változóval felülírható. Windowson a kész (hordozható) program
    az exe melletti "adatok" mappát használja, így USB-ről is vihető."""
    override = os.environ.get("PHDL_DATA_DIR")
    if override:
        return override
    home = os.path.expanduser("~")
    if is_mac():
        base = os.path.join(home, "Library", "Application Support")
        return _migrate_data(os.path.join(base, OLD_APP_NAME), os.path.join(base, APP_NAME))
    if is_win():
        if getattr(sys, "frozen", False):
            return os.path.join(app_dir(), "adatok")
        base = os.environ.get("APPDATA") or home
        return _migrate_data(os.path.join(base, OLD_APP_NAME), os.path.join(base, APP_NAME))
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    return _migrate_data(os.path.join(base, "ph-downloader"), os.path.join(base, "vid-ripper"))


def _migrate_data(old, new):
    """Az átnevezés (PH Downloader -> Vid-Ripper) után a régi beállítások, előzmények és
    bélyegképek átkerülnek az új mappába. A régi mappa megmarad biztonsági másolatnak."""
    try:
        if not os.path.exists(new) and os.path.isdir(old):
            shutil.copytree(old, new)
    except Exception:
        pass
    return new


def saved_language_setting():
    """A beállításokban mentett nyelv ("auto", "hu", "en" vagy "de"). Már az ablak előtt
    kell, mert a szövegek egy része betöltéskor készül el."""
    try:
        with open(os.path.join(app_data_dir(), "settings.json"), encoding="utf-8") as f:
            value = json.load(f).get("language")
    except Exception:
        value = None
    return value if value in LANGUAGES else "auto"


LANGUAGE_SETTING = saved_language_setting()
set_language(system_language() if LANGUAGE_SETTING == "auto" else LANGUAGE_SETTING)

def extra_tool_dirs():
    """Ahol az ffmpeg-et még keressük a PATH mellett. Finderből indítva a Mac nem látja a
    Homebrew-s ffmpeg-et; Windowson az app mellé tett ffmpeg.exe is megtalálható."""
    if is_mac():
        return ["/opt/homebrew/bin", "/usr/local/bin"]
    if is_win():
        base = app_dir()
        return [os.path.join(base, "_internal", "tools"), base,
                os.path.join(base, "ffmpeg"), os.path.join(base, "bin")]
    tools = linux_bundle_dir()
    if tools:  # AppImage: ha a gépen nincs ffmpeg vagy mpv, a mellécsomagolt indul
        return [tools, os.path.join(tools, "linux", "usr", "bin")]
    return []


LOG_MAX_BYTES = 200_000


def log_exc(where, exc_info=None, full=False):
    """Váratlan hiba naplózása (phdl.log az adatmappában). Soha nem dob hibát.
    Alapból a hiba sora és a helye, `full` esetén a teljes (rövidített) hívási lánc,
    hogy egy hibabejelentéshez elég legyen a naplót elküldeni."""
    try:
        import traceback
        path = os.path.join(app_data_dir(), "phdl.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and os.path.getsize(path) > LOG_MAX_BYTES:
            os.replace(path, path + ".old")
        lines = (traceback.format_exception(*exc_info) if exc_info
                 else traceback.format_exc().splitlines(True))
        lines = "".join(lines).strip().splitlines()
        if full:
            keep = lines[-24:]
        else:  # az utolsó hívási hely és maga a hiba
            keep = [ln for ln in lines if ln.lstrip().startswith("File ")][-1:] + lines[-1:]
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {APP_VERSION} {where}: "
                    + "\n    ".join(x.strip() for x in keep) + "\n")
    except Exception:
        pass


def install_error_logging(root):
    """A felület és a háttérszálak váratlan hibái is a naplóba kerülnek (a csomagolt
    Windows appnál nincs konzol, ott enélkül nyomtalanul elvesznének)."""
    def ui_error(exc, val, tb):
        log_exc("felület", (exc, val, tb), full=True)
        try:
            if sys.stderr is not None:
                import traceback
                traceback.print_exception(exc, val, tb)
        except Exception:
            pass
    root.report_callback_exception = ui_error

    def thread_error(args):
        if args.exc_type is SystemExit:
            return
        log_exc(f"szál ({getattr(args.thread, 'name', '?')})",
                (args.exc_type, args.exc_value, args.exc_traceback), full=True)
    threading.excepthook = thread_error


# ---------- yt-dlp: az appból letöltött újabb verzió használata ----------
# Az app a frissítést ide tölti le, indításkor pedig az újabbat használja a beépített
# (vagy telepített) helyett. Így a kész .app-ot sem kell újraépíteni.
YTDLP_LIB_DIR = os.path.join(app_data_dir(), "yt-dlp-lib")


def version_tuple(v):
    return tuple(int(p) for p in re.findall(r"\d+", str(v)))


def is_newer(latest, current):
    try:
        return version_tuple(latest) > version_tuple(current)
    except Exception:
        return False


def read_lib_version(lib_dir):
    """A mappában lévő yt-dlp verziója, vagy None, ha nincs ott használható csomag."""
    try:
        with open(os.path.join(lib_dir, "yt_dlp", "version.py"), encoding="utf-8") as f:
            m = re.search(r"""__version__\s*=\s*['"]([^'"]+)['"]""", f.read())
        return m.group(1) if m else None
    except OSError:
        return None


def _ytdlp_module_names():
    return [k for k in sys.modules if k == "yt_dlp" or k.startswith("yt_dlp.")]


# A letöltött verziók külön almappába kerülnek (yt-dlp-lib/<verzió>/yt_dlp), a current.txt
# mondja meg, melyiket használja az app. Így egy futó app alól sosem cserélődnek ki fájlok.
ACTIVE_LIB_DIR = None


def current_lib(lib_base):
    """A használandó, letöltött yt-dlp mappája, vagy None, ha nincs (épkézláb) letöltés."""
    try:
        with open(os.path.join(lib_base, "current.txt"), encoding="utf-8") as f:
            ver = f.read().strip()
    except OSError:
        return None
    if not ver or ver.startswith(".") or "/" in ver or "\\" in ver:
        return None
    path = os.path.join(lib_base, ver)
    return path if read_lib_version(path) == ver else None


def pick_ytdlp(bundled, lib_base=None):
    """Ha az appból letöltöttünk újabb yt-dlp-t, azt használjuk a beépített helyett.
    Visszaadja: (a használt modul, megjegyzés hiba esetén vagy None)."""
    global ACTIVE_LIB_DIR
    base = lib_base or YTDLP_LIB_DIR
    lib = current_lib(base)
    new_ver = read_lib_version(lib) if lib else None
    try:
        current = bundled.version.__version__
    except Exception:
        current = "0"
    if not new_ver or not is_newer(new_ver, current):
        return bundled, None
    saved_path = list(sys.path)
    saved_mods = {k: sys.modules[k] for k in _ytdlp_module_names()}
    try:
        for k in saved_mods:
            del sys.modules[k]
        sys.path.insert(0, lib)
        new = importlib.import_module("yt_dlp")
        loaded_from = os.path.realpath(getattr(new, "__file__", "") or "")
        if (not loaded_from.startswith(os.path.realpath(lib) + os.sep)
                or new.version.__version__ != new_ver):
            raise ImportError("nem a letöltött yt-dlp töltődött be")
        ACTIVE_LIB_DIR = lib
        return new, None
    except Exception:
        # vissza a beépített verzióra, a hibás letöltést többé nem használjuk
        for k in _ytdlp_module_names():
            del sys.modules[k]
        sys.modules.update(saved_mods)
        sys.path[:] = saved_path
        try:
            os.replace(os.path.join(base, "current.txt"),
                       os.path.join(base, "current.txt.broken"))
        except OSError:
            pass
        return bundled, (t('A letöltött yt-dlp ({new_ver}) nem indult el, ezért a beépített verziót használom.').format(new_ver=new_ver))


import yt_dlp  # noqa: E402

yt_dlp, YTDLP_NOTE = pick_ytdlp(yt_dlp)

try:
    from yt_dlp.version import __version__ as YTDLP_VERSION
except Exception:
    YTDLP_VERSION = t("ismeretlen")

# a rendszerfüggő extra helyek (Homebrew, az app melletti ffmpeg.exe) a PATH végére
for _d in extra_tool_dirs():
    os.environ["PATH"] += os.pathsep + _d

# Böngészőnek álcázás, ha a curl_cffi telepítve van
try:
    import curl_cffi  # noqa: F401
    from yt_dlp.networking.impersonate import ImpersonateTarget
    HAS_IMPERSONATE = True
except Exception:
    HAS_IMPERSONATE = False

# Linkek behúzása egérrel az ablakba (a Tk alapból nem tudja, a tkinterdnd2 hozza;
# ha nincs telepítve, a funkció egyszerűen kimarad)
try:
    import tkinterdnd2
    HAS_DND = True
except Exception:
    HAS_DND = False

# A bélyegkép megjelenítéséhez Pillow kell
try:
    from PIL import Image, ImageDraw, ImageOps, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False

# ---------- témák: PH, YT és VD (rendszer), mindegyik sötét és világos változatban ----------
# Minden szerepnek más a színe egy témán belül, mert váltáskor az érték alapján
# találjuk meg, melyik szerep színét kell kicserélni (lásd retheme).
# a kulcsok a mentett beállításokban vannak, ezért maradnak; a nevek semlegesek
THEME_STYLES = {"VD": t("Alap"), "PH": t("Narancs"), "YT": t("Piros"), "TV": t("Lila")}
THEME_MODES = ["dark", "light", "system"]  # a "system" a rendszer sötét/világos módját követi

# a semleges színek témánként; a kiemelő szín (accent) ezekből számolt szerepei külön jönnek
_NEUTRALS = {
    ("PH", "dark"): dict(
        BG="#1c1c1e", PANEL="#2a2a2d", BORDER="#3d3d41", CONTROL="#38383c",
        CONTROL_HOVER="#47474c", TEXT="#f2f2f4", GREY="#9d9da3", DANGER="#ff6961",
        DISABLED_BG="#313134", DISABLED_FG="#737378", SCROLL="#58585d", CHIP="#35353a",
        SEG_TRACK="#222225", SEG_SEL="#5a5a60", SIDEBAR="#232326"),
    ("PH", "light"): dict(
        BG="#f4f4f6", PANEL="#ffffff", BORDER="#dddde2", CONTROL="#fbfbfc",
        CONTROL_HOVER="#e8e8ed", TEXT="#1d1d1f", GREY="#6e6e73", DANGER="#d70015",
        DISABLED_BG="#e6e6eb", DISABLED_FG="#a3a3a8", SCROLL="#c2c2c7", CHIP="#efeff4",
        SEG_TRACK="#e3e3e9", SEG_SEL="#fdfdfe", SIDEBAR="#ebebef"),
    ("YT", "dark"): dict(
        BG="#0f0f0f", PANEL="#1e1e1e", BORDER="#333333", CONTROL="#272727",
        CONTROL_HOVER="#3a3a3a", TEXT="#f1f1f1", GREY="#aaaaaa", DANGER="#ff4e45",
        DISABLED_BG="#222222", DISABLED_FG="#717171", SCROLL="#4d4d4d", CHIP="#2c2c2c",
        SEG_TRACK="#181818", SEG_SEL="#505050", SIDEBAR="#141414"),
    ("YT", "light"): dict(
        BG="#f9f9f9", PANEL="#ffffff", BORDER="#e5e5e5", CONTROL="#f2f2f2",
        CONTROL_HOVER="#e4e4e6", TEXT="#0f0f0f", GREY="#606060", DANGER="#c00010",
        DISABLED_BG="#ececec", DISABLED_FG="#a0a0a0", SCROLL="#c8c8c8", CHIP="#efefef",
        SEG_TRACK="#e9e9e9", SEG_SEL="#fefefe", SIDEBAR="#f1f1f1"),
    # TV: lila, fekete és fehér
    ("TV", "dark"): dict(
        BG="#0e0e10", PANEL="#18181b", BORDER="#2f2f35", CONTROL="#26262c",
        CONTROL_HOVER="#35353b", TEXT="#efeff1", GREY="#adadb8", DANGER="#ff6b6b",
        DISABLED_BG="#1f1f23", DISABLED_FG="#6e6e78", SCROLL="#45454d", CHIP="#2a2a30",
        SEG_TRACK="#131315", SEG_SEL="#4a4a52", SIDEBAR="#1a1a1e"),
    ("TV", "light"): dict(
        BG="#f7f7f8", PANEL="#ffffff", BORDER="#dedee3", CONTROL="#f2f2f4",
        CONTROL_HOVER="#e6e6ea", TEXT="#0e0e10", GREY="#53535f", DANGER="#d4152e",
        DISABLED_BG="#ececef", DISABLED_FG="#a3a3ad", SCROLL="#c4c4cc", CHIP="#efeff2",
        SEG_TRACK="#e8e8ec", SEG_SEL="#fdfdfe", SIDEBAR="#efeff1"),
    # VD: a rendszerek saját alapszínei (macOS, Windows 11, GNOME/libadwaita)
    ("VD-mac", "dark"): dict(
        BG="#1e1e1e", PANEL="#2c2c2e", BORDER="#414144", CONTROL="#3a3a3c",
        CONTROL_HOVER="#4a4a4d", TEXT="#f5f5f7", GREY="#a1a1a6", DANGER="#ff6961",
        DISABLED_BG="#343437", DISABLED_FG="#76767b", SCROLL="#5a5a5e", CHIP="#3a3a3d",
        SEG_TRACK="#2d2d30", SEG_SEL="#636366", SIDEBAR="#262628"),
    ("VD-mac", "light"): dict(
        BG="#f2f2f7", PANEL="#ffffff", BORDER="#dcdce1", CONTROL="#fcfcfd",
        CONTROL_HOVER="#e9e9ee", TEXT="#1d1d1f", GREY="#6e6e73", DANGER="#d70015",
        DISABLED_BG="#e5e5ea", DISABLED_FG="#a1a1a6", SCROLL="#c1c1c6", CHIP="#f0f0f5",
        SEG_TRACK="#e4e4ea", SEG_SEL="#fdfdfe", SIDEBAR="#e8e8ed"),
    ("VD-win", "dark"): dict(
        BG="#202020", PANEL="#2b2b2b", BORDER="#3b3b3b", CONTROL="#2d2d2d",
        CONTROL_HOVER="#383838", TEXT="#fefefe", GREY="#a6a6a6", DANGER="#ff99a4",
        DISABLED_BG="#262626", DISABLED_FG="#6d6d6d", SCROLL="#5d5d5d", CHIP="#323232",
        SEG_TRACK="#1c1c1c", SEG_SEL="#454545", SIDEBAR="#1b1b1b"),
    ("VD-win", "light"): dict(
        BG="#f3f3f3", PANEL="#fbfbfb", BORDER="#e5e5e5", CONTROL="#fdfdfd",
        CONTROL_HOVER="#efefef", TEXT="#1b1b1b", GREY="#5f5f5f", DANGER="#c42b1c",
        DISABLED_BG="#ebebeb", DISABLED_FG="#a0a0a0", SCROLL="#8a8a8a", CHIP="#f6f6f6",
        SEG_TRACK="#e8e8e8", SEG_SEL="#fffffe", SIDEBAR="#eeeeee"),
    ("VD-linux", "dark"): dict(
        BG="#222226", PANEL="#2e2e32", BORDER="#3f3f44", CONTROL="#38383d",
        CONTROL_HOVER="#45454b", TEXT="#fdfdfd", GREY="#9a9a9f", DANGER="#ff7b63",
        DISABLED_BG="#2a2a2e", DISABLED_FG="#6f6f74", SCROLL="#5c5c61", CHIP="#333338",
        SEG_TRACK="#1d1d20", SEG_SEL="#55555b", SIDEBAR="#29292d"),
    ("VD-linux", "light"): dict(
        BG="#fafafb", PANEL="#ffffff", BORDER="#dedee2", CONTROL="#f6f6f7",
        CONTROL_HOVER="#e8e8eb", TEXT="#323233", GREY="#77767b", DANGER="#c01c28",
        DISABLED_BG="#ececee", DISABLED_FG="#a6a6aa", SCROLL="#c0bfc4", CHIP="#f0f0f2",
        SEG_TRACK="#e6e6e9", SEG_SEL="#fefefe", SIDEBAR="#ebebed"),
}

# a témák kiemelő színe (a VD témánál a rendszer színe felülírja, ha kiolvasható)
_ACCENTS = {
    ("PH", "dark"): "#ff9001", ("PH", "light"): "#e67e00",
    ("YT", "dark"): "#ff0033", ("YT", "light"): "#e5002d",
    ("TV", "dark"): "#9146ff", ("TV", "light"): "#772ce8",
    ("VD-mac", "dark"): "#0a84ff", ("VD-mac", "light"): "#007aff",
    ("VD-win", "dark"): "#4cc2ff", ("VD-win", "light"): "#005fb8",
    ("VD-linux", "dark"): "#3584e4", ("VD-linux", "light"): "#3584e4",
}


def _hex(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _mix(a, b, t):
    """a és b keveréke: t=0 az a, t=1 a b szín."""
    x, y = _hex(a), _hex(b)
    return "#%02x%02x%02x" % tuple(round(x[i] + (y[i] - x[i]) * t) for i in range(3))


def _luma(c):
    r, g, b = (v / 255 for v in _hex(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _make_unique(pal):
    """Minden szerepnek eltérő színkód kell (a témaváltás érték alapján cserél)."""
    seen = set()
    for role in list(pal):
        value = pal[role].lower()
        r, g, b = _hex(value)
        step = 1
        while value in seen:
            b2 = b + step if b + step <= 255 else b - step
            value = "#%02x%02x%02x" % (r, g, max(0, b2))
            step += 1
        seen.add(value)
        pal[role] = value
    return pal


def build_palette(key, mode, accent=None):
    """Egy téma teljes palettája: semleges színek + a kiemelő színből számolt szerepek."""
    dark = mode == "dark"
    pal = dict(_NEUTRALS[(key, mode)])
    acc = (accent or _ACCENTS[(key, mode)]).lower()
    light_text = _luma(acc) < 0.55
    pal["ACCENT"] = acc
    pal["ACCENT_HOVER"] = _mix(acc, "#ffffff", 0.14) if dark else _mix(acc, "#000000", 0.10)
    pal["ACCENT_FG"] = "#ffffff" if light_text else "#1b1b1e"
    pal["ACCENT_TEXT"] = _mix(acc, "#ffffff", 0.25) if dark else _mix(acc, "#000000", 0.12)
    pal["NAV_SEL"] = _mix(pal["SIDEBAR"], acc, 0.22 if dark else 0.16)
    pal["NAV_ACCENT"] = pal["ACCENT_TEXT"]
    order = ["BG", "PANEL", "BORDER", "CONTROL", "CONTROL_HOVER", "ACCENT", "ACCENT_HOVER",
             "ACCENT_FG", "ACCENT_TEXT", "TEXT", "GREY", "DANGER", "DISABLED_BG",
             "DISABLED_FG", "SCROLL", "CHIP", "SEG_TRACK", "SEG_SEL", "SIDEBAR", "NAV_SEL",
             "NAV_ACCENT"]
    return _make_unique({r: pal[r] for r in order})


def vd_key():
    return "VD-mac" if is_mac() else ("VD-win" if is_win() else "VD-linux")


_MAC_ACCENTS = {  # AppleAccentColor értékei -> (sötét, világos)
    "-1": ("#98989d", "#8e8e93"), "0": ("#ff453a", "#ff3b30"), "1": ("#ff9f0a", "#ff9500"),
    "2": ("#ffd60a", "#ffcc00"), "3": ("#32d74b", "#28cd41"), "4": ("#0a84ff", "#007aff"),
    "5": ("#bf5af2", "#af52de"), "6": ("#ff375f", "#ff2d55")}
_GNOME_ACCENTS = {"blue": "#3584e4", "teal": "#2190a4", "green": "#3a944a",
                  "yellow": "#c88800", "orange": "#ed5b00", "red": "#e62d42",
                  "pink": "#d56199", "purple": "#9141ac", "slate": "#6f8396"}


def _run_quiet(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
        return r.returncode, (r.stdout or "").strip()
    except Exception:
        return 1, ""


def system_appearance():
    """A rendszer színbeállítása: ("dark" vagy "light", kiemelő szín vagy None).
    Hiba esetén világos téma és a rendszer alap kiemelő színe."""
    mode, accent = "light", None
    try:
        if is_mac():
            code, out = _run_quiet(["defaults", "read", "-g", "AppleInterfaceStyle"])
            mode = "dark" if code == 0 and "dark" in out.lower() else "light"
            code, out = _run_quiet(["defaults", "read", "-g", "AppleAccentColor"])
            if code == 0 and out in _MAC_ACCENTS:
                accent = _MAC_ACCENTS[out][0 if mode == "dark" else 1]
        elif is_win():
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows"
                                    r"\CurrentVersion\Themes\Personalize") as k:
                    mode = "light" if winreg.QueryValueEx(k, "AppsUseLightTheme")[0] else "dark"
            except OSError:
                pass
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                    r"Software\Microsoft\Windows\DWM") as k:
                    v = int(winreg.QueryValueEx(k, "AccentColor")[0]) & 0xFFFFFF  # ABGR
                    accent = "#%02x%02x%02x" % (v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF)
            except (OSError, ValueError):
                pass
        else:
            code, out = _run_quiet(["gsettings", "get", "org.gnome.desktop.interface",
                                    "color-scheme"])
            if code == 0 and "dark" in out:
                mode = "dark"
            elif code == 0:
                code, theme = _run_quiet(["gsettings", "get", "org.gnome.desktop.interface",
                                          "gtk-theme"])
                mode = "dark" if code == 0 and "dark" in theme.lower() else "light"
            code, out = _run_quiet(["gsettings", "get", "org.gnome.desktop.interface",
                                    "accent-color"])
            if code == 0:
                accent = _GNOME_ACCENTS.get(out.strip("'\""))
    except Exception:
        pass
    return mode, accent


def needs_system(style, mode):
    """Kell-e a rendszer beállítása: a VD a rendszer kiemelő színét használja, a "Rendszer"
    mód pedig a rendszer sötét/világos módját."""
    return style == "VD" or mode == "system"


def theme_palette(style, mode, system=None):
    """A választott téma palettája. Minden témánál választható sötét, világos vagy a
    rendszer szerinti mód; a VD ezen felül a rendszer kiemelő színét is átveszi."""
    if needs_system(style, mode):
        sys_mode, accent = system if system else system_appearance()
    else:
        sys_mode, accent = "dark", None
    real = sys_mode if mode == "system" else (mode if mode in ("dark", "light") else "dark")
    if style == "VD":
        return build_palette(vd_key(), real, accent)
    style = style if style in THEME_STYLES else "PH"
    return build_palette(style, real)


PALETTES = {"dark": build_palette("PH", "dark"), "light": build_palette("PH", "light")}
PAL = dict(PALETTES["dark"])  # a most érvényes paletta


SCROLL_FRAME_MS = 8    # görgetéskor legfeljebb ennyi ms-onként mozdul az oldal (120 Hz-es kijelzőhöz)
SCROLL_WHEEL_PX = 110  # egy görgőkattanás ennyi képpont
SCROLL_TOUCH_FACTOR = 3  # az érintőpad egy egysége ennyi képpont (Tk 9, Mac)
SCROLL_EASE = 0.28     # egérgörgőnél képkockánként a hátralévő út ekkora része
UPDATE_CHECK_INTERVAL_MS = 6 * 3600 * 1000  # 6 óránként újra megnézi az új yt-dlp-t


def col(name):
    """Szerepnév (pl. "ACCENT") vagy kész színkód átváltása a mostani téma színére."""
    return PAL.get(name, name)


def apply_palette(name):
    """A színek átállítása: témanév (dark/light) vagy kész paletta (dict)."""
    PAL.clear()
    PAL.update(name if isinstance(name, dict) else PALETTES.get(name, PALETTES["dark"]))
    globals().update(PAL)


apply_palette("dark")


def hex_rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def blend_hex(front, back, t):
    """Két szín keverése: t=1 esetén a front, t=0 esetén a back színe."""
    f, b = hex_rgb(front), hex_rgb(back)
    mixed = tuple(round(b[i] + (f[i] - b[i]) * t) for i in range(3))
    return "#%02x%02x%02x" % mixed


ANIM_SLOW = 2  # az animációk lassítása: 1 az eredeti sebesség, 2 kétszer lassabb


def fade_in(win, steps=8, delay=16 * ANIM_SLOW):
    """Az ablak áttetszőből fokozatosan átlátszatlanná válik (ahol a rendszer tudja)."""
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        return

    job = {"id": None}

    def step(i=1):
        job["id"] = None
        try:
            win.attributes("-alpha", min(1.0, i / steps))
            if i < steps:
                job["id"] = win.after(delay, step, i + 1)
        except Exception:
            pass

    def stop(event):
        if event.widget is win and job["id"] is not None:
            try:
                win.after_cancel(job["id"])
            except Exception:
                pass
            job["id"] = None

    win.bind("<Destroy>", stop, add="+")
    job["id"] = win.after(delay, step)


THEME_OPTIONS = ("bg", "background", "fg", "foreground", "highlightbackground",
                 "readonlybackground",
                 "highlightcolor", "selectbackground", "selectforeground",
                 "insertbackground", "activebackground", "activeforeground",
                 "disabledforeground", "troughcolor")


def retheme(root, old, new):
    """Minden ablak és elem színének kicserélése a régi palettáról az újra.
    Előbb minden elem régi színét kiolvassuk, csak utána cserélünk, és a saját rajzoló
    elemeket (_retheme) a végén frissítjük. Így egy már átállított szín nem cserélődhet
    újra, ha véletlenül megegyezik a régi téma egy másik színével (ez okozta, hogy a YT és
    a VD téma közti váltásnál összekeveredtek a színek)."""
    table = {}
    for role, value in old.items():
        table.setdefault(value.lower(), new[role])
    widgets, stack = [], [root]
    while stack:
        w = stack.pop()
        widgets.append(w)
        try:
            stack.extend(w.winfo_children())
        except Exception:
            pass
    changes = []
    for w in widgets:
        for opt in THEME_OPTIONS:
            try:
                value = str(w.cget(opt)).lower()
            except Exception:
                continue
            if value in table:
                changes.append((w, opt, table[value]))
    for w, opt, value in changes:
        try:
            w.configure(**{opt: value})
        except Exception:
            pass
    for w in widgets:
        hook = getattr(w, "_retheme", None)
        if hook:
            try:
                hook()
            except Exception:
                pass


RADIUS = 8  # a gombok lekerekítése; témánként más (set_theme_radius), a kártyáké RADIUS + 4
THEME_RADIUS = {"PH": 10, "YT": 5, "TV": 6, "VD-mac": 9, "VD-win": 5, "VD-linux": 9}


def set_theme_radius(style):
    """A téma karakteréhez illő lekerekítés: a PH kerekebb, a YT szögletesebb,
    a VD a rendszer szokását követi (Windows 11 kevésbé kerek, macOS és GNOME kerekebb)."""
    global RADIUS
    RADIUS = THEME_RADIUS.get(vd_key() if style == "VD" else style, 8)

_FONTS = {}


def get_font(size, weight="normal", underline=False, family=None):
    """Közös betűtár: ugyanazt a betűtípus-objektumot nem kell újra és újra létrehozni."""
    root = id(tk._default_root)
    if _FONTS.get("root") != root:  # új főablak (tesztek): a régi betűk érvénytelenek
        _FONTS.clear()
        _FONTS["root"] = root
    key = (family or FONT_FAMILY, size, weight, underline)
    font = _FONTS.get(key)
    if font is None:
        font = _FONTS[key] = tkfont.Font(family=key[0], size=size, weight=weight,
                                         underline=underline)
    return font

BROWSERS = BROWSER_NAMES + ["Nincs"]


def browser_label(name):
    return t("Nincs") if name == "Nincs" else name

AUDIO_LABEL = t("Csak audio (mp3)")
NO_SUB_LABEL = t("Nincs")
BEST_LABEL = t("Legjobb elérhető")  # ha az oldal nem árulja el a videó felbontását
QUALITIES = ["320 kbps", "256 kbps", "192 kbps", "128 kbps"]
DEFAULT_QUALITY = "192 kbps"

PLAYER_GEO_RE = re.compile(r"^\d{2,5}x\d{2,5}[+-]\d{1,5}[+-]\d{1,5}$")  # ablak: SZxMA+X+Y
HISTORY_MAX = 25   # alapértelmezett előzmény-méret
# az előzmények mérete: (mentett érték, felirat); "all" = korlátlan, 0 = nincs előzmény
HISTORY_LIMITS = [(0, t("Nincs")), (25, "25"), (50, "50"), (100, "100"), ("all", t("Korlátlan"))]


def history_cap(value):
    """A beállított értékből a lista maximális hossza (None: nincs korlát)."""
    return None if value == "all" else value
FETCH_STALL_SECONDS = 45
RECENT_MAX = 5
MAX_PARALLEL = 3   # alapból egyszerre ennyi letöltés fut, a többi vár (Beállítások)
PARALLEL_PRESETS = (3, 5, 10)
PARALLEL_CUSTOM_MAX = 50
SPEED_CUSTOM_RANGE = (0.1, 1000.0)  # MB/s
MAX_JOBS = 120     # ennyi nem befejezett letöltés lehet a listában
PLAYLIST_MAX = 100  # egy lejátszási listából legfeljebb ennyi videót listázunk
DEFAULT_GEOMETRY = "860x820"
SIDEBAR_WIDTH = 220  # a bal oldali sáv szélessége
MIN_SIZE = (540 + SIDEBAR_WIDTH, 720)
GEOMETRY_RE = re.compile(r"^(\d+)x(\d+)\+(-?\d+)\+(-?\d+)$")

def entry_kw():
    return dict(bg=PANEL, fg=TEXT, insertbackground=TEXT, relief="flat",
                bd=0, highlightthickness=0, font=(FONT_FAMILY, 13))


# ---------- segédfüggvények (a felülettől függetlenek) ----------
def resource_path(name):
    """Mellé csomagolt fájl útvonala, futtatva és kész appban is."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Lekerekített téglalap rajzolása vászonra."""
    r = max(1, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def explain_error(msg, cookie_browser="Nincs"):
    """Közérthető magyarázat a yt-dlp hibaüzenetéhez.
    Visszaadja: (szöveg, érdemes-e újrapróbálni). A végén a technikai részlet is ott van."""
    low = msg.lower()
    detail = " ".join(str(msg).split())
    if len(detail) > 300:
        detail = detail[:299] + "…"

    def has(*words):
        return any(w in low for w in words)

    retry = True
    if has("operation not permitted") and has("cookies"):
        text = (t("A Safari sütijeihez az appnak Teljes lemezhozzáférés kell "
                "(Rendszerbeállítások → Adatvédelem és biztonság). Egyszerűbb, ha az "
                "Beállítások fülön a 'Nincs' opciót választod."))
        retry = False
    elif has("no space left", "disk full"):
        text = t("Elfogyott a hely a lemezen. Szabadíts fel helyet, vagy válassz másik mappát.")
        retry = False
    elif has("permission denied", "errno 13"):
        text = t("Nincs jogosultságom a kiválasztott mappába írni. Válassz másik mappát.")
        retry = False
    elif has("ffmpeg", "ffprobe") and has("not found", "not installed", "no such file",
                                          "not available", "missing"):
        text = t("Az ffmpeg hiányzik vagy nem működik. ") + ffmpeg_hint()
        retry = False
    elif has("unsupported url"):
        text = (t("Ezt a linket az yt-dlp nem ismeri fel. Ellenőrizd, hogy a videó oldalának "
                "a linkjét másoltad-e be."))
        retry = False
    elif has("live event will begin", "premieres in", "this live event", "is_upcoming",
             "will begin in", "waiting for scheduled stream"):
        text = t("Az élő adás még nem kezdődött el. Próbáld újra, amikor elindul.")
    elif has("requested format is not available"):
        text = (t("Ez a felbontás ehhez a videóhoz nem érhető el. Kérd le újra a videó "
                "adatait, és válassz másikat."))
        retry = False
    elif has("http error 429", "too many requests"):
        text = t("Az oldal túl sok kérést kapott tőlünk (429). Várj pár percet, utána próbáld újra.")
    elif has("http error 410"):
        text = (t("Az oldal 410-es hibát adott: a videó megszűnt, vagy az oldal nem szolgálja ki "
                "az appot. Ha más videóval is ez van, nézd meg a Beállítások fülön, van-e "
                "yt-dlp frissítés."))
    elif has("http error 403", "forbidden"):
        text = (t("Az oldal elutasította a kérést (403). Lehet, hogy az oldal védelme blokkolt, "
                "vagy elavult az yt-dlp: nézd meg a Beállítások fülön, van-e frissítés."))
    elif has("http error 404", "video unavailable", "has been removed", "does not exist",
             "no longer available", "private video"):
        text = t("A videó nem található: lehet, hogy törölték, vagy privát lett.")
    elif has("sign in", "log in", "login required", "members only", "premium"):
        text = (t("A videó megtekintéséhez bejelentkezés kell. A Beállítások fülön kiválaszthatod "
                "a böngészőt, amelyből az app átveszi a sütiket."))
    elif has("http error 500", "http error 502", "http error 503", "http error 504"):
        text = t("Az oldal szervere hibázik. Próbáld meg később.")
    elif has("getaddrinfo", "name resolution", "network is unreachable", "no route to host",
             "connection refused", "connection reset", "connection aborted", "timed out",
             "timeout", "unable to download webpage", "urlopen error", "remote end closed",
             "ssl", "transporterror"):
        text = (t("Nem érem el az oldalt. Ellenőrizd az internetkapcsolatot; ha az működik, "
                "lehet, hogy az oldal éppen nem válaszol."))
    else:
        text = t("Ismeretlen hiba történt.")
    if cookie_browser != "Nincs" and retry and text == t("Ismeretlen hiba történt."):
        text += (t(" A Beállítások fülön a sütik a(z) {cookie_browser} böngészőből jönnek; próbáld meg a 'Nincs' opcióval.").format(cookie_browser=cookie_browser))
    return t('{text}\n\nRészletek: {detail}').format(text=text, detail=detail), retry


def parse_pypi_release(data):
    """A PyPI JSON válaszból a legfrissebb yt-dlp kiadás adatai.
    Ha nincs hozzá letölthető wheel, az url és a sha256 üres marad."""
    release = {"version": data["info"]["version"], "url": None, "sha256": None,
               "size": 0, "filename": None}
    for f in data.get("urls") or []:
        if (f.get("packagetype") == "bdist_wheel"
                and str(f.get("filename", "")).endswith("py3-none-any.whl")
                and str(f.get("url", "")).startswith("https://")
                and (f.get("digests") or {}).get("sha256")):
            release.update(url=f["url"], sha256=f["digests"]["sha256"].lower(),
                           size=f.get("size") or 0, filename=f["filename"])
            break
    return release


# SponsorBlock: a nézők által jelölt részek YouTube videókban (sponsor.ajay.app)
SPONSORBLOCK_API = "https://sponsor.ajay.app"
SB_CATEGORIES = {
    "sponsor": "Szponzor",
    "selfpromo": "Saját reklám",
    "interaction": "Feliratkozás, like kérése",
    "intro": "Bevezető",
    "outro": "Zárás, stáblista",
    "preview": "Előzetes, összefoglaló",
    "filler": "Mellékszál, töltelék",
    "music_offtopic": "Nem zenei rész klipben",
}
SB_DEFAULT = ["sponsor", "selfpromo", "interaction"]
SB_MODES = {"remove": "Kivágás", "fade": "Kivágás áttűnéssel", "mark": "Fejezetként jelölés"}


def is_youtube(info):
    key = str((info or {}).get("extractor_key") or (info or {}).get("extractor") or "")
    return key.lower().startswith("youtube") and bool((info or {}).get("id"))


def fetch_sponsor_segments(video_id):
    """A videó SponsorBlock részei: [(kategória, kezdet, vége), ...]. A kérésben csak a
    videó azonosítójának hash-elejét küldjük el (mint a yt-dlp), hiba esetén üres lista."""
    import hashlib
    from urllib.parse import quote
    prefix = hashlib.sha256(video_id.encode()).hexdigest()[:4]
    cats = json.dumps(list(SB_CATEGORIES))
    url = (f"{SPONSORBLOCK_API}/api/skipSegments/{prefix}?service=YouTube"
           f"&categories={quote(cats)}")
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "socket_timeout": 10}) as ydl:
            data = json.loads(ydl.urlopen(url).read())
    except Exception:
        return []
    out = []
    for video in data if isinstance(data, list) else []:
        if video.get("videoID") != video_id:
            continue
        for seg in video.get("segments") or []:
            try:
                start, end = (float(x) for x in seg["segment"])
            except (KeyError, TypeError, ValueError):
                continue
            if seg.get("category") in SB_CATEGORIES and end > start \
                    and seg.get("actionType", "skip") == "skip":
                out.append((seg["category"], start, end))
    return out


def sponsor_summary(segments, categories):
    """(darab, összes hossz másodpercben) a kiválasztott kategóriákra."""
    picked = [(s, e) for c, s, e in segments if c in categories]
    return len(picked), sum(e - s for s, e in picked)


# ---------- SponsorBlock: kivágás áttűnéssel ----------
# A sima kivágás hirtelen ugrik. Áttűnéssel minden kivágott rész helyén: 1 mp elsötétülés
# (a kivágott rész első másodperce), 1 mp fekete kép felirattal, 1 mp visszatűnés (a kivágott
# rész utolsó másodperce). A videó tartalmából így semmi nem vész el, de az egészet újra
# kell kódolni, ezért lassabb, mint a sima vágás.
SB_FADE_SECONDS = 1.0
SB_CARD_SECONDS = 1.0
SB_CARD_FONTS = (
    "/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/SFNS.ttf",
    "/Library/Fonts/Arial.ttf", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
)
_ENCODERS = None


def ffmpeg_encoders():
    """Az ffmpeg videó- és hangkódolói (egyszer kérdezzük le)."""
    global _ENCODERS
    if _ENCODERS is None:
        _ENCODERS = set()
        exe = shutil.which("ffmpeg")
        if exe:
            try:
                out = subprocess.run([exe, "-hide_banner", "-encoders"], capture_output=True,
                                     text=True, timeout=15).stdout
                _ENCODERS = {line.split()[1] for line in out.splitlines()
                             if len(line.split()) > 1 and line.startswith(" ")}
            except Exception:
                pass
    return _ENCODERS


def merge_cut_ranges(chapters, duration):
    """A SponsorBlock részekből egymást nem fedő (kezdet, vége, kategória) sor."""
    ranges = []
    for ch in chapters or []:
        if ch.get("type", "skip") != "skip":
            continue
        try:
            start, end = max(0.0, float(ch["start_time"])), float(ch["end_time"])
        except (KeyError, TypeError, ValueError):
            continue
        if duration:
            end = min(end, duration)
        if end - start >= 0.2:
            ranges.append([start, end, ch.get("category") or ""])
    ranges.sort()
    merged = []
    for start, end, cat in ranges:
        if merged and start <= merged[-1][1] + 0.5:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end, cat])
    return [tuple(r) for r in merged]


def sb_card_text(category):
    if category == "sponsor":
        return t("Kivágott szponzor tartalom")
    name = SB_CATEGORIES.get(category)
    return t("Kivágott rész: {x}").format(x=t(name)) if name else t("Kivágott rész")


def make_sb_card(path, width, height, text):
    """Fekete kép középen fehér felirattal (Pillow-val, így nem kell az ffmpeg betűkészlete)."""
    from PIL import ImageFont
    img = Image.new("RGB", (width, height), (0, 0, 0))
    size = max(14, height // 20)
    font = None
    for cand in SB_CARD_FONTS:
        if os.path.exists(cand):
            try:
                font = ImageFont.truetype(cand, size)
                break
            except Exception:
                pass
    if font is None:
        try:
            font = ImageFont.load_default(size=size)
        except TypeError:
            font = ImageFont.load_default()
    draw = ImageDraw.Draw(img)
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(((width - w) / 2 - box[0], (height - h) / 2 - box[1]), text, font=font,
              fill=(235, 235, 235))
    img.save(path)


def probe_media(path):
    """Hossz, kép (szélesség, magasság, képkocka/mp, pixelformátum, bitráta) és hang."""
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        res = subprocess.run([exe, "-v", "error", "-show_entries",
                              "stream=codec_type,width,height,avg_frame_rate,r_frame_rate,"
                              "pix_fmt,bit_rate,sample_rate,channels:format=duration,bit_rate",
                              "-of", "json", path], capture_output=True, text=True, timeout=30)
        data = json.loads(res.stdout or "{}")
    except Exception:
        return None
    fmt = data.get("format") or {}
    out = {"duration": float(fmt.get("duration") or 0), "video": None, "audio": None,
           "bit_rate": int(fmt.get("bit_rate") or 0)}
    for st in data.get("streams") or []:
        kind = st.get("codec_type")
        if kind == "video" and out["video"] is None and st.get("width"):
            rate = st.get("avg_frame_rate") or st.get("r_frame_rate") or "30/1"
            try:
                num, den = (float(x) for x in rate.split("/"))
                fps = num / den if den else 30.0
            except ValueError:
                fps = 30.0
            if not 1 <= fps <= 240:
                fps = 30.0
            out["video"] = {"w": int(st["width"]), "h": int(st["height"]), "fps": fps,
                            "pix_fmt": st.get("pix_fmt") or "",
                            "bit_rate": int(st.get("bit_rate") or 0)}
        elif kind == "audio" and out["audio"] is None:
            out["audio"] = {"rate": int(st.get("sample_rate") or 48000)}
    return out


def build_fade_plan(duration, cuts, fade=SB_FADE_SECONDS):
    """Darabok sorrendben: ("clip", kezdet, vége), ("out", k, v), ("card", kategória),
    ("in", k, v). Mellé az időtérkép: [(régi kezdet, régi vége, új kezdet), ...] a
    megmaradt részekre, ebből számoljuk át a fejezeteket."""
    plan, kept = [], []
    pos = 0.0   # a régi idővonalon
    new = 0.0   # az új idővonalon
    for start, end, cat in cuts:
        if start - pos >= 0.05:
            plan.append(("clip", pos, start))
            kept.append((pos, start, new))
            new += start - pos
        f = min(fade, (end - start) / 2)
        if start > 0.05 and f >= 0.1:
            plan.append(("out", start, start + f))
            new += f
        plan.append(("card", cat))
        new += SB_CARD_SECONDS
        if end < duration - 0.05 and f >= 0.1:
            plan.append(("in", end - f, end))
            new += f
        pos = end
    if duration - pos >= 0.05:
        plan.append(("clip", pos, duration))
        kept.append((pos, duration, new))
    return plan, kept


def remap_chapters(chapters, kept, total):
    """Az eredeti fejezetek az új idővonalon. A kivágott részbe eső fejezethatár a
    következő megmaradt rész elejére kerül."""
    def to_new(sec):
        for a, b, off in kept:
            if sec < a:
                return off
            if sec <= b:
                return off + sec - a
        return total
    out = []
    for ch in chapters or []:
        title = ch.get("title") or ""
        if title.startswith("[SponsorBlock]"):
            continue
        try:
            start, end = to_new(float(ch["start_time"])), to_new(float(ch["end_time"]))
        except (KeyError, TypeError, ValueError):
            continue
        if end - start >= 1:
            out.append({"start_time": start, "end_time": end, "title": title})
    return out


def sponsor_fade_cut(path, cuts, kbps=None, progress=None, should_stop=None):
    """Újrakódolja a fájlt a kivágásokkal és az áttűnésekkel. Visszaadja az időtérképet
    és az új hosszt, vagy kivételt dob (ilyenkor marad a sima vágás)."""
    exe = shutil.which("ffmpeg")
    media = probe_media(path)
    if not exe or not media or not media["duration"]:
        raise RuntimeError("ffmpeg/ffprobe")
    video, audio, duration = media["video"], media["audio"], media["duration"]
    if video and (not HAS_PIL or "10" in video["pix_fmt"] or "12" in video["pix_fmt"]):
        raise RuntimeError("HDR")  # HDR-nél a fekete-fehér felirat színei nem lennének jók
    encs = ffmpeg_encoders()
    if video:
        if is_mac() and "h264_videotoolbox" in encs:
            rate = video["bit_rate"] or max(0, media["bit_rate"] - 160_000)
            rate = max(2_000_000, int(rate * 1.4)) if rate else 8_000_000
            vcodec = ["-c:v", "h264_videotoolbox", "-b:v", str(rate), "-allow_sw", "1"]
        elif "libx264" in encs:
            vcodec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]
        else:
            raise RuntimeError("no h264 encoder")
    is_mp3 = path.lower().endswith(".mp3")
    acodec = (["-c:a", "libmp3lame", "-b:a", f"{kbps or 192}k"] if is_mp3
              else ["-c:a", "aac", "-b:a", "192k"])
    plan, kept = build_fade_plan(duration, cuts)
    work = tempfile.mkdtemp(prefix="vr-fade-")
    try:
        args, filters, pads = [exe, "-hide_banner", "-nostdin", "-y"], [], []
        n = 0
        sr = audio["rate"] if audio else 48000
        if video:
            w, h, fps = video["w"] + video["w"] % 2, video["h"] + video["h"] % 2, video["fps"]
            vnorm = f"fps={fps:.5f},scale={w}:{h},setsar=1,format=yuv420p"
        anorm = f"aformat=sample_rates={sr}:channel_layouts=stereo"
        card_files = {}
        for piece in plan:
            kind = piece[0]
            if kind == "card":
                length = SB_CARD_SECONDS
                if video:
                    cat = piece[1]
                    if cat not in card_files:
                        card_files[cat] = os.path.join(work, f"card{len(card_files)}.png")
                        make_sb_card(card_files[cat], w, h, sb_card_text(cat))
                    args += ["-loop", "1", "-framerate", f"{fps:.5f}", "-t", f"{length}",
                             "-i", card_files[cat]]
                    filters.append(f"[{n}:v]{vnorm},fade=t=in:d=0.2,"
                                   f"fade=t=out:st={length - 0.2}:d=0.2[v{len(pads)}]")
                    n += 1
                args += ["-f", "lavfi", "-t", f"{length}", "-i", f"anullsrc=r={sr}:cl=stereo"]
                filters.append(f"[{n}:a]{anorm}[a{len(pads)}]")
                n += 1
            else:
                a, b = piece[1], piece[2]
                length = b - a
                args += ["-ss", f"{a:.3f}", "-t", f"{length:.3f}", "-i", path]
                vf = af = ""
                if kind == "out":
                    vf, af = f",fade=t=out:st=0:d={length:.3f}", f",afade=t=out:st=0:d={length:.3f}"
                elif kind == "in":
                    vf, af = f",fade=t=in:st=0:d={length:.3f}", f",afade=t=in:st=0:d={length:.3f}"
                if video:
                    filters.append(f"[{n}:v]setpts=PTS-STARTPTS,{vnorm}{vf}[v{len(pads)}]")
                if audio:
                    filters.append(f"[{n}:a]asetpts=PTS-STARTPTS,{anorm}{af}[a{len(pads)}]")
                else:
                    filters.append(f"anullsrc=r={sr}:cl=stereo,atrim=0:{length:.3f}[a{len(pads)}]")
                n += 1
            pads.append(length)
        k = len(pads)
        streams = "".join((f"[v{i}]" if video else "") + f"[a{i}]" for i in range(k))
        filters.append(f"{streams}concat=n={k}:v={1 if video else 0}:a=1"
                       + ("[vout]" if video else "") + "[aout]")
        graph = ";".join(filters)
        root, ext = os.path.splitext(path)
        out = root + ".fade" + ext
        if len(graph) < 20000:
            # közvetlenül adjuk át: a régi -filter_complex_script az ffmpeg 8-tól megszűnt
            args += ["-filter_complex", graph]
        else:
            # nagyon sok vágásnál fájlból (Windowson korlátos a parancssor hossza), ffmpeg 7+
            script = os.path.join(work, "filter.txt")
            with open(script, "w", encoding="utf-8") as fh:
                fh.write(graph)
            args += ["-/filter_complex", script]
        if video:
            args += ["-map", "[vout]"] + vcodec
        args += ["-map", "[aout]"] + acodec + ["-map_metadata", "-1", "-map_chapters", "-1"]
        if ext.lower() in (".mp4", ".m4a", ".mov"):
            args += ["-movflags", "+faststart"]
        args += ["-progress", "pipe:1", "-nostats", "-loglevel", "error", out]
        total = sum(pads)
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, errors="replace")
        err_lines = []
        threading.Thread(target=lambda: err_lines.extend(proc.stderr), daemon=True).start()
        for line in proc.stdout:
            if should_stop and should_stop():
                proc.kill()
                break
            if line.startswith("out_time_us=") and progress:
                try:
                    progress(min(99.0, int(line.split("=")[1]) / 1e6 / total * 100))
                except ValueError:
                    pass
        code = proc.wait()
        if code != 0 or not os.path.exists(out):
            try:
                os.remove(out)
            except OSError:
                pass
            raise RuntimeError("ffmpeg: " + "".join(err_lines[-5:]).strip())
        os.replace(out, path)
        return kept, total
    finally:
        shutil.rmtree(work, ignore_errors=True)


class SponsorFadePP(yt_dlp.postprocessor.PostProcessor):
    """yt-dlp utófeldolgozó: a SponsorBlock részek kivágása áttűnéssel. Ha nem sikerül
    (nincs megfelelő kódoló, HDR videó, ffmpeg hiba), a megszokott sima vágás fut le."""

    def __init__(self, downloader=None, categories=(), kbps=None, progress=None,
                 should_stop=None, on_fallback=None):
        super().__init__(downloader)
        self.categories = set(categories)
        self.kbps, self.progress, self.should_stop = kbps, progress, should_stop
        self.on_fallback = on_fallback

    def run(self, info):
        path = info.get("filepath")
        chapters = [c for c in info.get("sponsorblock_chapters") or []
                    if c.get("category") in self.categories]
        cuts = merge_cut_ranges(chapters, info.get("duration"))
        if not path or not cuts:
            return [], info
        try:
            kept, total = sponsor_fade_cut(path, cuts, self.kbps, self.progress,
                                           self.should_stop)
        except Exception as e:
            if self.should_stop and self.should_stop():
                raise DownloadCancelled() from e
            self.report_warning(f"SponsorBlock fade failed, plain cut instead: {e}")
            if self.on_fallback:
                self.on_fallback(str(e))
            from yt_dlp.postprocessor import ModifyChaptersPP
            pp = ModifyChaptersPP(self._downloader, remove_sponsor_segments=self.categories,
                                  sponsorblock_chapter_title="[SponsorBlock]: %(category_names)l")
            return pp.run(info)
        info["chapters"] = remap_chapters(info.get("chapters"), kept, total)
        info["duration"] = total
        return [], info


yt_dlp.postprocessor.postprocessors.value["SponsorFadePP"] = SponsorFadePP


class SafeEmbedThumbnailPP(yt_dlp.postprocessor.EmbedThumbnailPP):
    """Borítókép a fájlba, de ha az ffmpeg nem tudja beletenni (furcsa képformátum vagy
    tároló, egyes oldalaknál mindig), a letöltés nem bukik el: a videó borító nélkül
    elkészül, a kép törlődik."""

    def __init__(self, downloader=None, already_have_thumbnail=False, on_fail=None):
        super().__init__(downloader, already_have_thumbnail)
        self._on_fail = on_fail

    def run(self, info):
        try:
            return super().run(info)
        except yt_dlp.postprocessor.embedthumbnail.EmbedThumbnailPPError as e:
            self.report_warning(f"Borítókép nélkül: {e}")
            if self._on_fail:
                self._on_fail(str(e))
            files = []
            for th in info.get("thumbnails") or []:
                path = th.pop("filepath", None)
                if path and os.path.exists(path) and not self._already_have_thumbnail:
                    files.append(path)
            return files, info


yt_dlp.postprocessor.postprocessors.value["SafeEmbedThumbnailPP"] = SafeEmbedThumbnailPP


def fetch_ytdlp_release():
    """A legfrissebb yt-dlp kiadás adatai a PyPI-ról. Hiba esetén None."""
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            data = json.loads(ydl.urlopen("https://pypi.org/pypi/yt-dlp/json").read())
        return parse_pypi_release(data)
    except Exception:
        return None


def download_ytdlp_wheel(release, progress=None):
    """A wheel letöltése. A fájl sha256 összegének egyeznie kell a PyPI-n megadottal."""
    if not release.get("url") or not release.get("sha256"):
        raise RuntimeError(t("A PyPI nem ad letölthető csomagot ehhez a verzióhoz."))
    buf = io.BytesIO()
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        resp = ydl.urlopen(release["url"])
        try:
            total = int(resp.headers.get("Content-Length") or 0) or release.get("size") or 0
        except (TypeError, ValueError):
            total = release.get("size") or 0
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            buf.write(chunk)
            if progress:
                progress(buf.tell(), total)
    data = buf.getvalue()
    if hashlib.sha256(data).hexdigest() != release["sha256"]:
        raise RuntimeError(t("A letöltött fájl ellenőrző összege nem egyezik a PyPI-n "
                           "megadottal, ezért nem telepítem."))
    return data


def install_ytdlp_wheel(data, lib_base, expected_version):
    """A wheelből csak az yt_dlp mappát csomagolja ki egy új, verziószámos mappába, majd
    átírja a current.txt-t. A futó app által használt mappához nem nyúl, hiba esetén a
    korábbi telepítés érintetlen marad."""
    if (not expected_version or expected_version.startswith(".")
            or "/" in expected_version or "\\" in expected_version):
        raise RuntimeError(t("Érvénytelen verziószám."))
    final = os.path.join(lib_base, expected_version)
    if ACTIVE_LIB_DIR and os.path.realpath(final) == os.path.realpath(ACTIVE_LIB_DIR):
        raise RuntimeError(t("Ez a verzió már használatban van."))
    new_dir = final + ".new"
    shutil.rmtree(new_dir, ignore_errors=True)
    os.makedirs(new_dir)
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            if "yt_dlp/__init__.py" not in names or "yt_dlp/version.py" not in names:
                raise RuntimeError(t("A csomag nem tartalmazza az yt-dlp fájljait."))
            root = os.path.realpath(new_dir) + os.sep
            for info in zf.infolist():
                name = info.filename
                if not name.startswith("yt_dlp/") or name.endswith("/"):
                    continue
                target = os.path.realpath(os.path.join(new_dir, name))
                if not target.startswith(root):
                    raise RuntimeError(t("Gyanús fájlútvonal a csomagban."))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        if read_lib_version(new_dir) != expected_version:
            raise RuntimeError(t("A csomag verziója nem egyezik a várttal."))
        shutil.rmtree(final, ignore_errors=True)
        os.replace(new_dir, final)
        pointer = os.path.join(lib_base, "current.txt")
        with open(pointer + ".tmp", "w", encoding="utf-8") as f:
            f.write(expected_version)
        os.replace(pointer + ".tmp", pointer)
        try:
            os.remove(pointer + ".broken")
        except OSError:
            pass
    except Exception:
        shutil.rmtree(new_dir, ignore_errors=True)
        raise
    # a régi verziók törlése, kivéve a most futó appét
    keep = {expected_version}
    if ACTIVE_LIB_DIR:
        keep.add(os.path.basename(os.path.realpath(ACTIVE_LIB_DIR)))
    for entry in os.listdir(lib_base):
        path = os.path.join(lib_base, entry)
        if os.path.isdir(path) and entry not in keep:
            shutil.rmtree(path, ignore_errors=True)


DONE_SOUND = "/System/Library/Sounds/Glass.aiff"
LINUX_DONE_SOUND = "/usr/share/sounds/freedesktop/stereo/complete.oga"


def play_done_sound(root=None):
    """Rövid hangjelzés a kész letöltésnél: Macen rendszerhang, Windowson a rendszer
    értesítő hangja, Linuxon a szokásos értesítő hang (ha van), különben a rendszer csengője."""
    try:
        if is_mac() and os.path.exists(DONE_SOUND):
            subprocess.Popen(["afplay", DONE_SOUND], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return
        if is_win():
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return
        if not is_mac() and os.path.exists(LINUX_DONE_SOUND) and shutil.which("paplay"):
            subprocess.Popen(["paplay", LINUX_DONE_SOUND], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return
    except Exception:
        log_exc("play_done_sound")
    try:
        if root is not None:
            root.bell()
    except Exception:
        log_exc("play_done_sound bell")


def reveal_path(path):
    """A fájl megmutatása a fájlkezelőben (Finder, Intéző, Linuxon a mappa megnyitása).
    Visszaadja: "file", ha a fájlt megmutatta; "folder", ha a fájl már nincs meg, ezért a
    mappáját nyitotta meg; None, ha egyik sincs meg vagy a megnyitás nem sikerült."""
    folder = os.path.dirname(path)
    if os.path.exists(path):
        kind = "file"
        if is_mac():
            cmd = ["open", "-R", path]
        elif is_win():
            cmd = ["explorer", "/select," + os.path.normpath(path)]
        else:
            cmd = ["xdg-open", folder]  # Linuxon nincs általános "kijelölés": a mappát nyitjuk
    elif os.path.isdir(folder):
        kind = "folder"
        cmd = ["open", folder] if is_mac() else (["explorer", os.path.normpath(folder)]
                                                  if is_win() else ["xdg-open", folder])
    else:
        return None
    try:
        # az Intéző akkor is 1-gyel tér vissza, ha sikerült, ezért ott nem nézzük a kilépési kódot
        subprocess.run(cmd, timeout=10, check=not is_win(), stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        return kind
    except Exception:
        return None


def remove_history_entries(history, indices):
    """Az előzmények listája a megadott sorszámú elemek nélkül (több kijelölt törlése)."""
    drop = set(indices)
    return [e for i, e in enumerate(history) if i not in drop]


def clean_name_part(text):
    """Fájlnévbe nem illő karakterek törlése, szóközök helyett alulvonás."""
    text = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", text or "")
    text = re.sub(r"\s+", "_", text.strip())
    text = re.sub(r"_{2,}", "_", text)
    return text.strip("._")


def upload_date_prefix(info):
    """Feltöltés dátuma éééé_hh_nn formában. Ha nincs adat, a mai dátum."""
    d = str(info.get("upload_date") or info.get("release_date") or "")
    if re.fullmatch(r"\d{8}", d):
        return f"{d[:4]}_{d[4:6]}_{d[6:]}"
    ts = info.get("timestamp") or info.get("release_timestamp")
    if ts:
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y_%m_%d")
        except Exception:
            pass
    return datetime.now().strftime("%Y_%m_%d")


def build_basename(info, height=None, hdr=False):
    """A mentett fájl neve kiterjesztés nélkül: éééé_hh_nn_videó_címe_1080p
    (a felbontás csak videónál kerül bele, hangnál nem)."""
    title = clean_name_part(info.get("title")) or "nevtelen_video"
    base = f"{upload_date_prefix(info)}_{title}"[:150].rstrip("._")
    name = f"{base}_{height}p" if height else base
    return name + "_HDR" if hdr else name


def collect_playlist_entries(info):
    """A lejátszási lista (vagy csatorna) videóinak egyszerű listája:
    [{"url", "title", "uploader", "duration"}, ...]. A fülek, privát és törölt videók kimaradnak."""
    out, seen = [], set()

    def walk(entries, depth):
        for e in entries or []:
            if not isinstance(e, dict):
                continue
            if e.get("entries") is not None and depth < 2:
                walk(e.get("entries"), depth + 1)
                continue
            key = str(e.get("ie_key") or "")
            if key.endswith("Tab") or e.get("_type") == "playlist":
                continue
            url = e.get("url") or e.get("webpage_url")
            if not url and e.get("id") and key.lower() == "youtube":
                url = f"https://www.youtube.com/watch?v={e['id']}"
            if not url or not str(url).startswith(("http://", "https://")) or url in seen:
                continue
            title = str(e.get("title") or "")
            if title in ("[Private video]", "[Deleted video]"):
                continue
            seen.add(url)
            out.append({"url": str(url), "title": title or t("Névtelen videó"),
                        "uploader": str(e.get("uploader") or e.get("channel")
                                        or info.get("uploader") or info.get("channel") or ""),
                        "duration": e.get("duration")})

    walk(info.get("entries"), 0)
    return out[:PLAYLIST_MAX]


def find_videos_tab(info):
    """Csatorna főoldalnál a "Videók" fül linkje, ha a lista csak füleket tartalmaz."""
    for e in info.get("entries") or []:
        if isinstance(e, dict):
            url = str(e.get("url") or "")
            if url.rstrip("/").endswith("/videos"):
                return url
    return None


def format_height(f):
    """Egy formátum magassága. Ha az oldal nem adja meg közvetlenül, a felbontás
    szövegéből (1280x720, 720p) próbáljuk kiolvasni."""
    h = f.get("height")
    if isinstance(h, (int, float)) and h > 0:
        return int(h)
    for key in ("resolution", "format_note", "format_id", "format"):
        m = re.search(r"(\d{3,4})\s*[xX]\s*(\d{3,4})|(\d{3,4})p\b", str(f.get(key) or ""))
        if m:
            return int(m.group(2) or m.group(3))
    return None


def video_heights(info):
    """(felbontások csökkenő sorrendben, van-e egyáltalán letölthető videó)."""
    formats = info.get("formats") or []
    video = [f for f in formats if f.get("vcodec") != "none"
             and not (f.get("acodec") not in (None, "none") and f.get("ext") in ("m4a", "mp3", "opus", "ogg"))]
    heights = sorted({format_height(f) for f in video if format_height(f)}, reverse=True)
    has_video = bool(video) or (not formats and bool(info.get("url")))
    return heights, has_video


def is_hdr_format(f):
    """HDR a videóformátum? (a yt-dlp dynamic_range mezője: HDR10, HLG, HDR10+, DV)"""
    dr = str(f.get("dynamic_range") or "").upper()
    return f.get("vcodec") not in (None, "none") and bool(dr) and dr != "SDR"


def hdr_heights(info):
    """A HDR-ben elérhető felbontások csökkenő sorrendben (üres, ha nincs HDR)."""
    hs = {format_height(f) for f in (info.get("formats") or []) if is_hdr_format(f)}
    return sorted((h for h in hs if h), reverse=True)


def hdr_format_selector(height):
    """yt-dlp formátumválasztó HDR-hez: a kért magasságig a HDR videó, ha nincs, a sima."""
    lim = f"[height<=?{height}]" if height else ""
    return (f"bv*[dynamic_range!=SDR]{lim}+ba"
            f"/bv*{lim}+ba/b{lim}/b")


MEDIA_RE = re.compile(r"https?://[^\"'\s<>\\]+?\.(?:m3u8|mp4)(?:\?[^\"'\s<>\\]*)?", re.I)
IFRAME_RE = re.compile(r"<iframe[^>]+?src=[\"']([^\"']+)[\"']", re.I)
JUNK_WORDS = ("preview", "trailer", "thumb", "sample", "teaser", "poster", "sprite")


def find_media_urls(text):
    """Videófájl linkek (m3u8, mp4) egy oldal kódjából, az elkerült (\\/) alakokat is megtalálja.
    Az előnézeti, mintaklipek a lista végére kerülnek, az m3u8 előre."""
    text = (text.replace("\\/", "/").replace("\\u0026", "&").replace("&amp;", "&")
            .replace("\\u002F", "/"))
    seen, urls = set(), []
    for m in MEDIA_RE.finditer(text):
        u = m.group(0)
        if u not in seen:
            seen.add(u)
            urls.append(u)

    def rank(u):
        junk = any(w in u.lower() for w in JUNK_WORDS)
        hls = ".m3u8" in u.lower()
        return (junk, not hls)
    return sorted(urls, key=rank)


def sniff_media_urls(fetch, page_url, max_pages=6):
    """Az oldal és a benne lévő iframe-ek kódját átnézi videólinkek után.
    fetch(url, referer) a lap szövegét adja vissza (vagy hibát dob)."""
    from urllib.parse import urljoin
    found, queue, done = [], [(page_url, None, 0)], set()
    while queue and len(done) < max_pages:
        url, referer, depth = queue.pop(0)
        if url in done:
            continue
        done.add(url)
        try:
            text = fetch(url, referer)
        except Exception:
            continue
        for u in find_media_urls(text):
            if u not in found:
                found.append(u)
        if depth < 2:
            for src in IFRAME_RE.findall(text)[:4]:
                nxt = urljoin(url, src.replace("&amp;", "&"))
                if nxt.startswith(("http://", "https://")):
                    queue.append((nxt, url, depth + 1))
    return found


def page_title_from_url(url):
    """Tartalék cím, ha sem az oldal, sem a videó nem ad: az URL utolsó értelmes darabja."""
    from urllib.parse import urlparse, unquote
    path = unquote(urlparse(url).path).rstrip("/")
    name = path.rsplit("/", 1)[-1] or urlparse(url).netloc
    name = re.sub(r"\.(html?|php|aspx?)$", "", name)
    return name[:80] or t("Névtelen videó")


def format_duration(seconds):
    if not seconds:
        return t("ismeretlen")
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def parse_timecode(text):
    """Időpont szövegből másodpercbe: "90", "1:30", "1:02:03", "1.30" is jó. Hibásnál None."""
    text = (text or "").strip().replace(".", ":").replace(",", ":")
    if not text:
        return None
    parts = text.split(":")
    if len(parts) > 3 or not all(p.strip().isdigit() for p in parts):
        return None
    nums = [int(p) for p in parts]
    if any(n >= 60 for n in nums[1:]):
        return None
    total = 0
    for n in nums:
        total = total * 60 + n
    return total


def clip_suffix(start, end):
    """A kijelölt rész a fájlnévben: _1m30s-2m45s (órával: _1h02m05s-...)."""
    def part(sec):
        h, rem = divmod(int(sec), 3600)
        m, s = divmod(rem, 60)
        return f"{h}h{m:02d}m{s:02d}s" if h else f"{m}m{s:02d}s"
    return f"_{part(start)}-{part(end)}"


SUB_LANG_NAMES = {
    "hu": t("Magyar"), "en": t("Angol"), "de": t("Német"), "fr": t("Francia"), "es": t("Spanyol"),
    "it": t("Olasz"), "pt": t("Portugál"), "nl": t("Holland"), "pl": t("Lengyel"), "cs": t("Cseh"),
    "sk": t("Szlovák"), "ro": t("Román"), "ru": t("Orosz"), "uk": t("Ukrán"), "hr": t("Horvát"),
    "sr": t("Szerb"), "sv": t("Svéd"), "fi": t("Finn"), "da": t("Dán"), "no": t("Norvég"), "tr": t("Török"),
    "el": t("Görög"), "ja": t("Japán"), "ko": t("Koreai"), "zh": t("Kínai"), "ar": t("Arab"), "hi": t("Hindi"),
}


def _sub_lang_name(code, formats=None):
    base = code.split("-")[0].lower()
    if base in SUB_LANG_NAMES:
        name = SUB_LANG_NAMES[base]
        return name if base == code.lower() else f"{name} ({code})"
    for f in formats or []:
        if isinstance(f, dict) and f.get("name"):
            return str(f["name"])
    return code


def subtitle_choices(info):
    """A videó letölthető feliratai: [(kulcs, felirat), ...]. A kulcs "nyelv" vagy
    "auto:nyelv" (automatikus felirat). Az automatikusból csak az eredeti nyelvű és a
    magyar fordítás kerül a listába, a többi száz nyelv csak zavarna."""
    info = info or {}
    out, seen = [], set()
    subs = info.get("subtitles") or {}
    for code in sorted(subs, key=lambda c: (c.split("-")[0] != "hu", _sub_lang_name(c))):
        if code == "live_chat" or not subs.get(code):
            continue
        out.append((code, _sub_lang_name(code, subs[code])))
        seen.add(code.split("-")[0])
    auto = info.get("automatic_captions") or {}
    orig = [c for c in auto if c.endswith("-orig")]
    picks = [(c, c[:-5]) for c in orig]
    if not picks and info.get("language") in auto:
        picks = [(info["language"], info["language"])]
    if "hu" in auto and all(lang != "hu" for _, lang in picks):
        picks.append(("hu", "hu"))
    for code, lang in picks:
        if lang.split("-")[0] in seen or not auto.get(code):
            continue
        label = _sub_lang_name(lang)
        is_orig = code.endswith("-orig") or code == info.get("language")
        out.append((f"auto:{code}", t('{label} (automatikus)').format(label=label) if is_orig
                    else t('{label} (automatikus fordítás)').format(label=label)))
    return out


def format_size(nbytes, exact):
    mb = nbytes / 1024 / 1024
    if mb >= 1024:
        text = f"{mb / 1024:.2f} GB"
    elif mb >= 100:
        text = f"{mb:.0f} MB"
    else:
        text = f"{mb:.1f} MB"
    return text if exact else "~" + text


def _format_bytes(f, duration):
    """Egy formátum mérete: (bájt, pontos-e). Ha nem ismert: (None, False)."""
    if f.get("filesize"):
        return f["filesize"], True
    if f.get("filesize_approx"):
        return f["filesize_approx"], False
    tbr = f.get("tbr")
    if tbr and duration:
        return tbr * 1000 / 8 * duration, False
    return None, False


def estimate_size(info, height, hdr=False):
    """A letöltés becsült mérete a kiválasztott felbontásnál: (bájt, pontos-e) vagy None."""
    formats = info.get("formats") or []
    duration = info.get("duration")
    videos = [f for f in formats
              if f.get("height") == height and f.get("vcodec") != "none"
              and (not hdr or is_hdr_format(f))]
    if not hdr:  # sima letöltésnél a HDR változatot nem számoljuk, ha van sima is
        sdr = [f for f in videos if not is_hdr_format(f)]
        videos = sdr or videos
    if not videos:
        return None
    video = max(videos, key=lambda f: (f.get("ext") == "mp4", f.get("tbr") or 0))
    size, exact = _format_bytes(video, duration)
    if size is None:
        return None
    if video.get("acodec") == "none":  # külön hangsáv is kell
        audios = [f for f in formats
                  if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none")]
        if audios:
            audio = max(audios, key=lambda f: (f.get("ext") == "m4a",
                                               f.get("abr") or f.get("tbr") or 0))
            a_size, a_exact = _format_bytes(audio, duration)
            if a_size is not None:
                size += a_size
                exact = exact and a_exact
    return size, exact


def estimate_audio_size(info, kbps):
    """Az mp3 becsült mérete bájtban, a hossz és a bitráta alapján. Ha nincs hossz: None."""
    duration = (info or {}).get("duration")
    if not duration:
        return None
    return kbps * 1000 / 8 * duration


# ---------- beállítások és előzmények (a felülettől függetlenek) ----------
SETTINGS_FILE = os.path.join(app_data_dir(), "settings.json")
HISTORY_FILE = os.path.join(app_data_dir(), "history.json")
THUMB_DIR = os.path.join(app_data_dir(), "thumbs")
THUMB_NAME_RE = re.compile(r"^[0-9a-f]{16}\.jpg$")


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        log_exc(f"load_json {os.path.basename(path)}")
        return default


def save_json(path, data):
    """Biztonságos mentés: előbb ideiglenes fájlba ír, majd átnevezi."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
        return True
    except Exception:
        log_exc(f"save_json {os.path.basename(path)}")
        return False


LOCK_ITERS = 200_000          # a jelszó hash-elésének lassítása találgatás ellen
LOCK_MIN_LEN = 4
LOCK_IDLE_MINUTES = 4         # ennyi tétlenség után újra jelszót kér (Olivér kérése, fix)
LOCK_MAX_FAILS = 5            # ennyi hibás próba után rövid várakozás jön
LOCK_WAIT_SECONDS = 30


CHANGELOG = [
    ("5.1.1", [t("Hibajavítások.")]),
    ("5.1", [t("Hibajavítások, az első nyilvános kiadás.")]),
    ("5.0.3", [t("Ablak átméretezéssel kapcsolatos hibák javítása")]),
    ("5.0.2", [t("Bugfixek, előzmények oldal finomhangolása.")]),
    ("5.0.1", [t("Hibák javítása")]),
    ("5.0", [t("Finomhangolások és megújult Előzmények oldal: a futó letöltések és a kész videók egy helyen.")]),
    ("4.8", [t("Finomhangolások, az app ikonjának téma szerinti változtatása és letöltési limitek testreszabhatósága.")]),
    ("4.7", [t("Hibajavítások és dupla kattintásos műveletek hozzáadása")]),
    ("4.6.3", [t("SponsorBlock hibajavítások")]),
    ("4.6.2", [t("Kilépéskor nem jön hibaablak Windowson.")]),
    ("4.6.1", [t("Kijelölt rész letöltése: gyorsabb, látszik a haladás, és a megszakítás is működik.")]),
    ("4.6", [t("SponsorBlock: kivágás áttűnéssel is, így a vágás helyén egy rövid elsötétülés és felirat jelzi, hogy kimaradt valami.")]),
    ("4.5.1", [t("Az Újdonságok ablak mindig előre nyílik, és simább lett a görgetés.")]),
    ("4.5", [
        t("Bugfixek, finomhangolások"),
    ]),
    ("4.4", [
        t("Új Névjegy: rövid bemutatás és a funkciók listája"),
    ]),
    ("4.3", [
        t("Borítókép, cím és előadó kerül a letöltött fájlokba, videónál a fejezetek is (Beállítások)"),
        t("SponsorBlock: YouTube videókban a szponzorált részeket és hasonlókat kivághatod vagy fejezetként jelölheted"),
    ]),
    ("4.2", [
        t("Linkeket az ablakba húzva is elindíthatod a letöltést"),
        t("Ha új yt-dlp érhető el, a letöltő oldalon piros sáv jelzi"),
        t("Az FB-R téma megszűnt, helyette a VD-R lett beállítva"),
    ]),
    ("4.1", [
        t("Élő adások felvétele: az indítástól vagy YouTube-on az adás elejétől, a Leállítás és mentés gombbal bármikor megállítható"),
    ]),
    ("4.0", [
        t("Az app angolul és németül is elérhető. Alapból a rendszer nyelvén indul, a Beállításokban átállítható"),
    ]),
    ("3.7", [
        t("Linuxon egyetlen fájl az egész app: kicsomagolás után dupla kattintással indul, telepítés nélkül. A lejátszó és az ffmpeg is benne van"),
    ]),
    ("3.6", [
        t("Egy videónak elég csak egy részét letölteni: add meg, honnan meddig"),
        t("Ha a videónak van felirata, azt is letöltheted. A felirat a videó mellé kerül, a lejátszó magától betölti"),
    ]),
    ("3.4", [
        t("Az app új neve Vid-Ripper. A beállításaid és az előzményeid megmaradtak"),
        t("Több téma közül választhatsz, mindegyik lehet sötét, világos vagy a rendszerhez igazodó"),
        t("Átláthatóbb Beállítások: a magyarázatok az i ikon mögött vannak"),
    ]),
    ("3.3", [
        t("Letöltés után kis értesítés jelenik meg a sarokban, kattintásra megmutatja a videót az Előzményekben"),
        t("Gyors keresés: Cmd+K (Windowson és Linuxon Ctrl+K), oldalak, beállítások és előzmények egy helyen"),
    ]),
    ("3.0", [
        t("Új felület oldalsávval, a letöltő tetején a Videó kiválasztása és az Aktív letöltések"),
        t("Az elkészült letöltések a listában maradnak, amíg el nem távolítod őket"),
    ]),
    ("2.5", [
        t("Az Előzményekben egyszerre több videót is kijelölhetsz és törölhetsz"),
        t("Windowson a program mappájában csak az indítófájl látszik"),
    ]),
    ("2.3", [
        t("Új lejátszó (mpv): akadás nélkül játszik le nagy felbontásban és teljes képernyőn is"),
        t("A régi beépített lejátszó a Beállításokban továbbra is választható"),
    ]),
    ("2.2", [
        t("HDR letöltés, ha a videónak van HDR változata"),
    ]),
    ("2.0", [
        t("Az app Macen, Windowson és Linuxon is fut"),
    ]),
    ("1.15", [
        t("Beépített lejátszó a letöltött videókhoz és mp3-akhoz, teljes képernyővel és kis ablakos móddal"),
    ]),
    ("1.12", [
        t("NAS-ra is kíméletesen tölt le: a félkész fájlok a gépen készülnek, a célmappába csak a kész videó kerül"),
    ]),
    ("1.11", [
        t("Az Előzmények kereshető, rendezhető és szűrhető, a már letöltött linkre az app figyelmeztet"),
        t("Az Előzmények jelszóval zárolható"),
    ]),
    ("1.0", [
        t("Egyszerre több letöltés, lejátszási listák és csatornák letöltése, mp3 mentés"),
    ]),
]


# A Névjegy ablak szövege: rövid bemutatás és a funkciók fontossági sorrendben
ABOUT_INTRO = t("Videó- és zeneletöltő Macre, Windowsra és Linuxra. Bemásolod a linket, "
                "a többit az app intézi.")
ABOUT_FEATURES = [
    t("Letöltés YouTube-ról és több száz más oldalról, akár 4K-ban és HDR-ben"),
    t("Zene mentése mp3-ba, választható minőségben"),
    t("Lejátszási listák és teljes csatornák letöltése, a kívánt videók kiválasztásával"),
    t("Élő adások felvétele, akár az adás elejétől"),
    t("Egy videónak csak a kiválasztott része is letölthető"),
    t("Feliratok letöltése"),
    t("Szponzorált részek kivágása YouTube videókból (SponsorBlock)"),
    t("Borítókép, cím és fejezetek a letöltött fájlokban"),
    t("Egyszerre több letöltés, várakozási sorral"),
    t("Beépített lejátszó"),
    t("Kereshető, rendezhető előzmények, jelszavas védelemmel"),
    t("Figyelmeztetés a már letöltött linkekre"),
    t("Kíméletes letöltés NAS-ra"),
    t("Gyors keresés egy billentyűparanccsal"),
    t("Négy téma, sötét és világos módban"),
    t("Magyar, angol és német nyelv"),
    t("Beépített yt-dlp frissítés"),
]


def make_lock(password, iters=LOCK_ITERS):
    """A jelszóból sózott hash készül, magát a jelszót sehol sem tároljuk."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
    return {"salt": salt.hex(), "hash": digest.hex(), "iters": iters}


def check_lock(lock, password):
    try:
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                     bytes.fromhex(lock["salt"]), int(lock["iters"]))
        return hmac.compare_digest(digest.hex(), str(lock["hash"]))
    except (KeyError, TypeError, ValueError):
        return False


def valid_lock(lock):
    return (isinstance(lock, dict) and isinstance(lock.get("salt"), str)
            and isinstance(lock.get("hash"), str) and isinstance(lock.get("iters"), int)
            and 1000 <= lock["iters"] <= 5_000_000
            and re.fullmatch(r"[0-9a-f]{32}", lock["salt"])
            and re.fullmatch(r"[0-9a-f]{64}", lock["hash"]))


PLAYER_ENGINES = {"mpv": t("mpv (ajánlott)"), "builtin": t("ffmpeg (kompatibilitás)")}


def sanitize_settings(raw, default_folder):
    """A mentett beállítások ellenőrzése, hibás érték helyett az alapérték marad."""
    out = {"cookie_browser": "Nincs", "folder": default_folder, "geometry": None,
           "recent_folders": [], "theme": "system", "style": "VD",
           "history_lock": None, "notify_popup": True, "notify_sound": True, "toast_anim": "fade",
           "history_limit": HISTORY_MAX, "temp_local": True, "temp_dir": None,
           "seen_version": None, "player_volume": 1.0, "player_engine": "mpv",
           "player_geom_video": None, "player_geom_audio": None, "language": "auto",
           "embed_metadata": True, "sb_mode": "remove", "sb_categories": list(SB_DEFAULT),
           "speed_limit": SPEED_LIMIT_DEFAULT, "speed_limit_on": False,
           "speed_custom": False, "max_parallel": MAX_PARALLEL, "parallel_custom": False}
    if not isinstance(raw, dict):
        return out
    recent = raw.get("recent_folders")
    if isinstance(recent, list):
        out["recent_folders"] = [f for f in recent if isinstance(f, str) and f][:RECENT_MAX]
    # a régi "browser" kulcsot szándékosan nem vesszük át: abban még a régi,
    # automatikusan mentett "safari" lehet, az újnál az alapérték a "Nincs"
    if raw.get("cookie_browser") in BROWSERS:
        out["cookie_browser"] = raw["cookie_browser"]
    if isinstance(raw.get("embed_metadata"), bool):
        out["embed_metadata"] = raw["embed_metadata"]
    lim = raw.get("speed_limit")
    if isinstance(lim, (int, float)) and not isinstance(lim, bool) \
            and SPEED_CUSTOM_RANGE[0] <= lim <= SPEED_CUSTOM_RANGE[1]:
        out["speed_limit"] = lim
    par = raw.get("max_parallel")
    if isinstance(par, int) and not isinstance(par, bool) and 0 <= par <= PARALLEL_CUSTOM_MAX:
        out["max_parallel"] = par  # 0: korlátlan
    if raw.get("parallel_custom") is True:
        out["parallel_custom"] = True
    if raw.get("speed_custom") is True:
        out["speed_custom"] = True
    if isinstance(raw.get("speed_limit_on"), bool):
        out["speed_limit_on"] = raw["speed_limit_on"]
    if raw.get("sb_mode") in SB_MODES:
        out["sb_mode"] = raw["sb_mode"]
    if isinstance(raw.get("sb_categories"), list):
        out["sb_categories"] = [c for c in raw["sb_categories"] if c in SB_CATEGORIES]
    if raw.get("language") in LANGUAGES or raw.get("language") == "auto":
        out["language"] = raw["language"]
    if raw.get("theme") in THEME_MODES:
        out["theme"] = raw["theme"]
    if raw.get("style") in THEME_STYLES:
        out["style"] = raw["style"]
    elif raw.get("incognito") is True:  # a régi inkognitó mód helyett a YT téma
        out["style"] = "YT"
    for key in ("notify_popup", "notify_sound"):
        if raw.get(key) is False:
            out[key] = False
    if raw.get("toast_anim") in TOAST_ANIMS:
        out["toast_anim"] = raw["toast_anim"]
    if valid_lock(raw.get("history_lock")):
        out["history_lock"] = {k: raw["history_lock"][k] for k in ("salt", "hash", "iters")}
    if isinstance(raw.get("temp_dir"), str) and raw["temp_dir"].strip():
        out["temp_dir"] = raw["temp_dir"]  # a mappa hiánya használatkor derül ki, nem törlünk
    for key in ("player_geom_video", "player_geom_audio"):
        geo = raw.get(key)
        if isinstance(geo, str) and PLAYER_GEO_RE.match(geo):
            out[key] = geo
    if isinstance(raw.get("player_engine"), str) and raw["player_engine"] in PLAYER_ENGINES:
        out["player_engine"] = raw["player_engine"]
    vol = raw.get("player_volume")
    if isinstance(vol, (int, float)) and not isinstance(vol, bool) and 0 <= vol <= 1:
        out["player_volume"] = float(vol)
    if isinstance(raw.get("seen_version"), str) and raw["seen_version"]:
        out["seen_version"] = raw["seen_version"][:20]
    if raw.get("temp_local") is False:
        out["temp_local"] = False
    if raw.get("history_limit") in [v for v, _ in HISTORY_LIMITS] \
            and not isinstance(raw.get("history_limit"), bool):
        out["history_limit"] = raw["history_limit"]
    folder = raw.get("folder")
    if isinstance(folder, str) and os.path.isdir(folder):
        out["folder"] = folder
    geometry = raw.get("geometry")
    if isinstance(geometry, str):
        m = GEOMETRY_RE.match(geometry)
        if m:
            w, h, x, y = (int(v) for v in m.groups())
            # a képernyőn kívülre került ablakot nem állítjuk vissza
            if (MIN_SIZE[0] <= w <= 4000 and MIN_SIZE[1] <= h <= 3000
                    and -w + 100 < x < 8000 and 0 <= y < 5000):
                out["geometry"] = geometry
    return out


def add_recent_folder(recent, folder, limit=None):
    """A most használt mappa kerül előre, ismétlődés nélkül, legfeljebb 5 darab."""
    limit = limit or RECENT_MAX
    folder = os.path.normpath(folder)
    return ([folder] + [f for f in recent if os.path.normpath(f) != folder])[:limit]


def clean_history(raw, limit=HISTORY_MAX):
    if not isinstance(raw, list):
        return []
    items = [h for h in raw if isinstance(h, dict)
             and isinstance(h.get("name"), str) and isinstance(h.get("path"), str)]
    for h in items:
        if not (isinstance(h.get("thumb"), str) and THUMB_NAME_RE.match(h["thumb"])):
            h.pop("thumb", None)
    return items if limit is None else items[:limit]


def save_thumb(data, thumb_dir=None):
    """A bélyegkép kis JPEG másolatának mentése az előzményekhez. Fájlnév vagy None."""
    if not (HAS_PIL and data):
        return None
    thumb_dir = thumb_dir or THUMB_DIR
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((320, 180))
        name = hashlib.sha1(data).hexdigest()[:16] + ".jpg"
        os.makedirs(thumb_dir, exist_ok=True)
        img.save(os.path.join(thumb_dir, name), "JPEG", quality=82)
        return name
    except Exception:
        return None


def thumb_file(entry, thumb_dir=None):
    """Az előzmény-bejegyzés bélyegképének útvonala, ha van és létezik."""
    name = entry.get("thumb")
    if not (isinstance(name, str) and THUMB_NAME_RE.match(name)):
        return None
    path = os.path.join(thumb_dir or THUMB_DIR, name)
    return path if os.path.isfile(path) else None


def prune_thumbs(history, thumb_dir=None):
    """Törli azokat a bélyegképeket, amelyekre már nem hivatkozik előzmény."""
    thumb_dir = thumb_dir or THUMB_DIR
    keep = {h.get("thumb") for h in history}
    try:
        for name in os.listdir(thumb_dir):
            if THUMB_NAME_RE.match(name) and name not in keep:
                try:
                    os.remove(os.path.join(thumb_dir, name))
                except OSError:
                    pass
    except OSError:
        pass


def add_history_entry(history, entry, limit=HISTORY_MAX):
    """Az új letöltés kerül előre. Ugyanarra a fájlra csak egy bejegyzés marad."""
    rest = [h for h in history if h.get("path") != entry.get("path")]
    items = [entry] + rest
    return items if limit is None else items[:limit]


def history_label(entry):
    """Az előzmények listában látszó szöveg: "Feltöltő neve - fájlnév"."""
    uploader = " ".join(str(entry.get("uploader") or "").split()) or t("ismeretlen")
    return f"{uploader} - {entry['name']}"


DATE_FORMATS = {"hu": "%Y.%m.%d %H:%M", "en": "%Y-%m-%d %H:%M", "de": "%d.%m.%Y %H:%M"}


def format_history_date(iso):
    try:
        return datetime.fromisoformat(iso).strftime(DATE_FORMATS.get(LANG, "%Y.%m.%d %H:%M"))
    except Exception:
        return t("ismeretlen")


HU_MONTHS = ["január", "február", "március", "április", "május", "június", "július",
             "augusztus", "szeptember", "október", "november", "december"]


def _fold(text):
    """Kisbetűs, ékezet nélküli szöveg a kereséshez (a "ő" és az "o" egyformának számít)."""
    import unicodedata
    text = unicodedata.normalize("NFKD", str(text).casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def history_search_text(entry):
    """Minden, amire az előzményekben rá lehet keresni: feltöltő, cím (fájlnév), a letöltés
    dátuma többféle írásmóddal, a weboldal neve és a link."""
    parts = [entry.get("uploader") or "", entry.get("name") or "", entry.get("url") or ""]
    try:
        from urllib.parse import urlparse
        host = (urlparse(entry.get("url") or "").hostname or "").lower()
        if host.startswith("www."):
            host = host[4:]
        if host:
            parts.append(host)
            labels = host.split(".")
            if len(labels) >= 2:
                parts.append(labels[-2])  # pl. "youtube" a "youtube.com"-ból
    except ValueError:
        pass
    try:
        d = datetime.fromisoformat(entry.get("date") or "")
        parts += [d.strftime("%Y-%m-%d"), d.strftime("%Y.%m.%d"), d.strftime("%Y/%m/%d"),
                  d.strftime("%Y. %m. %d."), d.strftime("%Y.%m.%d."), d.strftime("%d.%m.%Y"),
                  HU_MONTHS[d.month - 1], t(HU_MONTHS[d.month - 1]), str(d.year)]
    except (TypeError, ValueError):
        pass
    return _fold(" ".join(parts))


def history_matches(entry, query):
    """Igaz, ha a keresőszöveg minden szava szerepel a bejegyzés adataiban."""
    words = _fold(query).split()
    if not words:
        return True
    text = history_search_text(entry)
    return all(w in text for w in words)


AUDIO_EXTS = (".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg", ".opus")
HIST_SORTS = [("date", t("Dátum (újabb elöl)")), ("name", t("Név (A-tól Z-ig)")),
              ("size", t("Méret (nagyobb elöl)"))]
HIST_FILTERS = [("all", t("Minden")), ("video", t("Csak videó")), ("audio", t("Csak mp3 (hang)"))]


def entry_kind(entry):
    """"audio" a hanganyagnak (mp3 stb.), különben "video"."""
    return "audio" if str(entry.get("path") or entry.get("name") or "").lower().endswith(
        AUDIO_EXTS) else "video"


def history_view(history, query="", sort="date", kind="all"):
    """A látszó sorok indexei: szűrve (keresés, típus) és rendezve."""
    idx = [i for i, e in enumerate(history)
           if history_matches(e, query) and (kind == "all" or entry_kind(e) == kind)]
    if sort == "name":
        idx.sort(key=lambda i: _fold(history[i].get("name") or ""))
    elif sort == "size":
        idx.sort(key=lambda i: -(history[i].get("size") or 0))
    else:
        idx.sort(key=lambda i: str(history[i].get("date") or ""), reverse=True)
    return idx


HIST_PROBE_MAX = 60    # egy körben legfeljebb ennyi régi videó hosszát pótoljuk
HIST_CHUNK = 8         # ennyi kártya épül egyszerre (a többi apránként, a háttérben)
HIST_PAGE = 100        # ennyi kártya látszik egyszerre az Előzményekben ("Továbbiak" gomb)
THUMB_BIG = (224, 126)     # az Előzmények kártyáinak bélyegképe


def ok_color():
    """Zöld a "kész" jelzéshez, a sötét vagy világos témához illően."""
    return "#30d158" if sum(hex_rgb(PAL.get("BG", "#000000"))) < 384 else "#248a3d"


def site_label(url):
    """A weboldal rövid neve a linkből (pl. YouTube, Twitch), vagy üres szöveg."""
    try:
        from urllib.parse import urlparse
        host = (urlparse(url or "").hostname or "").lower()
    except ValueError:
        return ""
    if host.startswith("www.") or host.startswith("m."):
        host = host.split(".", 1)[1]
    known = {"youtube.com": "YouTube", "youtu.be": "YouTube", "twitch.tv": "Twitch",
             "vimeo.com": "Vimeo", "facebook.com": "Facebook", "instagram.com": "Instagram",
             "tiktok.com": "TikTok", "x.com": "X", "twitter.com": "X",
             "soundcloud.com": "SoundCloud", "dailymotion.com": "Dailymotion"}
    if host in known:
        return known[host]
    labels = host.split(".")
    return labels[-2].capitalize() if len(labels) >= 2 else host


def copyable_text(parent, value, fg=None, font=None, on_click=None):
    """Feliratnak látszó, de egérrel kijelölhető és másolható szöveg (csak olvasható mező).
    `on_click`: sima kattintásra ez fut (pl. link megnyitása); húzással ettől még kijelölhető."""
    var = tk.StringVar(value=value)
    entry = tk.Entry(parent, textvariable=var, state="readonly", readonlybackground=PANEL,
                     fg=fg or TEXT, relief="flat", bd=0, highlightthickness=0,
                     selectbackground=ACCENT, selectforeground=ACCENT_FG,
                     font=font or get_font(12), cursor="hand2" if on_click else "xterm")
    entry.var = var  # a változót tartani kell
    add_context_menu(entry)
    if on_click:
        def released(_e):
            if not entry.selection_present():  # nem kijelölés volt, hanem kattintás
                on_click()
        entry.bind("<ButtonRelease-1>", released, add="+")
    return entry


def entry_upload_date(entry):
    """Az eredeti feltöltés dátuma szövegként: a mentett adatból, vagy a fájlnév elejéről
    (a fájlnév ééé_hh_nn_ kezdetű)."""
    raw = str(entry.get("upload_date") or "")
    m = re.match(r"(\d{4})(\d{2})(\d{2})$", raw) or \
        re.match(r"(\d{4})_(\d{2})_(\d{2})_", os.path.basename(entry.get("name") or ""))
    if not m:
        return ""
    y, mo, d = m.groups()
    if LANG == "de":
        return f"{d}.{mo}.{y}"
    if LANG == "en":
        return f"{y}-{mo}-{d}"
    return f"{y}.{mo}.{d}."


def extract_links(text):
    """A szövegben talált http(s) linkek sorrendben, ismétlés nélkül."""
    out = []
    for m in re.findall(r"https?://[^\s<>\"']+", text or ""):
        if m not in out:
            out.append(m)
    return out


def norm_url(url):
    """Összehasonlításhoz: kisbetűs gép, a # utáni rész és a záró / nélkül."""
    from urllib.parse import urldefrag, urlsplit
    url = urldefrag(str(url or "").strip())[0].rstrip("/")
    parts = urlsplit(url)
    return url.replace(parts.netloc, parts.netloc.lower(), 1) if parts.netloc else url


def find_downloaded(history, url, missing=()):
    """A korábbi letöltés ehhez a linkhez, ha van és a fájlja még megvan."""
    key = norm_url(url)
    for e in history:
        if e.get("url") and norm_url(e["url"]) == key and e.get("path") not in missing:
            return e
    return None


class DownloadJob:
    """Egy letöltés a sorban: adatai, állapota és a hozzá tartozó felületi elemek."""
    _counter = 0

    def __init__(self, url, height, folder, basename, audio, kbps, uploader, thumb, extra_opts, hdr=False):
        DownloadJob._counter += 1
        self.hdr = bool(hdr) and not audio
        self.id = DownloadJob._counter
        self.url, self.height, self.folder = url, height, folder
        self.basename, self.audio, self.kbps = basename, audio, kbps
        self.uploader, self.thumb, self.extra_opts = uploader, thumb, extra_opts
        self.state = "waiting"  # waiting, active, done, error, cancelled
        self.cancel_event = threading.Event()
        self.can_cancel = True
        self.pct = 0
        self.text = t("Várakozik")
        self.path = None
        self.ui = None
        self.retry_ok = True
        self.failed_counted = False
        self.source_url = url  # az eredeti oldal linkje (a letöltés lehet közvetlen videólinkről)
        self.title = ""   # a videó eredeti címe (az értesítéshez és az előzményhez)
        self.entry = None  # az előzmény-bejegyzés, ha kész
        self.lazy = False  # lejátszási listás videó: az adatait csak indításkor kérjük le
        self.clip = None   # (kezdet, vége) másodpercben, ha csak egy részt töltünk le
        self.sub = None    # a letöltendő felirat kulcsa ("en" vagy "auto:en-orig")
        self.live = False             # élő adás felvétele
        self.live_from_start = False  # az adás elejétől (csak YouTube)
        self.live_started = None      # mikor indult a felvétel (time.monotonic)
        self.stop_event = threading.Event()  # Leállítás és mentés
        self.thread_id = None
        self.work_dir = None          # ahol a félkész fájlok vannak
        self.sponsorblock = None      # (mód, kategóriák), ha a SponsorBlock be van kapcsolva
        self.embed_meta = True        # borító, cím, előadó, fejezetek a fájlba

    @property
    def ext(self):
        return ".mp3" if self.audio else (".mkv" if self.hdr else ".mp4")

    @property
    def name(self):
        return self.basename + self.ext

    @property
    def unfinished(self):
        return self.state in ("waiting", "active")


def live_state(info):
    """"live" ha az adás most megy, "upcoming" ha még nem kezdődött el, egyébként None."""
    info = info or {}
    status = info.get("live_status")
    if info.get("is_live") or status == "is_live":
        return "live"
    if status == "is_upcoming":
        return "upcoming"
    return None


def can_record_from_start(info):
    """Az adás elejétől csak YouTube-on lehet felvenni (a yt-dlp csak ott tudja)."""
    key = str((info or {}).get("extractor_key") or (info or {}).get("extractor") or "")
    return key.lower().startswith("youtube")


# Élő adásnál a yt-dlp az ffmpeg-et indítja, és megvárja, amíg az kilép. A leállításhoz
# kell az ffmpeg folyamat: egy "q" betűre rendesen lezárja a fájlt, és a yt-dlp a felvett
# részt kész videónak tekinti. Ezért a yt-dlp ffmpeg-indítását figyeljük, szálanként.
_LIVE_PROCS = {}
_LIVE_LOCK = threading.Lock()

# ---------- sebességkorlát ----------
# A korlát az összes letöltésre együtt vonatkozik, futás közben is átállítható. A yt-dlp
# saját korlátja (ratelimit) induláskor rögzül, és darabolt letöltésnél (HLS, DASH) nem is
# frissíthető, ezért a letöltő lassító függvényét cseréljük: letöltésenként egy közös
# "mikor jöhet a következő bájt" időpont, a közös keretet a futó letöltések között osztjuk el.
SPEED_LIMITS_MB = (1, 2, 5, 10, 20, 50)   # a lista; egyéni érték is megadható
SPEED_LIMIT_DEFAULT = 5
_SPEED = {"total": None, "active": lambda: 1}   # total: bájt/mp, vagy None (nincs korlát)
_SPEED_LOCK = threading.Lock()


def set_speed_limit(bytes_per_sec, active_count=None):
    _SPEED["total"] = bytes_per_sec or None
    if active_count is not None:
        _SPEED["active"] = active_count


def _job_rate(job):
    total = _SPEED["total"]
    if not total:
        return None
    try:
        n = max(1, _SPEED["active"]())
    except Exception:
        n = 1
    return total / n


def fmt_mb(value):
    """5 -> "5", 2.5 -> "2,5" (magyarul vesszővel), angolul ponttal."""
    value = float(value)
    txt = str(int(value)) if value.is_integer() else f"{value:g}"
    return txt.replace(".", ",") if LANG in ("hu", "de") else txt


def parse_number(text):
    """Szám a mezőből: vessző is lehet tizedesjel, a mértékegység elhagyható."""
    try:
        return float(str(text).strip().lower().replace("mb/s", "").replace(",", ".").strip())
    except ValueError:
        return None


def install_speed_limit():
    from yt_dlp.downloader.common import FileDownloader
    if getattr(FileDownloader, "_vr_speed", False):
        return
    orig_slow, orig_block = FileDownloader.slow_down, FileDownloader.best_block_size

    def slow_down(self, start_time, now, byte_counter):
        job = self.params.get("_vr_job")
        if job is None:
            return orig_slow(self, start_time, now, byte_counter)
        prev = getattr(self, "_vr_prev", None)
        delta = byte_counter - prev if prev is not None and byte_counter >= prev \
            else byte_counter
        self._vr_prev = byte_counter
        rate = _job_rate(job)
        if not rate or delta <= 0:
            job.rl_next = None
            return
        with _SPEED_LOCK:
            now_m = time.monotonic()
            start = max(getattr(job, "rl_next", None) or now_m, now_m - 0.5)
            job.rl_next = start + delta / rate
            wait = job.rl_next - now_m
        while wait > 0 and not job.cancel_event.is_set() and _job_rate(job):
            time.sleep(min(wait, 0.1))
            wait = job.rl_next - time.monotonic()

    @staticmethod
    def best_block_size(elapsed_time, bytes):
        size = orig_block(elapsed_time, bytes)
        # korlátnál kisebb darabokban olvasunk, így egyenletes a sebesség, nem lökésszerű
        return min(size, 128 * 1024) if _SPEED["total"] else size

    FileDownloader.slow_down = slow_down
    FileDownloader.best_block_size = best_block_size
    FileDownloader._vr_speed = True


# ---------- témához illő app ikon ----------
# Az alap ikon (icon.png): fekete négyzet, fehér VID, narancs RIP. A többi téma változata
# ebből készül futás közben (a betűk maszkként), így nem kell külön ikonfájl.
THEME_ICON_COLORS = {
    # (háttér, VID, RIP, a RIP mögötti sáv vagy None); mind az alap ikon elrendezése,
    # csak a RIP színe követi a témát
    "VD": None,
    "PH": ("#1d1d1f", "#ffffff", "#ff9001", None),
    "YT": ("#1d1d1f", "#ffffff", "#ff3347", None),
    "TV": ("#1d1d1f", "#ffffff", "#a370ff", None),
}
_ICON_CACHE = {}


def theme_icon(style, base_path):
    """A témához illő ikon Pillow képként (RGBA), vagy None."""
    if style in _ICON_CACHE:
        return _ICON_CACHE[style]
    from PIL import ImageChops
    src = Image.open(base_path).convert("RGBA")
    colors = THEME_ICON_COLORS.get(style)
    if not colors:
        _ICON_CACHE[style] = src
        return src
    bg_c, vid_c, rip_c, pill_c = colors
    r, g, b, alpha = src.split()
    dark = 0x1d  # az alap ikon hátterének fényessége
    scale = 255 / (255 - dark)
    rip = ImageChops.subtract(r, b).point(lambda v: min(255, int(v * scale)))
    low = ImageChops.darker(ImageChops.darker(r, g), b)
    vid = ImageChops.multiply(low.point(lambda v: max(0, min(255, int((v - dark) * scale)))),
                              ImageChops.invert(rip))
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    out.paste(Image.new("RGBA", src.size, bg_c), (0, 0), alpha)
    if pill_c:
        box = rip.point(lambda v: 255 if v > 128 else 0).getbbox()
        if box:
            k = src.size[0] / 1024
            x0, y0, x1, y1 = box
            ImageDraw.Draw(out).rounded_rectangle(
                (x0 - 34 * k, y0 - 26 * k, x1 + 34 * k, y1 + 26 * k), radius=36 * k, fill=pill_c)
    out.paste(Image.new("RGBA", src.size, vid_c), (0, 0), vid)
    out.paste(Image.new("RGBA", src.size, rip_c), (0, 0), rip)
    _ICON_CACHE[style] = out
    return out


def mac_set_dock_icon(png_path):
    """Macen a Dock ikon közvetlenül az AppKit-en át (NSApp setApplicationIconImage:).
    A Tk iconphoto-ja induláskor néha későn vagy egyáltalán nem hatott, ez kiszámítható."""
    import ctypes
    import ctypes.util
    objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
    ctypes.cdll.LoadLibrary("/System/Library/Frameworks/AppKit.framework/AppKit")
    objc.objc_getClass.restype = ctypes.c_void_p
    objc.objc_getClass.argtypes = [ctypes.c_char_p]
    objc.sel_registerName.restype = ctypes.c_void_p
    objc.sel_registerName.argtypes = [ctypes.c_char_p]
    addr = ctypes.cast(objc.objc_msgSend, ctypes.c_void_p).value
    send0 = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(addr)
    send1 = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p)(addr)
    send_str = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                ctypes.c_char_p)(addr)

    def cls(name):
        return objc.objc_getClass(name.encode())

    def sel(name):
        return objc.sel_registerName(name.encode())
    path = send_str(cls("NSString"), sel("stringWithUTF8String:"), png_path.encode("utf-8"))
    img = send1(send0(cls("NSImage"), sel("alloc")), sel("initWithContentsOfFile:"), path)
    if not img:
        raise RuntimeError("NSImage")
    app = send0(cls("NSApplication"), sel("sharedApplication"))
    send1(app, sel("setApplicationIconImage:"), img)


def install_live_tracking():
    try:
        from yt_dlp.downloader import external as ext
    except Exception:
        return
    base = ext.Popen
    if getattr(base, "_vr_tracked", False):
        return

    class TrackedPopen(base):
        _vr_tracked = True

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            with _LIVE_LOCK:
                _LIVE_PROCS.setdefault(threading.get_ident(), []).append(self)

        def __exit__(self, *exc):
            try:
                return super().__exit__(*exc)
            finally:
                with _LIVE_LOCK:
                    procs = _LIVE_PROCS.get(threading.get_ident(), [])
                    if self in procs:
                        procs.remove(self)

    ext.Popen = TrackedPopen


def live_elapsed(job):
    """A felvétel eddigi ideje szövegként (0:00-tól)."""
    secs = int(time.monotonic() - (job.live_started or time.monotonic()))
    h, rem = divmod(max(0, secs), 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def live_len(seconds):
    """Hossz szövegként: 45 mp, 1:45, 1:02:03."""
    secs = int(round(seconds))
    if secs < 60:
        return t("{n} mp").format(n=secs)
    h, rem = divmod(secs, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def live_procs(thread_id):
    with _LIVE_LOCK:
        return [p for p in _LIVE_PROCS.get(thread_id, []) if p.poll() is None]


def kill_procs(procs):
    for proc in procs:
        try:
            proc.kill()
        except Exception:
            pass


def kill_all_tracked():
    """Kilépéskor: a yt-dlp által indított ffmpeg folyamatok ne fussanak tovább a háttérben."""
    with _LIVE_LOCK:
        procs = [p for lst in _LIVE_PROCS.values() for p in lst if p.poll() is None]
    kill_procs(procs)


# Kijelölt rész: a pontos vágáshoz a yt-dlp újrakódol. Az ffmpeg alapbeállítása (libx264
# "medium") nagyon lassú és minden magot leterhel; helyette gyors, jó minőségű beállítás.
CLIP_VIDEO_BITRATE = ((2160, "35M"), (1440, "18M"), (1080, "10M"), (720, "6M"), (0, "4M"))


def clip_encode_args(height, progress_file):
    """Az ffmpeg kimeneti kapcsolói a kijelölt rész letöltéséhez, a haladás egy fájlba megy.
    None, ha nincs gyors kódoló: ilyenkor kulcskép-pontos vágás lesz újrakódolás nélkül."""
    encs = ffmpeg_encoders()
    if is_mac() and "h264_videotoolbox" in encs:
        rate = next(r for h, r in CLIP_VIDEO_BITRATE if (height or 1080) >= h)
        video = ["-c:v", "h264_videotoolbox", "-b:v", rate, "-allow_sw", "1"]
    elif "libx264" in encs:
        video = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]
    else:
        return None
    return video + ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-progress", progress_file]


def read_ffmpeg_progress(path):
    """Az ffmpeg -progress fájljából az eddig elkészült rész hossza másodpercben."""
    try:
        with open(path, "rb") as fh:
            fh.seek(max(0, os.path.getsize(path) - 2048))
            tail = fh.read().decode("utf-8", "replace")
    except OSError:
        return None
    for line in reversed(tail.splitlines()):
        if line.startswith("out_time_us="):
            try:
                return max(0.0, int(line.split("=", 1)[1]) / 1e6)
            except ValueError:
                return None
    return None


class DownloadCancelled(Exception):
    """A felhasználó megszakította a letöltést vagy a lekérést."""


class FetchLogger:
    """Csendes naplózó a videóadatok lekéréséhez. A yt-dlp minden lépésnél ide ír,
    megszakításkor pedig kivételt dobunk, így a lekérés azonnal kilép."""

    def __init__(self, cancel_event, on_message=None):
        self.cancel_event = cancel_event
        self.on_message = on_message

    def _check(self):
        if self.cancel_event.is_set():
            raise DownloadCancelled()

    def _seen(self, msg):
        self._check()
        if self.on_message:
            try:
                self.on_message(str(msg))
            except Exception:
                pass

    def debug(self, msg):
        self._seen(msg)

    def info(self, msg):
        self._seen(msg)

    def warning(self, msg):
        self._check()

    def error(self, msg):
        pass


FETCH_CAP = 90  # az adatlekérés becsült haladása eddig a százalékig nőhet, amíg tart


def advance_fetch_pct(pct, msg):
    """A yt-dlp üzenetéből becsli, hol tart a lekérés. Pontos százalék nem érhető el,
    ezért minden "Downloading ..." lépés a hátralévő út egy részét teljesíti.
    Visszaadja: (új százalék, a lépés magyar neve vagy None)."""
    low = str(msg).lower()
    if "extracting url" in low:
        return max(pct, 5), t("Link megnyitása")
    if "downloading" not in low:
        return pct, None
    if "m3u8" in low or "mpd" in low or "manifest" in low or "format" in low:
        stage = t("Formátumok beolvasása")
    elif "webpage" in low:
        stage = t("Oldal letöltése")
    elif "thumbnail" in low:
        stage = t("Bélyegkép letöltése")
    else:
        stage = t("Adatok lekérése")
    return pct + (FETCH_CAP - pct) * 0.3, stage


def is_partial_file(name, basename):
    """Félkész (ideiglenes) fájl-e a yt-dlp-től ehhez a letöltéshez.
    A kész, korábban letöltött basename.mp4 fájlt sosem érinti."""
    if not name.startswith(basename + "."):
        return False
    suffix = name[len(basename):]
    if suffix.lower().endswith(SUB_EXTS):  # felirat (pl. .fr.srt), nem a videó darabja
        return False
    if suffix.endswith((".part", ".ytdl")) or ".part-Frag" in suffix:
        return True
    if suffix.startswith(".temp."):
        return True
    # külön videó- és hangsáv, pl. .f137.mp4 vagy .f140.m4a
    return re.match(r"^\.f[\w-]+\.\w+$", suffix) is not None


SUB_EXTS = (".srt", ".vtt", ".ass", ".ttml", ".srv3", ".json3")


def subtitle_files(folder, basename):
    """A videóhoz tartozó feliratfájlok (basename.nyelv.srt) útvonalai."""
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    return [os.path.join(folder, n) for n in names
            if n.startswith(basename + ".") and n.lower().endswith(SUB_EXTS)]


def delete_subtitle_files(folder, basename):
    count = 0
    for path in subtitle_files(folder, basename):
        try:
            os.remove(path)
            count += 1
        except OSError:
            pass
    return count


def delete_partial_files(folder, basename):
    """Törli a félkész fájlokat, visszaadja a törölt fájlok számát."""
    count = 0
    try:
        names = os.listdir(folder)
    except OSError:
        return 0
    for name in names:
        if is_partial_file(name, basename):
            try:
                os.remove(os.path.join(folder, name))
                count += 1
            except OSError:
                pass
    return count


TEMP_DIR_NAME = "Vid-Ripper-temp"
OLD_TEMP_DIR_NAME = "PH-Downloader-temp"  # a 4.5 előtti név, csak a takarításhoz
TEMP_PARENT = os.path.join(tempfile.gettempdir(), TEMP_DIR_NAME)


def temp_parent(base=None):
    """A letöltések ideiglenes mappáinak szülője: a megadott mappán belül egy saját almappa.
    Ha a megadott mappa nem használható (például hiányzik a külső lemez), az alapértelmezett."""
    if base:
        try:
            if os.path.isdir(base) and os.access(base, os.W_OK):
                return os.path.join(base, TEMP_DIR_NAME)
        except OSError:
            pass
        log_exc(f"temp_parent: nem használható mappa, alapértelmezett lesz ({base})")
    return TEMP_PARENT


def make_job_temp(base=None):
    """Új, üres ideiglenes mappa egy letöltésnek."""
    parent = temp_parent(base)
    os.makedirs(parent, exist_ok=True)
    return tempfile.mkdtemp(prefix="job_", dir=parent)


def cleanup_old_temp(base=None, max_age=24 * 3600):
    """Indításkor törli a korábbi, félbemaradt letöltések ideiglenes mappáit. Csak a saját
    "job_" mappáinkhoz nyúl, az alapértelmezett és a megadott helyen is."""
    limit = time.time() - max_age
    roots = {tempfile.gettempdir()} | ({base} if base else set())
    for root in roots:
        for dir_name in (TEMP_DIR_NAME, OLD_TEMP_DIR_NAME):
            parent = os.path.join(root, dir_name)
            old = dir_name == OLD_TEMP_DIR_NAME
            try:
                names = os.listdir(parent)
            except OSError:
                continue
            for name in names:
                path = os.path.join(parent, name)
                try:
                    if name.startswith("job_") and os.path.isdir(path) \
                            and (old or os.path.getmtime(path) < limit):
                        shutil.rmtree(path, ignore_errors=True)
                except OSError:
                    pass
            if old:  # a régi nevű mappa, ha kiürült, el is tűnik
                try:
                    os.rmdir(parent)
                except OSError:
                    pass


def find_output_file(folder, basename, ext):
    """A kész fájl útvonala. Ha a várt név nincs meg, a legfrissebb hozzá tartozó fájl."""
    path = os.path.join(folder, basename + ext)
    if os.path.exists(path):
        return path
    try:
        names = [n for n in os.listdir(folder)
                 if n.startswith(basename + ".") and not is_partial_file(n, basename)]
        names.sort(key=lambda n: os.path.getmtime(os.path.join(folder, n)), reverse=True)
    except OSError:
        return path
    return os.path.join(folder, names[0]) if names else path


def add_context_menu(widget):
    """Jobb klikkes (Macen kétujjas kattintás) menü a beviteli mezőkhöz."""
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label=t("Kivágás"), command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label=t("Másolás"), command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label=t("Beillesztés"), command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label=t("Összes kijelölése"),
                     command=lambda: (widget.select_range(0, "end"), widget.icursor("end")))

    def popup(event):
        widget.focus_set()
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    for seq in ("<Button-2>", "<Button-3>", "<Control-Button-1>"):
        widget.bind(seq, popup)


# ---------- saját, lekerekített elemek ----------
class RoundButton(tk.Canvas):
    def __init__(self, parent, text, command, width=None, height=42,
                 bg="ACCENT", fg="ACCENT_FG", hover="ACCENT_HOVER", outline="",
                 font=(FONT_FAMILY, 13, "bold")):
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = BG
        if width:  # hosszabb (például német) feliratnál a gomb szélesebb lesz, nem vágódik le
            try:
                width = max(width, tkfont.Font(root=parent, font=font).measure(text) + 26)
            except Exception:
                pass
        super().__init__(parent, height=height, width=width or 10, bg=parent_bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self._text = text
        self._command = command
        self._bg, self._fg, self._hover = bg, fg, hover
        self._outline = outline
        self._font = font
        self._state = "normal"
        self._hovering = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        if self._state == "disabled" and self._bg == "ACCENT":
            fill = blend_hex(col("ACCENT"), col("BG"), 0.38)
            fg = blend_hex(col("ACCENT_FG"), col("BG"), 0.62)
        elif self._state == "disabled":
            fill, fg = col("DISABLED_BG"), col("DISABLED_FG")
        elif self._hovering:
            fill, fg = col(self._hover), col(self._fg)
        else:
            fill, fg = col(self._bg), col(self._fg)
        round_rect(self, 1, 1, w - 1, h - 1, RADIUS, fill=fill,
                   outline=col(self._outline) if self._outline else fill)
        text = self._text
        if len(text) * 5 > w - 16:  # lehet, hogy nem fér ki: mérés, és rövidítés ha kell
            try:
                fnt = tkfont.Font(root=self, font=self._font)
                limit = w - 16
                while len(text) > 2 and fnt.measure(text) > limit:
                    text = text[:-2].rstrip() + "…"
            except tk.TclError:
                pass
        self.create_text(w / 2, h / 2, text=text, fill=fg, font=self._font)

    def _retheme(self):
        self._draw()

    def set_text(self, text):
        if text != self._text:
            self._text = text
            self._draw()

    def set_colors(self, bg, fg, hover, outline=""):
        """Szerepnevekkel (ACCENT, CONTROL...), így a témaváltás is követi."""
        self._bg, self._fg, self._hover, self._outline = bg, fg, hover, outline
        self._draw()

    def set_state(self, state):
        self._state = state
        self.configure(cursor="arrow" if state == "disabled" else "hand2")
        self._draw()

    def _on_enter(self, _event):
        self._hovering = True
        self._draw()

    def _on_leave(self, _event):
        self._hovering = False
        self._draw()

    def _on_click(self, event):
        if self._state == "disabled":
            return
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self._command()


class RoundBox(tk.Canvas):
    """Lekerekített hátterű doboz egy beviteli mezőnek vagy legördülő listának."""

    CLEAR_SIZE = 22

    def __init__(self, parent, make_widget, height=42, pad=14, clear_command=None):
        super().__init__(parent, height=height, width=10, bg=BG,
                         highlightthickness=0, bd=0)
        self._pad = pad
        self._right = pad  # a jobb oldalon ennyi hely marad a mező után
        self._outline = "BORDER"
        self._clear_btn = None
        self.widget = make_widget(self)
        self._win = self.create_window(pad, height // 2, window=self.widget, anchor="w")
        self._clear_win = None
        if clear_command:
            self._build_clear(clear_command)
        self.bind("<Configure>", self._redraw)
        self.widget.bind("<FocusIn>", lambda e: self._set_outline("ACCENT"), add="+")
        self.widget.bind("<FocusOut>", lambda e: self._set_outline("BORDER"), add="+")

    def _build_clear(self, command):
        """Kis X a mező jobb szélén, kattintásra meghívja a megadott parancsot."""
        s = self.CLEAR_SIZE
        btn = tk.Canvas(self, width=s, height=s, bg=PANEL, highlightthickness=0,
                        bd=0, cursor="hand2")
        self._clear_btn = btn
        self._draw_clear(btn, False)
        btn.bind("<Enter>", lambda e: self._draw_clear(btn, True))
        btn.bind("<Leave>", lambda e: self._draw_clear(btn, False))
        btn.bind("<ButtonRelease-1>", lambda e: command())
        self._clear_win = self.create_window(0, 0, window=btn, anchor="e", state="hidden")
        self._right = 10 + s + 6

    @staticmethod
    def _draw_clear(btn, hover):
        btn.delete("all")
        if hover:
            btn.create_oval(1, 1, 21, 21, fill=col("CONTROL"), outline="")
        color = col("TEXT") if hover else col("GREY")
        btn.create_line(7, 7, 15, 15, fill=color, width=2, capstyle="round")
        btn.create_line(15, 7, 7, 15, fill=color, width=2, capstyle="round")

    def set_clear_visible(self, visible):
        if self._clear_win is not None:
            self.itemconfigure(self._clear_win, state="normal" if visible else "hidden")

    def _set_outline(self, color):
        self._outline = color
        self._redraw()

    def _retheme(self):
        if self._clear_btn is not None:
            self._draw_clear(self._clear_btn, False)
        self._redraw()

    def _redraw(self, _event=None):
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        self.delete("bg")
        if self._outline == "ACCENT":  # fókuszban: kék keret és körülötte halvány fény
            glow = blend_hex(col("ACCENT"), col("BG"), 0.35)
            round_rect(self, 0, 0, w, h, RADIUS + 2, fill=glow, outline=glow, tags="bg")
            round_rect(self, 2, 2, w - 2, h - 2, RADIUS, fill=col("PANEL"),
                       outline=col("ACCENT"), width=1.5, tags="bg")
        else:
            round_rect(self, 1, 1, w - 1, h - 1, RADIUS, fill=col("PANEL"),
                       outline=col(self._outline), width=1.5, tags="bg")
        self.tag_lower("bg")
        self.itemconfigure(self._win, width=max(20, w - self._pad - self._right))
        if self._clear_win is not None:
            self.coords(self._clear_win, w - 10, h / 2)


class BrandMark(tk.Canvas):
    """Az app felirata: "Vid" a téma kiemelő színével, utána "-Ripper"."""

    def __init__(self, parent, style="VD", size=15):
        super().__init__(parent, height=10, width=10, bg=col("SIDEBAR"),
                         highlightthickness=0, bd=0)
        self._font = get_font(size, "bold")
        self.style = style
        self._draw()

    def set_style(self, style):
        self.style = style
        self._draw()

    def _retheme(self):
        self.configure(bg=col("SIDEBAR"))
        self._draw()

    def _text(self, x, text, h, fg):
        self.create_text(x, h / 2, text=text, fill=fg, anchor="w", font=self._font)
        return x + self._font.measure(text)

    def _draw(self):
        self.delete("all")
        h = self._font.metrics("linespace") + 12
        x = self._text(2, "Vid", h, col("ACCENT"))
        x = self._text(x, "-Ripper", h, col("TEXT"))
        self.configure(width=int(x + 4), height=int(h))


class InfoIcon(tk.Canvas):
    """Karikás "i" ikon: fölé víve a kurzort fél másodperc múlva lebegő ablakban
    megjelenik a magyarázat. Így a kártyák rövidek maradnak."""

    DELAY = 500
    SIZE = 18

    def __init__(self, parent, text):
        bg = parent.cget("bg")
        super().__init__(parent, width=self.SIZE, height=self.SIZE, bg=bg,
                         highlightthickness=0, bd=0, cursor="question_arrow"
                         if not is_mac() else "arrow")
        self.text = text
        self._job = None
        self._tip = None
        self._hover = False
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self._draw()

    def _draw(self):
        self.delete("all")
        c = col("TEXT") if self._hover else col("GREY")
        s = self.SIZE
        self.create_oval(1, 1, s - 1, s - 1, outline=c, width=1.4)
        self.create_text(s / 2, s / 2 + 0.5, text="i", fill=c, font=get_font(10, "bold"))

    def _retheme(self):
        try:
            self.configure(bg=self.master.cget("bg"))
        except tk.TclError:
            pass
        self._draw()

    def _enter(self, _e=None):
        self._hover = True
        self._draw()
        self._job = self.after(self.DELAY, self.show)

    def _leave(self, _e=None):
        self._hover = False
        self._draw()
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        self.hide()

    def show(self):
        self._job = None
        if self._tip is not None:
            return
        tip = tk.Toplevel(self)
        tip.withdraw()
        tip.overrideredirect(True)
        try:
            tip.attributes("-topmost", True)
        except tk.TclError:
            pass
        frame = tk.Frame(tip, bg=col("PANEL"), highlightthickness=1,
                         highlightbackground=col("BORDER"), padx=12, pady=9)
        frame.pack()
        tk.Label(frame, text=self.text, bg=col("PANEL"), fg=col("TEXT"), justify="left",
                 wraplength=320, font=get_font(12)).pack()
        tip.update_idletasks()
        x = self.winfo_rootx() + self.SIZE + 8
        y = self.winfo_rooty() - 6
        sw = self.winfo_screenwidth()
        if x + tip.winfo_reqwidth() > sw - 10:
            x = max(10, self.winfo_rootx() - tip.winfo_reqwidth() - 8)
        tip.geometry(f"+{x}+{y}")
        tip.deiconify()
        self._tip = tip

    def hide(self):
        tip, self._tip = self._tip, None
        if tip is not None:
            try:
                tip.destroy()
            except tk.TclError:
                pass


TOAST_ANIMS = {"fade": t("Áttűnés"), "slide": t("Beúszás"), "none": t("Nincs")}


class Toast(tk.Canvas):
    """Egy értesítés a jobb alsó sarokban: bélyegkép (vagy ikon), felső sor, cím, alcím, x.
    Az áttűnéshez minden szín a háttér és a végső szín keveréke (a Tk-ban nincs átlátszóság)."""

    WIDTH = 360
    THUMB = (96, 54)

    def __init__(self, stack, title, message="", kind="ok", action=None, thumb=None,
                 header=None):
        super().__init__(stack.host, width=self.WIDTH, height=60, bg=col("BG"),
                         highlightthickness=0, bd=0, cursor="hand2" if action else "arrow")
        self.stack, self.title, self.message, self.kind = stack, title, message, kind
        self.header, self.action = header, action
        self.alpha = 1.0
        self.dx = 0          # beúszásnál a vízszintes eltolás
        self.leaving = False
        self._anim_job = None
        self._thumb_img = self._prepare_thumb(thumb)
        self._photo = None
        self.bind("<Enter>", lambda e: self.stack.pause(True))
        self.bind("<Leave>", lambda e: self.stack.pause(False))
        self.bind("<ButtonRelease-1>", self._click)
        self._draw()

    def _prepare_thumb(self, data):
        if not data or not HAS_PIL:
            return None
        try:
            from PIL import ImageDraw
            img = Image.open(io.BytesIO(data)).convert("RGB")
            img = ImageOps.fit(img, self.THUMB, Image.LANCZOS)
            mask = Image.new("L", self.THUMB, 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                [0, 0, self.THUMB[0] - 1, self.THUMB[1] - 1], 7, fill=255)
            return img, mask
        except Exception:
            return None

    def _click(self, event):
        if self.leaving:
            return
        if event.x > self.WIDTH - 30 and event.y < 30:  # a bezáró x
            self.stack.remove(self)
            return
        if self.action:
            self.action()
        self.stack.remove(self)

    def _retheme(self):
        self.configure(bg=col("BG"))
        self._draw()

    def _c(self, role):
        """Szín az áttűnés adott pontján (háttérből a végső színbe)."""
        target = role if role.startswith("#") else col(role)
        return target if self.alpha >= 1 else _mix(col("BG"), target, max(0.0, self.alpha))

    def _draw(self):
        self.delete("all")
        w = self.WIDTH
        head_f, title_f, msg_f = get_font(11), get_font(13, "bold"), get_font(12)
        left = 14 + (self.THUMB[0] + 12 if self._thumb_img else 34)
        text_w = w - left - 30
        title_lines = self._wrap(self.title, title_f, text_w)[:2]
        msg_lines = self._wrap(self.message, msg_f, text_w)[:2] if self.message else []
        text_h = (head_f.metrics("linespace") + 2 if self.header else 0) + \
            len(title_lines) * title_f.metrics("linespace") + \
            len(msg_lines) * msg_f.metrics("linespace")
        h = max(text_h, self.THUMB[1] if self._thumb_img else 26) + 30
        self.configure(height=h)
        round_rect(self, 1, 1, w - 1, h - 1, RADIUS + 4, fill=self._c("PANEL"),
                   outline=self._c("BORDER"))
        accent = "DANGER" if self.kind == "error" else "ACCENT"
        if self._thumb_img:
            img, mask = self._thumb_img
            if self.alpha < 1:
                img = Image.blend(Image.new("RGB", self.THUMB, col("PANEL")), img,
                                  max(0.0, self.alpha))
            base = Image.new("RGB", self.THUMB, self._c("PANEL"))
            base.paste(img, (0, 0), mask)
            self._photo = ImageTk.PhotoImage(base)
            self.create_image(14, h / 2, image=self._photo, anchor="w")
            if self.kind == "error":  # kis piros jelzés a kép sarkán
                self.create_oval(14 + self.THUMB[0] - 18, h / 2 - self.THUMB[1] / 2 + 4,
                                 14 + self.THUMB[0] - 4, h / 2 - self.THUMB[1] / 2 + 18,
                                 fill=self._c(accent), outline=self._c(accent))
        else:
            self.create_oval(14, h / 2 - 12, 38, h / 2 + 12, fill=self._c(accent),
                             outline=self._c(accent))
            self.create_text(26, h / 2, text="!" if self.kind == "error" else "\u2713",
                             fill=self._c("ACCENT_FG") if self.kind != "error" else
                             self._c("#ffffff"), font=get_font(12, "bold"))
        y = (h - text_h) / 2
        if self.header:
            self.create_text(left, y, text=self.header, anchor="nw", font=head_f,
                             fill=self._c(accent if self.kind == "error" else "GREY"))
            y += head_f.metrics("linespace") + 2
        for line in title_lines:
            self.create_text(left, y, text=line, anchor="nw", fill=self._c("TEXT"), font=title_f)
            y += title_f.metrics("linespace")
        for line in msg_lines:
            self.create_text(left, y, text=line, anchor="nw", fill=self._c("GREY"), font=msg_f)
            y += msg_f.metrics("linespace")
        self.create_text(w - 16, 16, text="\u00d7", fill=self._c("GREY"), font=get_font(14))

    @staticmethod
    def _wrap(text, font, width):
        out = []
        for para in str(text).split("\n"):
            line = ""
            for word in para.split(" "):
                test = (line + " " + word).strip()
                if font.measure(test) <= width or not line:
                    line = test
                else:
                    out.append(line)
                    line = word
            out.append(line)
        lines = [l for l in out if l] or [""]
        return lines


class ToastStack:
    """Az értesítések a tartalom jobb alsó sarkában, egymás fölé rendezve.
    Néhány másodperc múlva maguktól eltűnnek; amíg az egér rajtuk van, nem.
    Megjelenés és eltűnés: áttűnés, oldalról beúszás vagy animáció nélkül (anim)."""

    LIFETIME = 6000
    MAX = 4
    ANIM_MS = 260  # közepesen gyors

    def __init__(self, host, anim="fade"):
        self.host = host
        self.items = []
        self.anim = anim
        self._paused = False

    def show(self, title, message="", kind="ok", action=None, thumb=None, header=None):
        toast = Toast(self, title, message, kind, action, thumb, header)
        self.items.append(toast)
        while len([t for t in self.items if not t.leaving]) > self.MAX:
            self.remove(next(t for t in self.items if not t.leaving))
        if self.anim == "fade":
            toast.alpha = 0.0
            toast._draw()
        elif self.anim == "slide":
            toast.dx = Toast.WIDTH + 40
        self._layout()
        self._animate(toast, entering=True)
        self.host.after(self.LIFETIME, lambda t=toast: self._expire(t))
        return toast

    def pause(self, value):
        self._paused = value

    def _expire(self, toast):
        if toast not in self.items or toast.leaving:
            return
        if self._paused:  # az egér rajta van: várunk még
            self.host.after(1000, lambda: self._expire(toast))
            return
        self.remove(toast)

    def remove(self, toast):
        if toast not in self.items or toast.leaving:
            return
        toast.leaving = True
        self._paused = False
        if self.anim == "none":
            self._destroy(toast)
        else:
            self._animate(toast, entering=False)

    def _destroy(self, toast):
        if toast in self.items:
            self.items.remove(toast)
        try:
            toast.destroy()
        except tk.TclError:
            pass
        self._layout()

    def _animate(self, toast, entering):
        if self.anim == "none":
            return
        t0 = time.time()
        start_alpha, start_dx = toast.alpha, toast.dx

        def step():
            toast._anim_job = None
            t = min(1.0, (time.time() - t0) * 1000 / self.ANIM_MS)
            e = 1 - (1 - t) ** 3 if entering else t ** 2  # érkezéskor lassul, távozáskor gyorsul
            try:
                if self.anim == "fade":
                    toast.alpha = start_alpha + ((1.0 if entering else 0.0) - start_alpha) * e
                    toast._draw()
                else:
                    end = 0 if entering else Toast.WIDTH + 40
                    toast.dx = int(start_dx + (end - start_dx) * e)
                    self._place(toast)
            except tk.TclError:
                return
            if t < 1:
                toast._anim_job = self.host.after(16, step)
            elif not entering:
                self._destroy(toast)
        if toast._anim_job:
            try:
                self.host.after_cancel(toast._anim_job)
            except Exception:
                pass
        step()

    def _place(self, toast):
        toast.place(relx=1.0, rely=1.0, x=-18 + toast.dx, y=toast._y, anchor="se")

    def _layout(self):
        y = -18
        for toast in reversed(self.items):  # a legújabb legalul
            try:
                toast.update_idletasks()
                toast._y = y
                self._place(toast)
                toast.tk.call("raise", toast._w)  # a vászon lift() mást jelent
                y -= int(toast["height"]) + 10
            except tk.TclError:
                pass


class CommandMenu:
    """Cmd/Ctrl+K keresőmenü: oldalak, témák, műveletek és az előzmények egy helyen,
    billentyűzettel (fel, le, Enter, Esc) vagy egérrel."""

    MAX_ROWS = 9

    def __init__(self, app):
        self.app = app
        self.frame = None

    def toggle(self, _event=None):
        if self.frame is not None:
            self.close()
        else:
            self.open()
        return "break"

    def open(self):
        root = self.app.root
        card = RoundCard(self.app.content)  # a tartalom fölé, nem takarja a bal sávot
        card.inner.configure(padx=12, pady=12)
        card.inner.columnconfigure(0, weight=1)
        self.frame = card
        self.query = tk.StringVar()
        top = tk.Frame(card.inner, bg=PANEL)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        tk.Label(top, text="\u2315", bg=PANEL, fg=GREY, font=get_font(16)).grid(
            row=0, column=0, padx=(4, 8))
        self.entry = tk.Entry(top, textvariable=self.query, bg=PANEL, fg=TEXT, bd=0,
                              insertbackground=TEXT, highlightthickness=0, font=get_font(15))
        self.entry.grid(row=0, column=1, sticky="ew", ipady=4)
        close = tk.Label(top, text="\u00d7", bg=PANEL, fg=GREY, font=get_font(18),
                         cursor="hand2", padx=6)
        close.grid(row=0, column=2)
        close.bind("<Button-1>", lambda e: self.close())
        close.bind("<Enter>", lambda e: close.configure(fg=TEXT))
        close.bind("<Leave>", lambda e: close.configure(fg=GREY))
        self.close_btn = close
        tk.Frame(card.inner, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew", pady=8)
        self.listbox = tk.Listbox(
            card.inner, height=self.MAX_ROWS, bg=PANEL, fg=TEXT, bd=0, highlightthickness=0,
            selectbackground=ACCENT, selectforeground=ACCENT_FG, activestyle="none",
            font=get_font(13), exportselection=False)
        self.listbox.grid(row=2, column=0, sticky="ew")
        self.hint = tk.Label(card.inner, text=t("\u2191\u2193 választás   Enter: megnyitás   Esc: bezárás"),
                             bg=PANEL, fg=GREY, font=get_font(11), anchor="w")
        self.hint.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        card.place(relx=0.5, y=60, anchor="n", relwidth=0.86)
        card.tk.call("raise", card._w)
        self.query.trace_add("write", lambda *a: self._fill())
        self.entry.bind("<Down>", lambda e: self._move(1))
        self.entry.bind("<Up>", lambda e: self._move(-1))
        self.entry.bind("<Return>", lambda e: self._run())
        self.entry.bind("<Escape>", lambda e: self.close())
        self.listbox.bind("<ButtonRelease-1>", lambda e: self._run())
        self.listbox.bind("<Escape>", lambda e: self.close())
        self.entry.bind("<FocusOut>", lambda e: root.after(150, self._maybe_close))
        self._fill()
        self.entry.focus_set()

    def _maybe_close(self):
        if self.frame is None:
            return
        try:
            focus = self.app.root.focus_get()
        except (tk.TclError, KeyError):
            focus = None
        if focus not in (self.entry, self.listbox):
            self.close()

    def close(self):
        frame, self.frame = self.frame, None
        if frame is not None:
            try:
                frame.destroy()
            except tk.TclError:
                pass
        return "break"

    def commands(self):
        app = self.app
        cmds = [
            (t("Videó kiválasztása"), t("Letöltő"), lambda: app._switch_tab("0")),
            (t("Előzmények"), t("Oldal"), lambda: app._switch_tab("2")),
            (t("Beállítások"), t("Oldal"), lambda: app._switch_tab("3")),
            (t("Link beillesztése a vágólapról"), t("Művelet"),
             lambda: (app._switch_tab("0"), app._paste_url())),
            (t("Újdonságok ebben a verzióban"), t("Művelet"), app.show_changelog),
        ]
        for key, label in THEME_STYLES.items():
            cmds.append((t('Téma: {label}').format(label=label), t("Téma"), lambda k=key: app.set_theme_style(k)))
        cmds.append((t("Megjelenés: Sötét"), t("Téma"), lambda: app.set_theme_mode("dark")))
        cmds.append((t("Megjelenés: Világos"), t("Téma"), lambda: app.set_theme_mode("light")))
        return cmds

    def _fill(self):
        q = _fold(self.query.get().strip())
        items = [c for c in self.commands() if not q or q in _fold(c[0])]
        if q and not self.app.hist_locked:  # az előzményekben is keres
            for i, entry in enumerate(self.app.history):
                if history_matches(entry, self.query.get().strip()):
                    items.append((history_label(entry), t("Előzmény"),
                                  lambda i=i: self.app._open_history_index(i)))
                    if len(items) >= 40:
                        break
        self.items = items
        lb = self.listbox
        lb.delete(0, "end")
        for label, group, _ in items:
            lb.insert("end", f"  {label}" + (f"   ·  {group}" if group else ""))
        if not items:
            lb.insert("end", t("  Nincs találat"))
        else:
            lb.selection_set(0)
            lb.activate(0)
        lb.configure(height=max(1, min(self.MAX_ROWS, lb.size())))

    def _move(self, step):
        if not self.items:
            return "break"
        sel = self.listbox.curselection()
        i = (sel[0] if sel else 0) + step
        i = max(0, min(len(self.items) - 1, i))
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(i)
        self.listbox.activate(i)
        self.listbox.see(i)
        return "break"

    def _run(self):
        sel = self.listbox.curselection()
        if not self.items or not sel:
            return "break"
        func = self.items[sel[0]][2]
        self.close()
        func()
        return "break"


class NavItem(tk.Canvas):
    """Egy sor a bal oldali sávban: ikon, név és jobbra egy kis szám (pl. "2 fut")."""

    HEIGHT = 38

    def __init__(self, parent, icon, text, command):
        super().__init__(parent, height=self.HEIGHT, bg=col("SIDEBAR"), highlightthickness=0,
                         bd=0, cursor="hand2")
        self.icon, self.text, self.badge = icon, text, ""
        self.selected = False
        self._hover = False
        self._command = command
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Map>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self._command())

    def _set_hover(self, value):
        self._hover = value
        self._draw()

    def set_selected(self, value):
        if value != self.selected:
            self.selected = value
            self._draw()

    def set_badge(self, text):
        if text != self.badge:
            self.badge = text
            self._draw()

    def set_activity(self, n):
        """Futó letöltések: jobbra egy le-fel mozgó nyíl és a darabszám (0: eltűnik)."""
        if n == getattr(self, "activity", 0):
            return
        self.activity = n
        if n and getattr(self, "_bob_job", None) is None:
            self._bob_t0 = time.time()
            self._bob()
        self._draw()

    def _bob(self):
        self._bob_job = None
        if not getattr(self, "activity", 0):
            return
        try:
            self._draw()
            self._bob_job = self.after(50, self._bob)
        except tk.TclError:
            pass

    def _retheme(self):
        self.configure(bg=col("SIDEBAR"))
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.HEIGHT
        if w <= 1:
            return
        if self.selected:
            round_rect(self, 0, 1, w, h - 1, 9, fill=col("NAV_SEL"), outline=col("NAV_SEL"))
        elif self._hover:
            hov = blend_hex(col("TEXT"), col("SIDEBAR"), 0.06)
            round_rect(self, 0, 1, w, h - 1, 9, fill=hov, outline=hov)
        accent = col("NAV_ACCENT")
        self.create_text(18, h / 2, text=self.icon, font=get_font(14),
                         fill=accent if self.selected else col("GREY"))
        self.create_text(40, h / 2, text=self.text, anchor="w", fill=col("TEXT"),
                         font=get_font(13, "bold" if self.selected else "normal"))
        if getattr(self, "activity", 0):
            # a nyíl lassan le-fel mozog (1,2 mp-es ciklus), mellette a futók száma
            phase = ((time.time() - getattr(self, "_bob_t0", 0)) % 1.2) / 1.2
            dy = 2.5 * math.sin(phase * 2 * math.pi)
            color = col("ACCENT") if not self.selected else accent
            self.create_text(w - 12, h / 2, text=str(self.activity), anchor="e",
                             font=get_font(12, "bold"), fill=color)
            num_w = get_font(12, "bold").measure(str(self.activity))
            self.create_text(w - 16 - num_w, h / 2 + dy, text="↓", anchor="e",
                             font=get_font(13, "bold"), fill=color)
        elif self.badge:
            self.create_text(w - 12, h / 2, text=self.badge, anchor="e", font=get_font(11),
                             fill=accent if self.selected else col("GREY"))


def make_check(parent, text, variable, command=None, size=12):
    """Pipa az app színeivel (a beállításokban, a letöltő oldalon és a listában ugyanígy)."""
    try:
        bg = parent.cget("bg")
    except tk.TclError:
        bg = PANEL
    return tk.Checkbutton(parent, text=text, variable=variable, command=command, anchor="w",
                          bg=bg, fg=TEXT, activebackground=bg, activeforeground=TEXT,
                          selectcolor=CONTROL, highlightthickness=0, bd=0,
                          font=(FONT_FAMILY, size))


def on_off_options():
    return [("off", t("Ki")), ("on", t("Be"))]


def labeled_control(parent, row, text, options, value, command, width):
    """Egy sor: balra a felirat, jobbra a kapcsoló (például Ki / Be). (sor, kapcsoló)"""
    line = tk.Frame(parent, bg=PANEL)
    line.grid(row=row, column=0, sticky="ew", pady=(8, 0))
    line.columnconfigure(0, weight=1)
    tk.Label(line, text=text, bg=PANEL, fg=TEXT, font=(FONT_FAMILY, 13)).grid(
        row=0, column=0, sticky="w")
    ctl = SegmentedControl(line, options, value, command, width=width, height=30)
    ctl.grid(row=0, column=1, sticky="e")
    return line, ctl


def secondary_button(parent, text, command, width=100, height=42, fg="TEXT", **kw):
    """Szürke, másodlagos gomb (a fő, kék gomb mellett: Mégse, Tallózás, Törlés stb.)."""
    return RoundButton(parent, text, command, width=width, height=height, bg="CONTROL",
                       fg=fg, hover="CONTROL_HOVER", outline="BORDER", **kw)


class SegmentedControl(tk.Canvas):
    """Apple stílusú kapcsoló: egymás mellett lévő lehetőségek, az egyik ki van választva."""

    def __init__(self, parent, options, value, command, width=300, height=32):
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = BG
        try:  # minden felirat elférjen (a német szövegek hosszabbak)
            fnt = get_font(13, "bold")
            width = max(width, sum(fnt.measure(lbl) + 28 for _, lbl in options) + 4)
        except Exception:
            pass
        super().__init__(parent, width=width, height=height, bg=parent_bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.options = list(options)  # [(érték, felirat), ...]
        self.value = value
        self._command = command
        self._pulse_i = None
        self._pulse_a = 0.0
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<ButtonRelease-1>", self._on_click)

    def _pulse_step(self, k, steps=8):
        self._pulse_a = 1 - abs(2 * k / steps - 1)
        try:
            self._draw()
            if k < steps:
                self.after(20 * ANIM_SLOW, self._pulse_step, k + 1)
            else:
                self._pulse_i = None
                self._draw()
        except tk.TclError:
            pass

    def set_value(self, value):
        self.value = value
        self._draw()

    def set_label(self, value, label):
        self.options = [(v, label if v == value else t) for v, t in self.options]
        self._draw()

    def _bounds(self, w):
        """Az egyes elemek (bal, jobb) széle. Alapból egyforma szélesek; ha egy felirat
        (például "Aktív letöltések (1)") nem fér el, az kap több helyet."""
        n = len(self.options)
        total = w - 4
        equal = total / n
        try:
            font = get_font(13, "bold")
            need = [font.measure(label) + 28 for _, label in self.options]
        except tk.TclError:
            need = [0] * n
        if all(x <= equal for x in need):
            widths = [equal] * n
        else:
            extra = max(0.0, total - sum(need)) / n
            widths = [x + extra for x in need]
            scale = total / sum(widths)
            widths = [x * scale for x in widths]
        out, x = [], 2.0
        for width in widths:
            out.append((x, x + width))
            x += width
        return out

    def _on_click(self, event):
        w = max(1, self.winfo_width())
        idx = len(self.options) - 1
        for i, (x1, x2) in enumerate(self._bounds(w)):
            if event.x < x2:
                idx = i
                break
        value = self.options[idx][0]
        if value != self.value:
            self.value = value
            self._draw()
            self._command(value)

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        round_rect(self, 0, 0, w, h, RADIUS + 1, fill=col("SEG_TRACK"),
                   outline=col("SEG_TRACK"))
        bounds = self._bounds(w)
        for i, (value, label) in enumerate(self.options):
            x1, x2 = bounds[i]
            seg = x2 - x1
            selected = value == self.value
            if i == self._pulse_i and not selected:
                round_rect(self, x1, 2, x1 + seg, h - 2, RADIUS,
                           fill=blend_hex(col("ACCENT"), col("SEG_TRACK"), self._pulse_a * 0.85),
                           outline=blend_hex(col("ACCENT"), col("SEG_TRACK"), self._pulse_a * 0.85))
            if selected:
                round_rect(self, x1, 2, x1 + seg, h - 2, RADIUS,
                           fill=col("SEG_SEL"), outline=col("BORDER"))
            self.create_text(x1 + seg / 2, h / 2, text=label,
                             fill=col("TEXT") if selected else col("GREY"),
                             font=(FONT_FAMILY, 13, "bold" if selected else "normal"))

    def _retheme(self):
        self._draw()


class RoundProgress(tk.Canvas):
    def __init__(self, parent, height=10):
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = BG
        super().__init__(parent, height=height, width=10, bg=parent_bg,
                         highlightthickness=0, bd=0)
        self._value = 0   # a cél
        self._shown = 0   # ami éppen látszik (ez közelít a célhoz)
        self._job = None
        self.bind("<Configure>", lambda e: self._draw())

    def set(self, value):
        value = max(0, min(100, value))
        if value < self._value or value == 0:  # visszaállítás: nem animáljuk
            self._shown = value
        self._value = value
        self._tick()

    def _tick(self):
        self._job = None
        diff = self._value - self._shown
        if abs(diff) < 0.4:
            self._shown = self._value
        else:
            self._shown += diff * (0.3 / ANIM_SLOW)
            try:
                self._job = self.after(16, self._tick)
            except tk.TclError:
                self._shown = self._value
        self._draw()

    def set_live(self, on):
        """Élő felvétel: piros, mozgó csíkos sáv (nincs ismert vége)."""
        on = bool(on)
        if on == getattr(self, "_live", False):
            return
        self._live = on
        self._offset = 0
        if on:
            self._live_tick()
        else:
            self._draw()

    def _live_tick(self):
        if not getattr(self, "_live", False):
            return
        self._offset = (self._offset + 1) % 18
        try:
            if self.winfo_ismapped():
                self._draw()
            self.after(60, self._live_tick)
        except tk.TclError:
            self._live = False

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        if getattr(self, "_live", False):
            base = col("DANGER")
            light = blend_hex("#ffffff", base, 0.35)
            round_rect(self, 0, 0, w, h, h / 2, fill=base, outline=base)
            r = h / 2  # a lekerekített végeken nem rajzolunk csíkot
            for x in range(-18 + self._offset, w + 18, 18):
                if x >= r and x + 12 <= w - r:
                    self.create_polygon(x, h, x + 6, 0, x + 12, 0, x + 6, h,
                                        fill=light, outline="")
            return
        round_rect(self, 0, 0, w, h, h / 2, fill=col("SEG_TRACK"), outline=col("SEG_TRACK"))
        fill_w = w * self._shown / 100
        if fill_w > h:
            round_rect(self, 0, 0, fill_w, h, h / 2, fill=col("ACCENT"), outline=col("ACCENT"))

    def _retheme(self):
        self._draw()


class EmptyState(tk.Canvas):
    """Üres lista helyett: kerek ikon, cím és rövid magyarázat középen."""

    def __init__(self, parent, kind, title, hint, height=210):
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = BG
        super().__init__(parent, height=height, width=10, bg=parent_bg,
                         highlightthickness=0, bd=0)
        self.kind, self.title, self.hint = kind, title, hint
        self.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        cx, cy, r = w / 2, h / 2 - 34, 34
        self.create_oval(cx - r, cy - r, cx + r, cy + r, fill=col("CHIP"), outline="")
        line = col("GREY")
        if self.kind == "search":
            self.create_oval(cx - 13, cy - 14, cx + 7, cy + 6, outline=line, width=3)
            self.create_line(cx + 6, cy + 5, cx + 15, cy + 14, fill=line, width=3,
                             capstyle="round")
        elif self.kind == "clock":
            self.create_oval(cx - 15, cy - 15, cx + 15, cy + 15, outline=line, width=3)
            self.create_line(cx, cy, cx, cy - 9, fill=line, width=3, capstyle="round")
            self.create_line(cx, cy, cx + 7, cy + 4, fill=line, width=3, capstyle="round")
        else:
            self.create_line(cx, cy - 15, cx, cy + 8, fill=line, width=3, capstyle="round")
            self.create_line(cx - 9, cy, cx, cy + 9, cx + 9, cy, fill=line, width=3,
                             capstyle="round", joinstyle="round")
            self.create_line(cx - 14, cy + 17, cx + 14, cy + 17, fill=line, width=3,
                             capstyle="round")
        self.create_text(cx, cy + r + 24, text=self.title, fill=col("TEXT"),
                         font=(FONT_FAMILY, 14, "bold"))
        self.create_text(cx, cy + r + 50, text=self.hint, fill=col("GREY"), width=w - 60,
                         justify="center", font=(FONT_FAMILY, 12))

    def _retheme(self):
        self._draw()


class RoundCard(tk.Canvas):
    """Lekerekített kártya, amibe elemeket lehet tenni (a .inner keretbe)."""

    def __init__(self, parent):
        try:
            parent_bg = parent.cget("bg")
        except Exception:
            parent_bg = BG
        super().__init__(parent, height=10, width=10, bg=parent_bg,
                         highlightthickness=0, bd=0)
        self.inner = tk.Frame(self, bg=PANEL)
        self._win = self.create_window(2, 2, window=self.inner, anchor="nw")
        self.outline_role = "BORDER"
        self.bind("<Configure>", self._on_resize)
        self.inner.bind("<Configure>", self._on_inner)

    def set_outline(self, role):
        """A keret színe szerepnévvel (BORDER, ACCENT, OK = a kész zöldje, DANGER)."""
        if role != self.outline_role:
            self.outline_role = role
            self._draw()

    def _on_resize(self, event):
        self.itemconfigure(self._win, width=max(10, event.width - 4))
        self._draw()

    def _on_inner(self, event):
        self.configure(height=self.inner.winfo_reqheight() + 4)

    def sync_height(self):
        """A kártya magassága a tartalma szerint akkor is, ha épp nem látszik."""
        h = self.inner.winfo_reqheight() + 4
        if self.winfo_reqheight() != h:
            self.configure(height=h)
        return h

    def _draw(self):
        self.delete("bg")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        outline = ok_color() if self.outline_role == "OK" else col(self.outline_role)
        round_rect(self, 1, 1, w - 1, h - 1, RADIUS + 4, fill=col("PANEL"),
                   outline=outline, width=2 if self.outline_role != "BORDER" else 1, tags="bg")
        self.tag_lower("bg")

    def _retheme(self):
        self._draw()


class PreviewCard(tk.Canvas):
    """Kártya a videó bélyegképével, címével és adataival. Megjelenéskor előtűnik."""

    STEPS = 9

    def __init__(self, parent, height=152):
        super().__init__(parent, height=height, width=10, bg=BG,
                         highlightthickness=0, bd=0)
        self._title = ""
        self._details = []
        self._photo = None
        self._pil = None
        self._frame_photo = None
        self._a = 1.0
        self._job = None
        self.bind("<Configure>", lambda e: self._draw())

    def show(self, title, details, photo=None, pil=None, animate=False):
        self._title = title
        self._details = details
        self._photo = photo
        self._pil = pil
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        if animate:
            self._a = 0.0
            self._advance(0)
        else:
            self._a = 1.0
            self._draw()

    def _advance(self, i):
        self._job = None
        t = i / self.STEPS
        self._a = 1 - (1 - t) ** 2  # lassulva érkezik
        self._draw()
        if i < self.STEPS:
            try:
                self._job = self.after(22 * ANIM_SLOW, self._advance, i + 1)
            except tk.TclError:
                self._a = 1.0

    def set_details(self, details):
        self._details = details
        self._draw()

    def thumb_geometry(self):
        """A bélyegkép helye a képernyőn (x, y, szélesség, magasság), vagy None."""
        try:
            if self._photo is None or self._pil is None or not self.winfo_ismapped():
                return None
            w, h = self._pil.size
            return (self.winfo_rootx() + 14,
                    self.winfo_rooty() + (self.winfo_height() - h) // 2, w, h)
        except tk.TclError:
            return None

    def _retheme(self):
        self._draw()

    def _fade(self, color):
        return blend_hex(col(color), col("BG"), self._a) if self._a < 1 else col(color)

    def _photo_now(self):
        if self._a >= 1 or self._pil is None or not HAS_PIL:
            return self._photo
        try:
            back = Image.new("RGB", self._pil.size, hex_rgb(col("BG")))
            self._frame_photo = ImageTk.PhotoImage(Image.blend(back, self._pil, self._a))
            return self._frame_photo
        except Exception:
            return self._photo

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4:
            return
        round_rect(self, 1, 1, w - 1, h - 1, RADIUS, fill=self._fade("PANEL"),
                   outline=self._fade("BORDER"))

        photo = self._photo_now()
        x = 14
        if photo is not None:
            self.create_image(14, h / 2, image=photo, anchor="w")
            x = 14 + photo.width() + 14
        wrap = max(80, w - x - 14)

        title = self._title if len(self._title) <= 90 else self._title[:89] + "…"
        item = self.create_text(x, 0, text=title, fill=self._fade("TEXT"), anchor="nw",
                                width=wrap, font=(FONT_FAMILY, 13, "bold"), tags="txt")
        y = (self.bbox(item) or (0, 0, 0, 0))[3] + 6  # üres cím: nincs szövegdoboz

        measure = get_font(12).measure
        for label, value in self._details:
            label_text = f"{label}: "
            lw = measure(label_text)
            self.create_text(x, y, text=label_text, fill=self._fade("GREY"), anchor="nw",
                             font=(FONT_FAMILY, 12), tags="txt")
            val = self.create_text(x + lw, y, text=value, fill=self._fade("TEXT"),
                                   anchor="nw", width=max(40, wrap - lw),
                                   font=(FONT_FAMILY, 12), tags="txt")
            y = (self.bbox(val) or (0, y, 0, y))[3] + 3

        # a szöveg függőleges középre igazítása
        box = self.bbox("txt")
        if box:
            self.move("txt", 0, (h - (box[3] - box[1])) / 2 - box[1])
        if self._a < 1:  # közben kicsit lentről csúszik a helyére
            self.move("all", 0, (1 - self._a) * 10)


RESIZE_SETTLE_MS = 120  # átméretezéskor ennyi szünet után igazodik a tartalom szélessége


class CanvasStack:
    """Görgethető oszlop, amelyben minden elem (kártya, csoportcím) külön ablak-elem a vásznon.
    A Tk a látható részen kívül eső ablak-elemeket leveszi a képernyőről, így átméretezéskor
    és görgetéskor csak a látszó néhány kártyát kell kirajzolni, nem mind a százat. Macen egy
    keretben tartott sok kártya miatt egy átméretezési lépés másodpercekig is tartott.
    A szélesség húzásos átméretezés közben nem követi az ablakot, csak amikor megáll a húzás."""

    def __init__(self, canvas, right_gap=22, end_pad=0):
        self.canvas = canvas
        self.gap = right_gap
        self.end_pad = end_pad
        self.items = []
        self.total = 0
        self._region = None
        self._job = None
        self._width_job = None
        self._canvas_width = None
        canvas.bind("<Configure>", self._on_canvas_configure)

    # --- elemek ---
    def width(self):
        try:
            return max(self.canvas.winfo_width() - self.gap, 100)
        except tk.TclError:
            return 100

    def add(self, widget, top=0, bottom=0, padx=0, keep=False, footer=False):
        """Új elem az oszlop végére (a lábléc elé). `keep`: az ürítés nem törli."""
        item = self.canvas.create_window(padx, self.total, window=widget, anchor="nw",
                                         width=max(10, self.width() - 2 * padx))
        rec = {"w": widget, "id": item, "top": top, "bottom": bottom, "padx": padx,
               "keep": keep or footer, "footer": footer, "y": None, "h": None}
        pos = len(self.items)
        if not footer:
            while pos and self.items[pos - 1]["footer"]:
                pos -= 1
        self.items.insert(pos, rec)
        widget.bind("<Configure>", self._on_item_configure, add="+")
        self.relayout_soon()
        return widget

    def clear(self):
        """A nem megtartott elemek törlése (pl. a kártyák újraépítése előtt)."""
        for rec in [r for r in self.items if not r["keep"]]:
            try:
                self.canvas.delete(rec["id"])
                rec["w"].destroy()
            except tk.TclError:
                pass
        self.items = [r for r in self.items if r["keep"]]
        self.relayout_soon()

    def bounds(self, widget):
        """(teteje, magassága) a vásznon, a widget vagy valamelyik szülője alapján."""
        self.relayout()
        w = widget
        while w is not None:
            for rec in self.items:
                if rec["w"] is w:
                    return rec["y"] or 0, rec["h"] or 0
            w = getattr(w, "master", None)
        return None

    # --- elrendezés ---
    @staticmethod
    def _height(widget):
        sync = getattr(widget, "sync_height", None)
        if sync is not None:
            return sync()
        if widget.winfo_class() == "Frame" and not (
                widget.grid_slaves() or widget.pack_slaves() or widget.place_slaves()):
            # a Tk az üressé vált keret régi méretét megtartja (pl. ha a FOLYAMATBAN rész
            # eltűnt): ilyenkor kézzel zsugorítjuk, különben nagy üres hely marad
            if widget.winfo_reqheight() > 1:
                widget.configure(height=1)
            return 1
        return widget.winfo_reqheight()

    def relayout_soon(self):
        if self._job is None:
            try:
                self._job = self.canvas.after_idle(self.relayout)
            except tk.TclError:
                pass

    def relayout(self):
        if self._job is not None:
            try:
                self.canvas.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        c = self.canvas
        try:
            view_top = c.canvasy(0)
        except tk.TclError:
            return
        # az első látszó elem a helyén marad, ha fölötte valami megnőtt vagy összement
        anchor = next((r for r in self.items if r["y"] is not None
                       and r["y"] + r["h"] > view_top), None)
        old_anchor_y = anchor["y"] if anchor else None
        y = 0
        try:
            for rec in self.items:
                y += rec["top"]
                h = self._height(rec["w"])
                if rec["y"] != y:
                    c.coords(rec["id"], rec["padx"], y)
                rec["y"], rec["h"] = y, h
                y += h + rec["bottom"]
        except tk.TclError:
            return
        self.total = y + self.end_pad
        region = (0, 0, self.width(), self.total)
        if region != self._region:
            self._region = region
            c.configure(scrollregion=region)
        if anchor is not None and anchor in self.items and view_top > 0:
            shift = anchor["y"] - old_anchor_y
            if shift:
                new_top = max(0, view_top + shift)
                c.yview_moveto(new_top / max(1, self.total))
                if getattr(c, "_sc_job", None) is not None:  # épp görgetés-animáció fut
                    c._sc_pos = getattr(c, "_sc_pos", view_top) + shift
                    c._sc_target = getattr(c, "_sc_target", view_top) + shift

    def _on_item_configure(self, event):
        for rec in self.items:
            if rec["w"] is event.widget:
                if rec["h"] != event.height:
                    self.relayout_soon()
                return

    # --- szélesség ---
    def _apply_width(self):
        self._width_job = None
        w = self.width()
        try:
            for rec in self.items:
                self.canvas.itemconfigure(rec["id"], width=max(10, w - 2 * rec["padx"]))
        except tk.TclError:
            return
        self.relayout_soon()

    def _on_canvas_configure(self, event):
        if event.width == self._canvas_width:
            return
        first = self._canvas_width is None
        self._canvas_width = event.width
        if self._width_job is not None:
            self.canvas.after_cancel(self._width_job)
        if first:
            self._apply_width()
        else:
            self._width_job = self.canvas.after(RESIZE_SETTLE_MS, self._apply_width)


def track_scroll_body(canvas, body):
    """A görgetési terület mérete csak akkor frissül, ha a tartalom tényleg átméreteződött.
    A görgetés maga is <Configure>-t küld (elmozdul a keret), ilyenkor nincs teendő:
    enélkül minden görgetési lépés egy teljes újrarajzolást is kért, ez akadozott Macen."""
    last = [None]

    def on_configure(event):
        size = (event.width, event.height)
        if size != last[0]:
            last[0] = size
            canvas.configure(scrollregion=canvas.bbox("all"))
    body.bind("<Configure>", on_configure)


def auto_scrollbar(bar, lo, hi, **grid):
    """A görgetősáv csak akkor látszik, ha nem fér el minden. Csak váltáskor nyúlunk az
    elrendezéshez, mert a grid() minden hívása újraszámolja az oldalt."""
    bar.set(lo, hi)
    need = not (float(lo) <= 0.0 and float(hi) >= 1.0)
    if getattr(bar, "_shown", None) is need:
        return
    bar._shown = need
    if need:
        bar.grid(**grid)
    else:
        bar.grid_remove()


def bring_to_front(win):
    """Az ablak előre kerül és megkapja a fókuszt. Kicsit később is, mert Macen a kattintás
    befejezése után a főablak még visszaveheti az elsőbbséget."""
    def front():
        try:
            if win.winfo_exists():
                win.deiconify()
                win.lift()
                win.focus_force()
        except tk.TclError:
            pass
    front()
    win.after(60, front)


def center_over(win, parent, min_y=0):
    """A párbeszédablakot a szülő ablak közepére teszi (a méretét a tartalom adja)."""
    parent.update_idletasks()
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
    win.geometry(f"+{max(x, 0)}+{max(y, min_y)}")


class Dialog(tk.Toplevel):
    """Saját felugró ablak, ami az app ablakának közepén jelenik meg."""

    HEADINGS = {"info": t("Letöltés kész"), "warning": t("Figyelem"), "error": t("Hiba")}

    def __init__(self, parent, kind, message):
        super().__init__(parent)
        self.withdraw()
        self.title(APP_NAME)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)

        accent = DANGER if kind == "error" else TEXT
        body = tk.Frame(self, bg=BG, padx=26, pady=22)
        body.pack()
        tk.Label(body, text=self.HEADINGS.get(kind, APP_NAME), bg=BG, fg=accent,
                 font=(FONT_FAMILY, 14, "bold")).pack(anchor="w")
        tk.Label(body, text=message, bg=BG, fg=TEXT, font=(FONT_FAMILY, 13),
                 justify="left", wraplength=360).pack(anchor="w", pady=(10, 18))
        RoundButton(body, "OK", self.destroy, width=100).pack(anchor="e")
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

        center_over(self, parent)

        self.deiconify()
        fade_in(self)
        self.wait_visibility()
        self.grab_set()
        self.focus_set()


class ConfirmDialog(tk.Toplevel):
    """Igen/Nem jellegű kérdés, az app ablakának közepén. Az eredmény a result mezőben."""

    def __init__(self, parent, heading, message, yes_text, no_text, danger):
        super().__init__(parent)
        self.withdraw()
        self.title(APP_NAME)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.result = False

        accent = DANGER if danger else TEXT
        body = tk.Frame(self, bg=BG, padx=26, pady=22)
        body.pack()
        tk.Label(body, text=heading, bg=BG, fg=accent,
                 font=(FONT_FAMILY, 14, "bold")).pack(anchor="w")
        tk.Label(body, text=message, bg=BG, fg=TEXT, font=(FONT_FAMILY, 13),
                 justify="left", wraplength=400).pack(anchor="w", pady=(10, 18))
        row = tk.Frame(body, bg=BG)
        row.pack(anchor="e")
        secondary_button(row, no_text, lambda: self._finish(False),
                    width=max(100, 9 * len(no_text) + 36)).pack(side="left")
        RoundButton(row, yes_text, lambda: self._finish(True),
                    width=max(100, 9 * len(yes_text) + 36)).pack(side="left", padx=(10, 0))
        self.bind("<Escape>", lambda e: self._finish(False))
        if not danger:
            self.bind("<Return>", lambda e: self._finish(True))
        self.protocol("WM_DELETE_WINDOW", lambda: self._finish(False))

        center_over(self, parent)

        self.deiconify()
        fade_in(self)
        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    def _finish(self, value):
        self.result = value
        self.destroy()


class PlaylistDialog(tk.Toplevel):
    """Lejátszási lista: itt lehet kipipálni, melyik videókat töltsük le. Eredmény a result mezőben:
    (kiválasztott elemek, felbontás felirata) vagy None."""

    def __init__(self, parent, title, entries, capped, res_values, default_res):
        super().__init__(parent)
        self.withdraw()
        self.title(APP_NAME)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.result = None
        self.entries = entries
        self.vars = [tk.BooleanVar(value=True) for _ in entries]
        self.res = tk.StringVar(value=default_res)

        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack()
        head = title if len(title) <= 46 else title[:45] + "…"
        tk.Label(body, text=head, bg=BG, fg=TEXT, anchor="w",
                 font=(FONT_FAMILY, 14, "bold")).pack(anchor="w")
        note = t('{n_entries} videót találtam').format(n_entries=len(entries))
        if capped:
            note += t(' (az első {playlist_max}-ra korlátoztam)').format(playlist_max=PLAYLIST_MAX)
        tk.Label(body, text=note + t(". Pipáld ki, amit le szeretnél tölteni."), bg=BG, fg=GREY,
                 anchor="w", font=(FONT_FAMILY, 12)).pack(anchor="w", pady=(2, 10))

        box = tk.Frame(body, bg=PANEL)
        box.pack(fill="x")
        self.canvas = tk.Canvas(box, bg=PANEL, width=460, height=300, highlightthickness=0, bd=0)
        bar = ttk.Scrollbar(box, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        inner = tk.Frame(self.canvas, bg=PANEL)
        self.canvas.create_window((0, 0), window=inner, anchor="nw")
        track_scroll_body(self.canvas, inner)
        self.checks = []
        for entry, var in zip(entries, self.vars):
            name = entry["title"] if len(entry["title"]) <= 52 else entry["title"][:51] + "…"
            if entry.get("duration"):
                name += f"  ({format_duration(entry['duration'])})"
            cb = make_check(inner, name, var, self._update_count)
            cb.pack(fill="x", padx=8, pady=1)
            self.checks.append(cb)
        for w in (self.canvas, inner, *self.checks):
            w.bind("<MouseWheel>", self._wheel)
            w.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
            w.bind("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))

        tools = tk.Frame(body, bg=BG)
        tools.pack(fill="x", pady=(10, 0))
        small = (FONT_FAMILY, 12)
        secondary_button(tools, t("Mind"), lambda: self._set_all(True), width=70, height=28,
                    font=small).pack(side="left")
        secondary_button(tools, t("Egyik sem"), lambda: self._set_all(False), width=90, height=28,
                    font=small).pack(side="left", padx=(6, 0))
        self.res_box = ttk.Combobox(tools, textvariable=self.res, state="readonly",
                                    style="Chip.TCombobox", values=res_values, width=14,
                                    font=(FONT_FAMILY, 13))
        self.res_box.pack(side="right")
        tk.Label(tools, text=t("Minőség"), bg=BG, fg=GREY, font=small).pack(side="right", padx=(0, 8))

        row = tk.Frame(body, bg=BG)
        row.pack(fill="x", pady=(16, 0))
        self.count = tk.Label(row, text="", bg=BG, fg=GREY, font=small)
        self.count.pack(side="left")
        RoundButton(row, t("Sorba állítás"), self._accept, width=130).pack(side="right")
        secondary_button(row, t("Mégse"), self._cancel, width=90).pack(side="right", padx=(0, 10))
        self._update_count()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())

        center_over(self, parent)
        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    def _wheel(self, event):
        step = -1 if event.delta > 0 else 1
        if abs(event.delta) >= 120:  # Windows
            step *= max(1, abs(event.delta) // 120)
        self.canvas.yview_scroll(step * 2, "units")

    def _chosen(self):
        return [e for e, v in zip(self.entries, self.vars) if v.get()]

    def _set_all(self, value):
        for v in self.vars:
            v.set(value)
        self._update_count()

    def _update_count(self):
        n = len(self._chosen())
        self.count.configure(text=t('{n} kijelölve').format(n=n))

    def _accept(self):
        chosen = self._chosen()
        if not chosen:
            return
        self.result = (chosen, self.res.get())
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class PasswordDialog(tk.Toplevel):
    """Jelszó bekérő ablak egy vagy több mezővel. Az eredmény a result mezőben:
    a beírt értékek listája, vagy None, ha mégsem. A validate(értékek) hibaszöveget ad
    vissza (és az ablak nyitva marad), vagy None-t, ha rendben van."""

    def __init__(self, parent, heading, message, labels, ok_text, validate=None, danger=False):
        super().__init__(parent)
        self.withdraw()
        self.title(APP_NAME)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.result = None
        self._validate = validate
        self.vars = [tk.StringVar() for _ in labels]

        body = tk.Frame(self, bg=BG, padx=26, pady=22)
        body.pack()
        tk.Label(body, text=heading, bg=BG, fg=DANGER if danger else TEXT,
                 font=(FONT_FAMILY, 14, "bold")).pack(anchor="w")
        if message:
            tk.Label(body, text=message, bg=BG, fg=TEXT, font=(FONT_FAMILY, 13),
                     justify="left", wraplength=360).pack(anchor="w", pady=(10, 4))
        self.entries = []
        for label, var in zip(labels, self.vars):
            tk.Label(body, text=label, bg=BG, fg=GREY, font=(FONT_FAMILY, 12)).pack(
                anchor="w", pady=(10, 3))
            box = RoundBox(body, lambda p, v=var: tk.Entry(p, textvariable=v, show="•",
                                                           **entry_kw()),
                           height=36, pad=12)
            box.configure(width=360)
            box.pack(fill="x")
            box.widget.bind("<Return>", lambda e: self._accept())
            self.entries.append(box.widget)
        self.error = tk.Label(body, text="", bg=BG, fg=DANGER, justify="left", wraplength=360,
                              font=(FONT_FAMILY, 12))
        self.error.pack(anchor="w", pady=(10, 0))
        row = tk.Frame(body, bg=BG)
        row.pack(anchor="e", pady=(14, 0))
        secondary_button(row, t("Mégse"), self._cancel, width=100).pack(side="left")
        RoundButton(row, ok_text, self._accept, width=max(110, 9 * len(ok_text) + 36)).pack(
            side="left", padx=(10, 0))
        self.bind("<Escape>", lambda e: self._cancel())
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        center_over(self, parent)
        self.deiconify()
        self.wait_visibility()
        self.grab_set()
        if self.entries:
            self.entries[0].focus_set()

    def _accept(self):
        values = [v.get() for v in self.vars]
        if self._validate:
            problem = self._validate(values)
            if problem:
                self.error.configure(text=problem)
                return
        self.result = values
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class AboutDialog(tk.Toplevel):
    """A Névjegy ablak: Macen az alkalmazásmenü "About Vid-Ripper" pontjából nyílik.
    Sima, külön ablak (nem tartozik a főablakhoz), hogy mozgatás közben ne akadozzon."""

    def __init__(self, parent, app, icon):
        super().__init__(parent)
        self.withdraw()
        self.app = app
        self.title(t("{app} névjegye").format(app=APP_NAME))
        self.configure(bg=BG)
        self._icon = icon  # a képet tartani kell, különben eltűnik

        body = tk.Frame(self, bg=BG, padx=34, pady=24)
        body.pack()
        if icon is not None:
            tk.Label(body, image=icon, bg=BG).pack(pady=(0, 10))
        tk.Label(body, text=APP_NAME, bg=BG, fg=TEXT,
                 font=(FONT_FAMILY, 18, "bold")).pack()
        tk.Label(body, text=CREDIT, bg=BG, fg=GREY,
                 font=(FONT_FAMILY, 13)).pack(pady=(4, 12))

        info = tk.Frame(body, bg=BG)
        info.pack()
        tk.Label(info, text=t("Alkalmazás verziója"), bg=BG, fg=GREY,
                 font=(FONT_FAMILY, 13)).grid(row=0, column=0, sticky="w", padx=(0, 22), pady=2)
        tk.Label(info, text=f"v.{APP_VERSION}", bg=BG, fg=TEXT,
                 font=(FONT_FAMILY, 13)).grid(row=0, column=1, sticky="w", pady=2)
        tk.Label(info, text=t("yt-dlp verziója"), bg=BG, fg=GREY,
                 font=(FONT_FAMILY, 13)).grid(row=1, column=0, sticky="w", padx=(0, 22), pady=2)
        tk.Label(info, text=str(YTDLP_VERSION), bg=BG, fg=TEXT,
                 font=(FONT_FAMILY, 13)).grid(row=1, column=1, sticky="w", pady=2)

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(14, 14))
        box = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        box.pack(fill="both")
        self.guide = tk.Text(box, width=64, height=20, wrap="word", bg=PANEL, fg=TEXT,
                             bd=0, highlightthickness=0, padx=14, pady=8, cursor="arrow",
                             font=(FONT_FAMILY, 13), spacing3=3, takefocus=0)
        bar = ttk.Scrollbar(box, orient="vertical", command=self.guide.yview)
        self.guide.configure(yscrollcommand=bar.set)
        self.guide.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self._fill_guide()

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind(f"<{MOD_KEY}-w>", lambda e: self.destroy())

        center_over(self, parent, 30)
        bring_to_front(self)

    def _fill_guide(self):
        txt = self.guide
        txt.tag_configure("p", lmargin1=4, lmargin2=4, spacing3=10)
        txt.tag_configure("item", lmargin1=4, lmargin2=24)
        txt.insert("end", ABOUT_INTRO + "\n", "p")
        for line in ABOUT_FEATURES:
            txt.insert("end", "•  " + line + "\n", "item")
        txt.configure(state="disabled")

class ChangelogDialog(tk.Toplevel):
    """Újdonságok: a verziók közti változások, a legfrissebbtől visszafelé."""

    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.title(t("Újdonságok"))
        self.configure(bg=BG)
        body = tk.Frame(self, bg=BG, padx=30, pady=22)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=t("Újdonságok"), bg=BG, fg=TEXT, anchor="w",
                 font=(FONT_FAMILY, 18, "bold")).pack(fill="x")
        tk.Label(body, text=t('Jelenlegi verzió: v.{app_version}').format(app_version=APP_VERSION), bg=BG, fg=GREY, anchor="w",
                 font=(FONT_FAMILY, 12)).pack(fill="x", pady=(2, 12))
        box = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        box.pack(fill="both", expand=True)
        self.text = tk.Text(box, width=58, height=20, wrap="word", bg=PANEL, fg=TEXT,
                            bd=0, highlightthickness=0, padx=16, pady=8, cursor="arrow",
                            font=(FONT_FAMILY, 13), spacing3=3, takefocus=0)
        bar = ttk.Scrollbar(box, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=bar.set)
        self.text.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self._fill()
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind(f"<{MOD_KEY}-w>", lambda e: self.destroy())
        center_over(self, parent, 30)
        bring_to_front(self)

    def _fill(self):
        txt = self.text
        txt.tag_configure("v", font=(FONT_FAMILY, 15, "bold"), spacing1=14, spacing3=4)
        txt.tag_configure("new", font=(FONT_FAMILY, 12, "bold"), foreground=ACCENT_TEXT)
        txt.tag_configure("item", lmargin1=4, lmargin2=24)
        for i, (ver, items) in enumerate(CHANGELOG):
            label = t("Korábbi, 1.0 előtti verziók") if ver == "0.x" else f"v.{ver}"
            txt.insert("end", label, "v")
            if ver == APP_VERSION:
                txt.insert("end", t("   jelenlegi"), "new")
            txt.insert("end", "\n")
            for line in items:
                txt.insert("end", "•  " + line + "\n", "item")
        txt.configure(state="disabled")


def open_default(path):
    """A fájl megnyitása az operációs rendszer alapértelmezett programjával.
    Visszaadja, hogy sikerült-e elindítani."""
    try:
        if is_mac():
            subprocess.run(["open", path], timeout=10, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif is_win():
            os.startfile(path)  # noqa: F821  (csak Windowson van)
        else:
            subprocess.run(["xdg-open", path], timeout=10, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        log_exc("open_default")
        return False


_PLAYER_NAMES = {}


def default_player_name(path):
    """Az operációs rendszer alapértelmezett lejátszójának neve a fájlhoz (pl. QuickTime Player),
    vagy None, ha nem derül ki. Kiterjesztésenként gyorsítótárazva."""
    ext = os.path.splitext(path)[1].lower()
    if ext in _PLAYER_NAMES:
        return _PLAYER_NAMES[ext]
    name = None
    try:
        if is_mac():
            # a fájl útvonala argumentumként megy (nem a szövegbe), így semmi nem törheti el
            script = ('use framework "Foundation"\nuse framework "AppKit"\n'
                      "on run argv\n"
                      "set u to current application's NSURL's fileURLWithPath:(item 1 of argv)\n"
                      "set a to current application's NSWorkspace's sharedWorkspace()"
                      "'s URLForApplicationToOpenURL:u\n"
                      "return (a's lastPathComponent()) as text\n"
                      "end run\n")
            res = subprocess.run(["osascript", "-", path], input=script,
                                 capture_output=True, text=True, timeout=8)
            out = res.stdout.strip()
            if res.returncode == 0 and out:
                name = out[:-4] if out.lower().endswith(".app") else out
        elif is_win():
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            size = ctypes.c_ulong(260)
            # ASSOCSTR_FRIENDLYAPPNAME = 4
            if ctypes.windll.shlwapi.AssocQueryStringW(0, 4, ext, None, buf,
                                                       ctypes.byref(size)) == 0:
                name = buf.value or None
        else:
            import mimetypes
            mime = mimetypes.guess_type(path)[0]
            if mime:
                res = subprocess.run(["xdg-mime", "query", "default", mime],
                                     capture_output=True, text=True, timeout=5)
                desk = res.stdout.strip()
                if desk.endswith(".desktop"):
                    name = desk[:-8].split(".")[-1].replace("-", " ").title()
    except Exception:
        log_exc("default_player_name")
        name = None
    if name:
        name = name.strip()[:28] or None
    _PLAYER_NAMES[ext] = name
    return name


def usable_geometry(geo, sw, sh, min_w=480, min_h=320):
    """A mentett ablakhelyzet, ha érvényes és látszik a képernyőn (pl. már nincs meg a második
    monitor); különben None."""
    if not isinstance(geo, str) or not PLAYER_GEO_RE.match(geo):
        return None
    m = re.match(r"^(\d+)x(\d+)([+-]\d+)([+-]\d+)$", geo)
    w, h, x, y = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    if w < min_w or h < min_h or w > sw + 200 or h > sh + 200:
        return None
    if x < -w + 120 or y < -20 or x > sw - 120 or y > sh - 120:
        return None
    return geo


def probe_video(path):
    """Az ffprobe adatai a fájlról: méret, képkockasebesség, hossz, van-e kép és hang.
    None, ha az ffprobe nincs meg vagy a fájl nem olvasható."""
    exe = shutil.which("ffprobe")
    if not exe:
        return None
    try:
        res = subprocess.run([exe, "-v", "error", "-print_format", "json", "-show_streams",
                              "-show_format", path], capture_output=True, text=True, timeout=20)
        data = json.loads(res.stdout or "{}")
    except Exception:
        log_exc("probe_video")
        return None
    info = {"w": 0, "h": 0, "fps": 25.0, "dur": 0.0, "has_video": False, "has_audio": False}
    for st in data.get("streams", []):
        kind = st.get("codec_type")
        if kind == "audio":
            info["has_audio"] = True
        elif kind == "video" and not info["has_video"] \
                and not (st.get("disposition") or {}).get("attached_pic"):
            info["has_video"] = True
            w, h = int(st.get("width") or 0), int(st.get("height") or 0)
            rot = 0
            try:
                rot = int(float((st.get("tags") or {}).get("rotate", 0)))
                for sd in st.get("side_data_list") or []:
                    if "rotation" in sd:
                        rot = int(float(sd["rotation"]))
            except (TypeError, ValueError):
                rot = 0
            if abs(rot) % 180 == 90:
                w, h = h, w
            info["w"], info["h"] = w, h
            for key in ("avg_frame_rate", "r_frame_rate"):
                try:
                    a, b = str(st.get(key, "0/1")).split("/")
                    fps = float(a) / float(b)
                except (ValueError, ZeroDivisionError):
                    continue
                if 1 <= fps <= 240:
                    info["fps"] = fps
                    break
    try:
        info["dur"] = float((data.get("format") or {}).get("duration") or 0)
    except (TypeError, ValueError):
        pass
    return info


def fmt_speed(v):
    """0,5x, 1x, 1,25x: magyar tizedesvesszővel."""
    return (f"{v:g}").replace(".", ",") + "x"


def fmt_time(sec):
    sec = max(0, int(sec))
    h, rest = divmod(sec, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


# a lejátszó mindig sötét, a témától függetlenül; a színek szándékosan nincsenek a
# palettákban, így a témaváltás nem írja át őket
PL_VIDEO = "#000001"
PL_BAR = "#161618"
PL_BTN = "#262629"
PL_BTN_HOVER = "#37373b"
PL_TEXT = "#f2f2f4"
PL_DIM = "#9a9aa0"
PL_MIN_PIXELS = 640 * 360  # ennél kisebbre nem csökkentjük a képet, ha a gép lassú
PL_MAX_PIXELS = 2560 * 1440  # ennél nagyobb képet (4K) kisebben dekódolunk és nagyítunk
PL_SPEEDS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
PL_PIP_WIDTH = 360
PL_HIDE_MS = 2500  # teljes képernyőn ennyi mozdulatlanság után tűnnek el a vezérlők


class SeekBar(tk.Canvas):
    """Vékony, Apple stílusú csúszka (keresősáv, később a hangerő is): 0 és 1 közti érték."""

    def __init__(self, parent, on_seek, on_drag=None, height=26):
        super().__init__(parent, height=height, bg=parent.cget("bg"), highlightthickness=0,
                         bd=0, cursor="hand2")
        self._on_seek = on_seek
        self._on_drag = on_drag
        self.value = 0.0
        self._hover = False
        self._drag = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Map>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._move)
        self.bind("<ButtonRelease-1>", self._release)

    def _set_hover(self, flag):
        self._hover = flag
        self._draw()

    def _frac(self, x):
        w = max(1, self.winfo_width() - 12)
        return max(0.0, min(1.0, (x - 6) / w))

    def _press(self, e):
        self._drag = True
        self.value = self._frac(e.x)
        self._draw()
        if self._on_drag:
            self._on_drag(self.value)

    def _move(self, e):
        if self._drag:
            self.value = self._frac(e.x)
            self._draw()
            if self._on_drag:
                self._on_drag(self.value)

    def _release(self, e):
        if self._drag:
            self._drag = False
            self.value = self._frac(e.x)
            self._draw()
            self._on_seek(self.value)

    def set_value(self, v):
        """Kívülről állítva (lejátszás közben); húzás közben nem írjuk felül."""
        if self._drag:
            return
        v = max(0.0, min(1.0, v))
        if abs(v - self.value) > 0.0005:
            self.value = v
            self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20:
            return
        y = h / 2
        th = 5 if (self._hover or self._drag) else 3
        x0, x1 = 6, w - 6
        xv = x0 + (x1 - x0) * self.value
        self.create_line(x0, y, x1, y, width=th, fill="#4a4a4f", capstyle="round")
        if xv > x0:
            self.create_line(x0, y, xv, y, width=th, fill=PL_TEXT, capstyle="round")
        if self._hover or self._drag:
            self.create_oval(xv - 6, y - 6, xv + 6, y + 6, fill=PL_TEXT, outline="")


class AudioOut:
    """A hang: az ffmpeg PCM-et ad, a hangkártyára a sounddevice viszi. A lejátszási idő a
    ténylegesen kiadott hangmintákból számolódik, ez a lejátszó fő órája (a kép ehhez igazodik).
    A `make_stream` cserélhető, így a hangkártya nélkül is tesztelhető."""

    RATE = 44100
    CHANNELS = 2
    FRAME = 4  # 2 csatorna, 16 bit
    MAX_BUFFER = RATE * FRAME * 3  # legfeljebb 3 másodpercnyi hang vár a pufferben

    def __init__(self, path, start, make_stream=None):
        self.path = path
        self.volume = 1.0
        self.muted = False
        self.playing = False
        self.speed = 1.0
        self._lock = threading.Lock()
        self._buf = bytearray()
        self._consumed = 0          # kiadott képkockák (hangminták) száma az indulás óta
        self._start = 0.0
        self._eof = False
        self._proc = None
        self._stop = threading.Event()
        self._stream = None
        self._make_stream = make_stream or self._sounddevice_stream
        self.restart(start)

    @staticmethod
    def _sounddevice_stream(callback):
        return sounddevice.RawOutputStream(
            samplerate=AudioOut.RATE, channels=AudioOut.CHANNELS, dtype="int16",
            blocksize=1024, callback=callback)

    # ---------- dekódolás ----------
    def restart(self, start):
        """Új kezdőpont (tekerés): a hang az adott időponttól szól tovább."""
        self._kill()
        with self._lock:
            self._buf = bytearray()
            self._consumed = 0
            self._start = max(0.0, start)
            self._eof = False
        self._stop = threading.Event()
        stop = self._stop
        try:
            proc = subprocess.Popen(
                [shutil.which("ffmpeg") or "ffmpeg", "-v", "quiet", "-ss", f"{self._start:.3f}",
                 "-i", self.path, "-vn", "-sn"]
                + (["-af", f"atempo={self.speed:g}"] if abs(self.speed - 1.0) > 0.001 else [])
                + ["-f", "s16le", "-ac", str(self.CHANNELS), "-ar", str(self.RATE), "-"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        except Exception:
            log_exc("AudioOut ffmpeg indítás")
            with self._lock:
                self._eof = True
            return
        self._proc = proc
        threading.Thread(target=self._reader, args=(proc, stop), daemon=True).start()

    def _reader(self, proc, stop):
        try:
            while not stop.is_set():
                with self._lock:
                    full = len(self._buf) >= self.MAX_BUFFER
                if full:
                    time.sleep(0.02)
                    continue
                chunk = proc.stdout.read(16384)
                if not chunk:
                    break
                with self._lock:
                    if stop.is_set():
                        return
                    self._buf += chunk
        except Exception:
            pass
        with self._lock:
            if not stop.is_set():
                self._eof = True

    def _kill(self):
        self._stop.set()
        proc, self._proc = self._proc, None
        if proc is not None:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass
            try:
                proc.stdout.close()
            except Exception:
                pass

    # ---------- kimenet ----------
    def _callback(self, outdata, frames, _time, _status):
        need = frames * self.FRAME
        data = b""
        if self.playing:
            with self._lock:
                data = bytes(self._buf[:need])
                del self._buf[:len(data)]
                self._consumed += len(data) // self.FRAME
            vol = 0.0 if self.muted else self.volume
            if data and vol < 0.999:
                arr = array.array("h")
                arr.frombytes(data[:len(data) // 2 * 2])
                if vol <= 0.001:
                    data = bytes(len(data))
                else:
                    data = array.array("h", [int(x * vol) for x in arr]).tobytes()
        if len(data) < need:
            data += bytes(need - len(data))  # hiány vagy szünet: csend
        outdata[:need] = data

    def start_stream(self):
        """A hangkártya megnyitása (az első lejátszáskor). False, ha nem sikerült."""
        if self._stream is not None:
            return True
        try:
            self._stream = self._make_stream(self._callback)
            self._stream.start()
            return True
        except Exception:
            log_exc("AudioOut stream")
            self._stream = None
            return False

    def position(self):
        lat = 0.0
        try:
            lat = float(self._stream.latency) if self._stream is not None else 0.0
        except Exception:
            pass
        with self._lock:
            return max(self._start, self._start + (self._consumed / self.RATE - lat) * self.speed)

    def finished(self):
        """A fájl hangja véget ért és a puffer is kiürült."""
        with self._lock:
            return self._eof and not self._buf

    def close(self):
        self.playing = False
        self._kill()
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                log_exc("AudioOut close")


def extract_cover(path):
    """A fájlba ágyazott borítókép (mp3), PNG bájtokban; None, ha nincs."""
    exe = shutil.which("ffmpeg")
    if not exe:
        return None
    try:
        res = subprocess.run([exe, "-v", "quiet", "-i", path, "-an", "-frames:v", "1",
                              "-f", "image2pipe", "-vcodec", "png", "-"],
                             capture_output=True, timeout=10)
        return res.stdout or None
    except Exception:
        return None


class SpeakerButton(tk.Canvas):
    """Hangszóró ikon: kattintásra némít és visszahangosít. A szint (0 néma, 1 halk, 2 hangos)
    az ikon hullámait változtatja."""

    def __init__(self, parent, command, size=32):
        super().__init__(parent, width=size, height=size, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2")
        self._command = command
        self.level = 2
        self._hover = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Map>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self._command())

    def _set_hover(self, flag):
        self._hover = flag
        self._draw()

    def set_level(self, level):
        if level != self.level:
            self.level = level
            self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8:
            return
        cx, cy = w / 2, h / 2
        color = "#ffffff" if self._hover else PL_TEXT
        # hangszóró test
        self.create_polygon(cx - 9, cy - 3, cx - 5, cy - 3, cx, cy - 8, cx, cy + 8,
                            cx - 5, cy + 3, cx - 9, cy + 3, fill=color, outline=color)
        if self.level == 0:
            self.create_line(cx + 4, cy - 4, cx + 11, cy + 4, fill=color, width=2,
                             capstyle="round")
            self.create_line(cx + 4, cy + 4, cx + 11, cy - 4, fill=color, width=2,
                             capstyle="round")
            return
        for i in range(self.level):
            r = 5 + i * 5
            self.create_arc(cx + 2 - r, cy - r, cx + 2 + r, cy + r, start=-45, extent=90,
                            style="arc", outline=color, width=2)


class FullscreenButton(tk.Canvas):
    """Teljes képernyő ikon (négy sarok); aktív állapotban befelé néző sarkok."""

    def __init__(self, parent, command, size=32):
        super().__init__(parent, width=size, height=size, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2")
        self._command = command
        self.active = False
        self._hover = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Map>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self._command())

    def _set_hover(self, flag):
        self._hover = flag
        self._draw()

    def set_active(self, flag):
        self.active = flag
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8:
            return
        cx, cy = w / 2, h / 2
        color = "#ffffff" if self._hover else PL_TEXT
        d, a = 8, 5  # a sarkok távolsága a középtől, és a szárak hossza
        for sx in (-1, 1):
            for sy in (-1, 1):
                if self.active:
                    ox, oy = cx + sx * 3, cy + sy * 3
                    pts = (ox + sx * a, oy, ox, oy, ox, oy + sy * a)
                else:
                    ox, oy = cx + sx * d, cy + sy * d
                    pts = (ox - sx * a, oy, ox, oy, ox, oy - sy * a)
                self.create_line(*pts, fill=color, width=2, capstyle="round", joinstyle="round")


class PipButton(tk.Canvas):
    """Kis ablak (PiP) ikon: nagy keret, benne egy kis, kitöltött ablak a sarokban."""

    def __init__(self, parent, command, size=32):
        super().__init__(parent, width=size, height=size, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2")
        self._command = command
        self.active = False
        self._hover = False
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Map>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda e: self._command())

    def _set_hover(self, flag):
        self._hover = flag
        self._draw()

    def set_active(self, flag):
        self.active = flag
        self._draw()

    def _draw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 8:
            return
        cx, cy = w / 2, h / 2
        color = "#ffffff" if self._hover else PL_TEXT
        self.create_rectangle(cx - 11, cy - 8, cx + 11, cy + 8, outline=color, width=2)
        if self.active:
            self.create_rectangle(cx - 6, cy - 4, cx + 6, cy + 4, fill=color, outline=color)
        else:
            self.create_rectangle(cx + 1, cy + 0, cx + 9, cy + 6, fill=color, outline=color)


class VideoPlayer(tk.Toplevel):
    """Egyszerű beépített lejátszó videóhoz és hanganyaghoz. Az ffmpeg adja a képkockákat és a
    hangot. Ha van hang, annak ideje a fő óra (a kép ehhez igazodik), különben falióra."""

    def __init__(self, parent, path, title, info, cover=None, make_stream=None, autoplay=True,
                 volume=1.0, on_volume=None, geometry=None, on_geometry=None):
        super().__init__(parent)
        self.withdraw()
        self.path, self.info = path, info
        self.title_text = title
        self.has_video = info["has_video"]
        self.fps = info["fps"]
        self.dur = info["dur"]
        self.title(title)
        self.configure(bg=PL_VIDEO)
        self.minsize(480, 320)
        self._alive = True
        self._proc = None
        self._gen = 0
        self._q = queue.Queue(maxsize=4)
        self._stop = threading.Event()
        self._start = 0.0          # a mostani képdekódolás kezdőideje
        self._base_pos = 0.0
        self._base_wall = 0.0
        self._awaiting = True      # falióránál az első képkockáig áll az óra
        self._pending = None
        self._want_one = True
        self.playing = False
        self._size = (0, 0)
        self._disp = (0, 0)
        self._photo = None
        self._photo_size = None
        self._frame_item = None
        self._frame_pos = None
        self._draw_ms = None        # a kirajzolás átlagos ideje (ms), a hibakereséshez
        self._pix_cap = None        # ha a gép nem bírja a kép méretét: legfeljebb ennyi képpont
        self._cost_n = 0            # a kirajzolás mért költsége a mostani méretnél
        self._cost_ms = 0.0
        self._adapt_now = False
        self._resize_job = None
        self._dragging = False
        self._ended = False
        self._cover_src = None
        if not self.has_video:
            data = cover or extract_cover(path)
            if data and HAS_PIL:
                try:
                    self._cover_src = Image.open(io.BytesIO(data)).convert("RGB")
                except Exception:
                    self._cover_src = None
        self.volume = max(0.0, min(1.0, volume))
        self.muted = False
        self.speed = 1.0
        self._on_volume = on_volume
        self._on_geometry = on_geometry
        self._geo_job = None
        self._geo0 = None  # a nyitáskori ablakhelyzet: csak a felhasználó változtatását mentjük
        self._click_job = None
        self._flash_job = None
        self.audio = None
        if info["has_audio"] and (HAS_AUDIO or make_stream is not None):
            self.audio = AudioOut(path, 0.0, make_stream)
            self.audio.volume = self.volume

        self.canvas = tk.Canvas(self, bg=PL_VIDEO, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        bar = tk.Frame(self, bg=PL_BAR, padx=14, pady=8)
        bar.pack(fill="x", side="bottom")
        self.bar = bar
        self.fullscreen = False
        self._hide_job = None
        self._bar_hover = False
        self._normal_geo = None
        self.play_btn = RoundButton(bar, "▶", self.toggle, width=44, height=32, bg=PL_BTN,
                                    fg=PL_TEXT, hover=PL_BTN_HOVER, font=(FONT_FAMILY, 14))
        self.cur_lbl = tk.Label(bar, text="0:00", bg=PL_BAR, fg=PL_TEXT, width=5, anchor="e",
                                font=(FONT_FAMILY, 12))
        self.total_lbl = tk.Label(bar, text=fmt_time(self.dur), bg=PL_BAR, fg=PL_DIM,
                                  width=5, anchor="w", font=(FONT_FAMILY, 12))
        self.speaker = SpeakerButton(bar, self.toggle_mute)
        self.vol_bar = SeekBar(bar, self._set_volume_frac, self._set_volume_frac)
        self.vol_bar.configure(width=84)
        self.vol_bar.value = self.volume
        self.fs_btn = FullscreenButton(bar, self.toggle_fullscreen)
        self.pip_btn = PipButton(bar, self.toggle_pip)
        self.speed_btn = RoundButton(bar, fmt_speed(1.0), self._speed_menu, width=52, height=32,
                                     bg=PL_BTN, fg=PL_TEXT, hover=PL_BTN_HOVER,
                                     font=(FONT_FAMILY, 12))
        self.seek = SeekBar(bar, self._seek_frac, self._drag_preview)
        self.note = None
        self.note_lbl = None
        if info["has_audio"] and self.audio is None and self.has_video:
            self.note = t("A hang nem elérhető")
            self.note_lbl = tk.Label(bar, text=self.note, bg=PL_BAR, fg=PL_DIM,
                                     font=(FONT_FAMILY, 11))
        self.pip = False
        self._pip_restore = None
        self._layout_bar(False)
        self._refresh_volume_ui()

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Configure>", self._on_configure)
        self.bind("<space>", lambda e: self.toggle())
        self.bind("<Left>", lambda e: self.skip(-5))
        self.bind("<Right>", lambda e: self.skip(5))
        self.bind("<Up>", lambda e: self.change_volume(0.05))
        self.bind("<Down>", lambda e: self.change_volume(-0.05))
        self.bind("<m>", lambda e: self.toggle_mute())
        for seq, d in (("<less>", -1), ("<bracketleft>", -1), ("<greater>", 1),
                       ("<bracketright>", 1)):
            self.bind(seq, lambda e, d=d: self.change_speed(d))
        self.bind("<Escape>", self._on_escape)
        self.bind("<f>", lambda e: self.toggle_fullscreen())
        self.bind("<Motion>", lambda e: self._show_controls())
        bar.bind("<Enter>", lambda e: self._set_bar_hover(True))
        bar.bind("<Leave>", lambda e: self._set_bar_hover(False))
        self.bind(f"<{MOD_KEY}-w>", lambda e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

        # induló méret: a videó mérete, de legfeljebb a képernyő 80 százaléka
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        if self.has_video:
            vw, vh = max(info["w"], 16), max(info["h"], 9)
            scale = min(1.0, sw * 0.8 / vw, (sh * 0.8 - 56) / vh)
            w, h = max(480, int(vw * scale)), max(320, int(vh * scale) + 56)
        else:
            w, h = 520, 440
        x = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
        y = parent.winfo_rooty() + 20
        self.geometry(usable_geometry(geometry, sw, sh) or f"{w}x{h}+{max(x, 0)}+{max(y, 30)}")
        self.deiconify()
        self.after(900, self._set_geo_baseline)
        self.focus_set()
        self.after(20, self._tick)
        if autoplay:
            self.after(400, self.play)

    # ---------- idő ----------
    def _pos(self):
        if self.audio is not None:
            pos = self.audio.position()
            return min(self.dur, pos) if self.dur else pos
        if self.playing and not self._awaiting:
            return min(self.dur or 1e9,
                       self._base_pos + (time.time() - self._base_wall) * self.speed)
        return self._base_pos

    # ---------- kép dekódolása ----------
    def _fit(self):
        cw, ch = max(self.canvas.winfo_width(), 2), max(self.canvas.winfo_height(), 2)
        vw, vh = max(self.info["w"], 1), max(self.info["h"], 1)
        s = min(cw / vw, ch / vh)
        w, h = max(2, int(vw * s) // 2 * 2), max(2, int(vh * s) // 2 * 2)
        if self._pix_cap and w * h > self._pix_cap:
            k = (self._pix_cap / (w * h)) ** 0.5
            w, h = max(2, int(w * k) // 2 * 2), max(2, int(h * k) // 2 * 2)
        return w, h

    @staticmethod
    def _decode_size(disp):
        """A kép méretét az ffmpeg állítja pontosan a megjelenítési méretre (a Pythonban a
        nagyítás lassú volna). Csak a 4K körüli méretet korlátozzuk, ott kirajzoláskor nagyítunk."""
        w, h = disp
        k = (PL_MAX_PIXELS / (w * h)) ** 0.5
        if k >= 1:
            return disp
        return max(2, int(w * k) // 2 * 2), max(2, int(h * k) // 2 * 2)

    def _start_decoder(self, at):
        self._kill_decoder()
        self._cost_n = 0
        self._disp = self._fit()
        self._size = self._decode_size(self._disp)
        ow, oh = self._size
        self._gen += 1
        gen = self._gen
        self._start = max(0.0, at)
        self._awaiting = True
        self._pending = None
        self._want_one = True
        self._base_pos = self._start
        self._stop = threading.Event()
        stop = self._stop
        try:
            proc = subprocess.Popen(
                [shutil.which("ffmpeg") or "ffmpeg", "-v", "quiet", "-ss", f"{self._start:.3f}",
                 "-i", self.path, "-an", "-sn", "-vf", f"scale={ow}:{oh}:flags=bilinear",
                 "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        except Exception:
            log_exc("VideoPlayer ffmpeg indítás")
            self._proc = None
            return
        self._proc = proc
        threading.Thread(target=self._reader, args=(proc, gen, stop, ow * oh * 3),
                         daemon=True).start()

    def _reader(self, proc, gen, stop, size):
        idx = 0
        try:
            while not stop.is_set():
                data = proc.stdout.read(size)
                if len(data) < size:
                    break
                while not stop.is_set():
                    try:
                        self._q.put((gen, idx, data), timeout=0.1)
                        break
                    except queue.Full:
                        continue
                idx += 1
        except Exception:
            pass
        while not stop.is_set():
            try:
                self._q.put((gen, -1, None), timeout=0.1)
                break
            except queue.Full:
                continue

    def _kill_decoder(self):
        self._stop.set()
        proc, self._proc = self._proc, None
        if proc is not None:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except Exception:
                pass
            try:
                proc.stdout.close()
            except Exception:
                pass
        while True:
            try:
                self._q.get_nowait()
            except queue.Empty:
                break
        self._video_eof_gen = None

    # ---------- vezérlés ----------
    def toggle(self):
        if self.playing:
            self.pause()
        else:
            self.play()

    def _set_icon(self, text):
        self.play_btn._text = text
        self.play_btn._draw()

    def play(self):
        if not self._alive:
            return
        if self._ended or (self.dur and self._pos() >= self.dur - 0.05):
            self.seek_to(0.0)  # a végén újrakezdi
        elif self.has_video and self._proc is None:
            self._start_decoder(self._pos())
        self._ended = False
        self.playing = True
        self._base_wall = time.time()
        if self.audio is not None:
            if not self.audio.start_stream():
                self.audio.close()
                self.audio = None
                self._base_pos = self._start
                self.note = t("A hang nem elérhető")
            else:
                self.audio.playing = True
        self._set_icon("❚❚")

    def pause(self):
        self._base_pos = self._pos()
        self.playing = False
        if self.audio is not None:
            self.audio.playing = False
        self._set_icon("▶")

    def seek_to(self, sec):
        sec = max(0.0, min(sec, max(0.0, self.dur - 0.1)) if self.dur else sec)
        self._ended = False
        if self.audio is not None:
            self.audio.restart(sec)
        if self.has_video:
            self._start_decoder(sec)
        self._base_pos = sec
        self._base_wall = time.time()
        self._show_time(sec)

    def _layout_bar(self, compact):
        """A vezérlősáv elemeinek elrendezése. Kis (PiP) ablakban csak lejátszás, keresősáv
        és a visszaváltó gomb marad."""
        for w in (self.play_btn, self.cur_lbl, self.seek, self.total_lbl, self.speaker,
                  self.vol_bar, self.fs_btn, self.pip_btn, self.note_lbl, self.speed_btn):
            if w is not None:
                w.pack_forget()
        self.play_btn.pack(side="left")
        if not compact:
            self.cur_lbl.pack(side="left", padx=(12, 4))
        if self.has_video:
            if not compact:
                self.fs_btn.pack(side="right", padx=(8, 0))
            self.pip_btn.pack(side="right", padx=(8, 0))
        if not compact:
            self.total_lbl.pack(side="right", padx=(4, 0))
            if self.note_lbl is not None:
                self.note_lbl.pack(side="right", padx=(8, 0))
            self.speed_btn.pack(side="right", padx=(10, 0))
            if self.info["has_audio"] and self.audio is not None:
                self.vol_bar.pack(side="right", padx=(0, 2))
                self.speaker.pack(side="right", padx=(10, 0))
        self.seek.pack(side="left", fill="x", expand=True, padx=(8 if compact else 0, 0))

    # ---------- kis ablak (PiP) ----------
    def toggle_pip(self):
        if not self.has_video:
            return
        if self.pip:
            self.exit_pip()
        else:
            self.enter_pip()

    def enter_pip(self):
        """Kis, mindig felül lévő ablak a sarokban; a vezérlők egérmozdításra jönnek elő."""
        if self.pip or not self._alive:
            return
        if self.fullscreen:
            self.exit_fullscreen()
        self._pip_restore = self.geometry()
        w = PL_PIP_WIDTH
        h = max(120, int(w * max(self.info["h"], 1) / max(self.info["w"], 1)))
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = max(0, sw - w - 24), max(0, sh - h - 110)
        self.pip = True
        self.minsize(220, 124)
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass
        self.geometry(f"{w}x{h}+{x}+{y}")
        self._layout_bar(True)
        self.bar.configure(padx=8, pady=6)
        self.bar.pack_forget()
        self.bar.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        self.bar.lift()
        self.pip_btn.set_active(True)
        self._show_controls()

    def exit_pip(self):
        if not self.pip:
            return
        self.pip = False
        self._cancel_hide()
        try:
            self.attributes("-topmost", False)
        except tk.TclError:
            pass
        self.bar.place_forget()
        self.bar.configure(padx=14, pady=8)
        self._layout_bar(False)
        self.bar.pack(fill="x", side="bottom")
        self.canvas.configure(cursor="")
        self.pip_btn.set_active(False)
        self.minsize(480, 320)
        if self._pip_restore:
            geo = self._pip_restore
            self.after(50, lambda: self._alive and self.geometry(geo))

    # ---------- teljes képernyő ----------
    def _on_escape(self, _e=None):
        if self.fullscreen:
            self.exit_fullscreen()
        elif self.pip:
            self.exit_pip()
        else:
            self.close()

    def toggle_fullscreen(self):
        if not self.has_video:
            return
        if self.fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self):
        if self.fullscreen or self.pip or not self._alive:
            return
        self._normal_geo = self.geometry()
        try:
            self.attributes("-fullscreen", True)
        except tk.TclError:
            log_exc("VideoPlayer fullscreen")
            return
        self.fullscreen = True
        self.fs_btn.set_active(True)
        # a vezérlősáv a kép fölé úszik, a kép kitölti az egész képernyőt
        self.bar.pack_forget()
        self.bar.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        self.bar.lift()
        self._show_controls()

    def exit_fullscreen(self):
        if not self.fullscreen:
            return
        self.fullscreen = False
        self._cancel_hide()
        try:
            self.attributes("-fullscreen", False)
        except tk.TclError:
            pass
        self.bar.place_forget()
        self.bar.pack(fill="x", side="bottom")
        self.canvas.configure(cursor="")
        self.fs_btn.set_active(False)
        if self._normal_geo:
            self.after(50, lambda: self._alive and self.geometry(self._normal_geo))

    def _set_bar_hover(self, flag):
        self._bar_hover = flag
        if flag:
            self._cancel_hide()
        else:
            self._show_controls()

    def _cancel_hide(self):
        if self._hide_job is not None:
            try:
                self.after_cancel(self._hide_job)
            except tk.TclError:
                pass
            self._hide_job = None

    def _show_controls(self):
        """Teljes képernyőn egérmozdulatra előjön a sáv, mozdulatlanság után eltűnik."""
        if not (self.fullscreen or self.pip):
            return
        self.bar.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")
        self.bar.lift()
        self.canvas.configure(cursor="")
        self._cancel_hide()
        self._hide_job = self.after(PL_HIDE_MS, self._hide_controls)

    def _hide_controls(self):
        self._hide_job = None
        if not ((self.fullscreen or self.pip) and self._alive):
            return
        if self._bar_hover or self._dragging or not self.playing:
            self._hide_job = self.after(PL_HIDE_MS, self._hide_controls)
            return
        self.bar.place_forget()
        self.canvas.configure(cursor="none")

    # ---------- sebesség ----------
    def _speed_menu(self):
        menu = tk.Menu(self, tearoff=0)
        var = tk.DoubleVar(value=self.speed)
        for v in PL_SPEEDS:
            label = fmt_speed(v) + (t("  (normál)") if v == 1.0 else "")
            menu.add_radiobutton(label=label, variable=var, value=v,
                                 command=lambda v=v: self.set_speed(v))
        b = self.speed_btn
        try:
            menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() - 26 * len(PL_SPEEDS) - 8)
        finally:
            menu.grab_release()

    def set_speed(self, v):
        """Lejátszási sebesség. A hang az ffmpeg atempo szűrőjével gyorsul (a hangmagasság marad),
        a kép a hang órájához igazodik."""
        v = min(PL_SPEEDS[-1], max(PL_SPEEDS[0], float(v)))
        if abs(v - self.speed) < 1e-6:
            return
        cur = self._pos()
        self.speed = v
        self.speed_btn._text = fmt_speed(v)
        self.speed_btn._draw()
        if self.audio is not None:
            self.audio.speed = v
            self.audio.restart(cur)
        else:
            self._base_pos = cur
            self._base_wall = time.time()
        self._flash(fmt_speed(v), None)

    def change_speed(self, direction):
        i = min(range(len(PL_SPEEDS)), key=lambda k: abs(PL_SPEEDS[k] - self.speed))
        j = max(0, min(len(PL_SPEEDS) - 1, i + direction))
        self.set_speed(PL_SPEEDS[j])

    # ---------- ablak helyének megjegyzése ----------
    def _set_geo_baseline(self):
        if self._alive and not (self.fullscreen or self.pip):
            self._geo0 = self.geometry()

    def _report_geometry(self, geo=None):
        """A felhasználó által megváltoztatott ablakhelyzetet jelentjük az appnak."""
        self._geo_job = None
        if not self._alive or self._on_geometry is None or self._geo0 is None:
            return
        if geo is None:
            if self.fullscreen or self.pip:
                return
            geo = self.geometry()
        if geo and geo != self._geo0:
            self._on_geometry("video" if self.has_video else "audio", geo)

    # ---------- kattintás, ugrás, hangerő ----------
    def _on_click(self, _e):
        """Egy kattintás: lejátszás/szünet. Rövid késleltetéssel, hogy a dupla kattintást
        meg lehessen különböztetni."""
        if self._click_job is not None:
            self.after_cancel(self._click_job)
        self._click_job = self.after(350, self._click_toggle)

    def _click_toggle(self):
        self._click_job = None
        if self._alive:
            self.toggle()
            self._toggled_at = time.time()

    def _on_double_click(self, e):
        """Dupla kattintás a kép bal felén: 15 mp vissza, a jobb felén: 15 mp előre."""
        if self._click_job is not None:
            self.after_cancel(self._click_job)
            self._click_job = None
        elif time.time() - getattr(self, "_toggled_at", 0) < 0.8:
            self.toggle()  # lassú dupla kattintás: az első kattintás váltását visszavonjuk
            self._toggled_at = 0
        forward = e.x >= self.canvas.winfo_width() / 2
        self.skip(15 if forward else -15, flash=True)

    def skip(self, delta, flash=False):
        cur = self._pos()
        target = max(0.0, cur + delta)
        if self.dur:
            target = min(target, max(0.0, self.dur - 0.2))
        self.seek_to(target)
        if flash or abs(delta) >= 15:
            self._flash(t('{x}{x2} mp').format(x='+' if delta > 0 else '−', x2=abs(int(delta))), delta > 0)

    def _flash(self, text, right):
        """Rövid jelzés a képen ugrásnál."""
        c = self.canvas
        c.delete("flash")
        cw, ch = c.winfo_width(), c.winfo_height()
        cx = cw / 2 if right is None else cw * (0.78 if right else 0.22)
        c.create_oval(cx - 46, ch / 2 - 46, cx + 46, ch / 2 + 46, fill="#202022",
                      outline="", tags="flash")
        c.create_text(cx, ch / 2, text=text, fill=PL_TEXT, tags="flash",
                      font=(FONT_FAMILY, 15, "bold"))
        if self._flash_job is not None:
            self.after_cancel(self._flash_job)
        self._flash_job = self.after(650, lambda: self.canvas.delete("flash"))

    def _apply_volume(self):
        if self.audio is not None:
            self.audio.volume = self.volume
            self.audio.muted = self.muted
        self._refresh_volume_ui()

    def _refresh_volume_ui(self):
        eff = 0.0 if self.muted else self.volume
        self.speaker.set_level(0 if eff <= 0.001 else (1 if eff < 0.5 else 2))
        self.vol_bar.set_value(eff)

    def _set_volume_frac(self, frac):
        self.volume = max(0.0, min(1.0, frac))
        self.muted = self.volume <= 0.001
        self._apply_volume()
        if self._on_volume and self.volume > 0.001:
            self._on_volume(self.volume)

    def change_volume(self, delta):
        self.volume = max(0.0, min(1.0, self.volume + delta))
        self.muted = self.volume <= 0.001
        self.vol_bar.value = self.volume
        self._apply_volume()
        if self._on_volume and self.volume > 0.001:
            self._on_volume(self.volume)

    def toggle_mute(self):
        if self.muted and self.volume <= 0.001:
            self.volume = 0.5  # 0-ról némítás megszüntetése: közepes hangerő
        self.muted = not self.muted
        self._apply_volume()

    def _seek_frac(self, frac):
        self._dragging = False
        self.seek_to(frac * self.dur)

    def _drag_preview(self, frac):
        self._dragging = True
        self.cur_lbl.configure(text=fmt_time(frac * self.dur))

    def _show_time(self, sec):
        self.cur_lbl.configure(text=fmt_time(sec))
        if self.dur:
            self.seek.set_value(sec / self.dur)

    # ---------- megjelenítés ----------
    def _on_configure(self, _e):
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(200, self._resized)
        if self._geo0 is not None and not (self.fullscreen or self.pip):
            if self._geo_job is not None:
                self.after_cancel(self._geo_job)
            self._geo_job = self.after(1000, self._report_geometry)

    def _resized(self):
        self._resize_job = None
        if not self._alive:
            return
        if not self.has_video:
            self._draw_cover()
            return
        if self._proc is None and self._size == (0, 0):
            self._start_decoder(0.0)  # első megjelenés: az első képkocka
        elif self._fit() != self._disp:
            self._start_decoder(self._pos())

    def _draw_cover(self):
        """Hanganyagnál: borítókép (ha van), különben egy hangjegy, alatta a cím."""
        c = self.canvas
        cw, ch = c.winfo_width(), c.winfo_height()
        c.delete("all")
        side = max(80, min(cw, ch) - 130)
        top = (ch - side - 60) // 2
        if self._cover_src is not None:
            img = self._cover_src.copy()
            img.thumbnail((side, side))
            self._photo = ImageTk.PhotoImage(img)
            c.create_image(cw // 2, top + side // 2, image=self._photo)
        else:
            x0, y0 = cw // 2 - side // 2, top
            round_rect(c, x0, y0, x0 + side, y0 + side, 18, fill=PL_BTN, outline=PL_BTN)
            c.create_text(cw // 2, y0 + side // 2, text="♪", fill=PL_DIM,
                          font=(FONT_FAMILY, max(30, side // 2)))
        c.create_text(cw // 2, top + side + 34, text=self.title_text, fill=PL_TEXT,
                      width=max(100, cw - 60), font=(FONT_FAMILY, 14, "bold"))

    def _draw_frame(self, data):
        """Egy képkocka kirajzolása. Teljes képernyőn ez volt a szűk keresztmetszet: az új
        kép és vászonelem minden kockánál sokkal lassabb, mint a meglévő képbe írás, ezért
        ugyanazt a képet és vászonelemet frissítjük, amíg a méret nem változik."""
        t0 = time.perf_counter()
        ow, oh = self._size
        img = Image.frombytes("RGB", (ow, oh), data)
        if (ow, oh) != self._disp and self._disp[0] > 0:
            img = img.resize(self._disp, Image.BILINEAR)
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if self._photo is not None and self._photo_size == img.size and self._frame_item \
                and self.canvas.type(self._frame_item) == "image":
            self._photo.paste(img)
            if self._frame_pos != (cw // 2, ch // 2):
                self.canvas.coords(self._frame_item, cw // 2, ch // 2)
        else:
            self._photo = ImageTk.PhotoImage(img)
            self._photo_size = img.size
            self.canvas.delete("frame")
            self._frame_item = self.canvas.create_image(cw // 2, ch // 2, image=self._photo,
                                                        tags="frame")
            self.canvas.tag_lower("frame")
        self._frame_pos = (cw // 2, ch // 2)
        if self.playing:
            self.canvas.update_idletasks()  # a tényleges rajzolás itt történik, így mérhető
        ms = (time.perf_counter() - t0) * 1000
        self._draw_ms = ms if self._draw_ms is None else self._draw_ms * 0.9 + ms * 0.1
        if self.playing:
            self._note_cost(ms)

    def _note_cost(self, ms):
        """Ha egy kocka kirajzolása tartósan tovább tart, mint a kockák közti idő (pl. Mac
        teljes képernyőn), kisebb képet kérünk, hogy a videó sima maradjon.
        A kirajzolás ideje a kép területével arányos."""
        self._cost_n += 1
        self._cost_ms = ms if self._cost_n == 1 else self._cost_ms * 0.85 + ms * 0.15
        if self._cost_n < 20:
            return False
        budget = 1000.0 / min(60.0, max(1.0, self.fps) * max(self.speed, 1.0)) * 0.8
        if self._cost_ms <= budget:
            return False
        area = self._disp[0] * self._disp[1]
        if area <= PL_MIN_PIXELS:
            return False
        cap = int(area * budget / self._cost_ms)
        self._pix_cap = max(PL_MIN_PIXELS, cap)
        self._adapt_now = True
        return True

    def _tick(self):
        if not self._alive:
            return
        try:
            shown = None
            video_done = not self.has_video
            while self.has_video:
                if self._pending is None:
                    try:
                        gen, idx, data = self._q.get_nowait()
                    except queue.Empty:
                        break
                    if gen != self._gen:
                        continue
                    if idx < 0:
                        video_done = True
                        self._video_eof_gen = gen
                        break
                    self._pending = (idx, data)
                    if self._awaiting:
                        self._awaiting = False
                        if self.audio is None:
                            self._base_pos = self._start + idx / self.fps
                            self._base_wall = time.time()
                idx, data = self._pending
                if self.playing:
                    due = self._start + idx / self.fps <= self._pos() + 0.001
                else:
                    due = self._want_one
                if due:
                    shown = data
                    self._pending = None
                    self._want_one = False
                    if not self.playing:
                        break
                else:
                    break
            if self.has_video and getattr(self, "_video_eof_gen", None) == self._gen:
                video_done = True
            if shown is not None:
                self._draw_frame(shown)
                if self._adapt_now:
                    self._adapt_now = False
                    self._cost_n = 0
                    self._start_decoder(self._pos())
            if self.playing and video_done and self._pending is None:
                audio_done = self.audio is None or self.audio.finished() \
                    or (self.dur and self._pos() >= self.dur - 0.05)
                if audio_done:
                    self._finish()
            elif self.playing and not self.has_video and self.audio is not None \
                    and self.audio.finished():
                self._finish()
            if not self._dragging:
                self._show_time(self._pos())
        except Exception:
            log_exc("VideoPlayer._tick")
        # videó közben sűrűbben nézünk rá: a 15 ms + a rajzolás ideje 60 fps-nél már kockát dobott
        self.after(5 if (self.playing and self.has_video) else 15, self._tick)

    def _finish(self):
        self.pause()
        self._ended = True
        self._base_pos = self.dur or self._base_pos
        self._show_time(self._base_pos)

    def close(self):
        if not self._alive:
            return
        geo = self._normal_geo if self.fullscreen else (self._pip_restore if self.pip
                                                         else self.geometry())
        if self._geo_job is not None:
            try:
                self.after_cancel(self._geo_job)
            except tk.TclError:
                pass
        if self._geo0 is not None and self._on_geometry is not None and geo \
                and geo != self._geo0:
            self._on_geometry("video" if self.has_video else "audio", geo)
        self._alive = False
        self.playing = False
        for job in (self._click_job, self._flash_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        self._cancel_hide()
        self._kill_decoder()
        if self.audio is not None:
            self.audio.close()
        try:
            self.destroy()
        except tk.TclError:
            pass


class MpvIpc:
    """Az mpv vezérlőcsatornája (Unix: socket, Windows: névvel ellátott cső). Csak
    tulajdonságokat olvasunk, a hangerő megjegyzéséhez."""

    def __init__(self, path, tries=50):
        self._f = self._sock = None
        self._buf = b""
        self._id = 0
        for _ in range(tries):
            try:
                if is_win():
                    self._f = open(path, "r+b", buffering=0)
                else:
                    import socket
                    self._sock = socket.socket(socket.AF_UNIX)
                    self._sock.settimeout(0.5)
                    self._sock.connect(path)
                return
            except OSError:
                self._sock = None
                time.sleep(0.1)
        raise OSError("az mpv vezérlőcsatornája nem érhető el")

    def _read(self):
        if self._f is not None:
            return self._f.read(65536)
        return self._sock.recv(65536)

    def get(self, prop, timeout=1.0):
        self._id += 1
        msg = (json.dumps({"command": ["get_property", prop], "request_id": self._id})
               + "\n").encode()
        if self._f is not None:
            self._f.write(msg)
        else:
            self._sock.sendall(msg)
        t0 = time.time()
        while time.time() - t0 < timeout:
            while b"\n" in self._buf:
                line, self._buf = self._buf.split(b"\n", 1)
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("request_id") == self._id:
                    return d.get("data") if d.get("error") == "success" else None
            try:
                chunk = self._read()
            except OSError:
                chunk = b""
            if not chunk:
                if self._sock is None:
                    return None
                continue
            self._buf += chunk
        return None

    def close(self):
        for h in (self._f, self._sock):
            try:
                if h is not None:
                    h.close()
            except OSError:
                pass


class MpvPlayer:
    """Lejátszó az mpv-vel (külön folyamat, saját ablak). Az app a fájlt átadja neki, az mpv
    gyors, GPU-s kirajzolással játssza le, a HDR is helyesen jelenik meg.
    Billentyűk: szóköz, nyilak (±5 mp, hangerő), m, [ ], f, p (kép a képben), Esc, q."""

    SPEEDS = " ".join(str(v) for v in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0))

    def __init__(self, parent, path, title, audio_only=False, volume=1.0, on_volume=None,
                 geometry=None):
        self.parent = parent
        self._on_volume = on_volume
        self._proc = None
        self._volume = volume
        self._alive = False
        self._sock_path = self._ipc_path = None
        mpv = shutil.which("mpv")
        if not mpv:
            raise FileNotFoundError("mpv")
        self._conf = tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False,
                                                 encoding="utf-8")
        self._conf.write(
            "SPACE cycle pause\nLEFT seek -5\nRIGHT seek 5\nUP add volume 5\n"
            "DOWN add volume -5\nm cycle mute\nf cycle fullscreen\nESC set fullscreen no\n"
            f"] cycle-values speed {self.SPEEDS}\n[ cycle-values !reverse speed {self.SPEEDS}\n"
            "p cycle-values window-scale 0.3 1.0 ; cycle ontop\n")
        self._conf.close()
        args = [mpv, "--no-config", f"--input-conf={self._conf.name}", "--keep-open=yes",
                "--really-quiet", f"--force-media-title={title}", "--hwdec=auto-safe",
                f"--volume={max(0, min(130, round(volume * 100)))}",
                "--autofit-larger=90%x90%", "--osd-font-size=64", "--sub-font-size=64",
                "--script-opts=osc-scalewindowed=1.5,osc-scalefullscreen=1.5,"
                "osc-hidetimeout=4000,osc-fadeduration=400"]
        if audio_only:
            args += ["--force-window=yes", "--audio-display=embedded-first",
                     "--geometry=560x560"]
        geo = None
        if geometry and not audio_only:
            try:
                geo = usable_geometry(geometry, parent.winfo_screenwidth(),
                                      parent.winfo_screenheight())
            except Exception:
                geo = geometry if PLAYER_GEO_RE.match(geometry) else None
        if geo:
            args.append(f"--geometry={geo}")
        if is_win():
            self._ipc_path = r"\\.\pipe\phdl_mpv_%d_%d" % (os.getpid(), int(time.time()))
        else:
            self._ipc_path = os.path.join(tempfile.gettempdir(),
                                          f"phdl_mpv_{os.getpid()}_{int(time.time())}.sock")
        self._sock_path = None if is_win() else self._ipc_path
        args.append(f"--input-ipc-server={self._ipc_path}")
        args.append(path)
        self._proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      stdin=subprocess.DEVNULL)
        self._started = time.time()
        self._alive = True
        threading.Thread(target=self._poll_volume, daemon=True).start()
        self._watch()

    def _watch(self):
        """Ha az mpv ablakát bezárták, az app is tudja."""
        if self._proc is not None and self._proc.poll() is not None:
            code = self._proc.returncode
            early = time.time() - self._started < 4
            self._cleanup()
            if early and code is not None and code > 0 and code != 4:
                # az mpv rögtön kilépett: hiányzó rendszerfájl, sérült fájl vagy hibás beállítás
                show_dialog(self.parent, "warning",
                            t('Az mpv lejátszó nem indult el rendesen (hibakód: {code}).\nHa a fájl más programban lejátszható, nézd meg, hogy az mpv teljes és friss-e.\n').format(code=code) + (
                                t("Windowson ehhez a videókártya friss illesztőprogramja is kell.")
                                if is_win() else ""))
            return
        if self._alive:
            try:
                self.parent.after(500, self._watch)
            except Exception:
                pass

    def _poll_volume(self):
        """A hangerőt másodpercenként elkérjük az mpv-től, hogy az app megjegyezze."""
        try:
            ipc = MpvIpc(self._ipc_path)
        except OSError:
            return
        try:
            while self._alive and self._proc is not None and self._proc.poll() is None:
                vol = ipc.get("volume")
                if isinstance(vol, (int, float)):
                    v = round(vol / 100.0, 3)
                    if abs(v - self._volume) > 0.004:
                        self._volume = v
                        if self._on_volume is not None:
                            self.parent.after(0, self._on_volume, v)
                time.sleep(1.0)
        except Exception:
            pass
        finally:
            ipc.close()

    def _cleanup(self):
        self._alive = False
        for f in (self._conf.name, self._sock_path):
            try:
                if f:
                    os.remove(f)
            except OSError:
                pass

    def close(self):
        self._alive = False
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self._cleanup()


def release_popups(parent):
    """Ha egy legördülő menü nyitva van (például a felbontásé), az magához ragadja az egeret és a
    billentyűzetet, és a felugró ablak nem kapna semmit. Ezért előtte bezárjuk őket."""
    def walk(w):
        if isinstance(w, ttk.Combobox):
            try:
                w.tk.call("ttk::combobox::Unpost", str(w))
            except tk.TclError:
                pass
        for child in w.winfo_children():
            walk(child)
    try:
        walk(parent.winfo_toplevel())
        if parent.winfo_toplevel() is not parent:
            walk(parent)
        parent.update_idletasks()
    except tk.TclError:
        pass


def show_dialog(parent, kind, message):
    release_popups(parent)
    dlg = Dialog(parent, kind, message)
    parent.wait_window(dlg)


def ask_playlist(parent, title, entries, capped, res_values, default_res):
    """Lejátszási lista kiválasztó. (kiválasztott elemek, felbontás) vagy None."""
    release_popups(parent)
    dlg = PlaylistDialog(parent, title, entries, capped, res_values, default_res)
    parent.wait_window(dlg)
    return dlg.result


def ask_password(parent, heading, message, labels, ok_text, validate=None, danger=False):
    """Jelszó bekérése. A beírt értékek listája, vagy None, ha mégsem."""
    release_popups(parent)
    dlg = PasswordDialog(parent, heading, message, labels, ok_text, validate, danger)
    parent.wait_window(dlg)
    return dlg.result


def show_confirm(parent, heading, message, yes_text=t("Igen"), no_text=t("Nem"), danger=False):
    """Igen/Nem kérdés. True, ha az Igen (vagy a megadott első) gombot nyomták meg."""
    release_popups(parent)
    dlg = ConfirmDialog(parent, heading, message, yes_text, no_text, danger)
    parent.wait_window(dlg)
    return dlg.result


# ---------- maga az alkalmazás ----------
class LockMixin:
    """Az előzmények jelszavas védelme és a tétlenség miatti zárolás."""

    # ---------- az előzmények jelszavas védelme ----------
    def _build_lock_overlay(self, tab):
        """Zárolt állapotban ez a panel takarja az Előzmények fület."""
        self._lock_overlay = tk.Frame(tab, bg=BG)
        self.lock_pw = tk.StringVar()
        center = tk.Frame(self._lock_overlay, bg=BG)
        center.place(relx=0.5, rely=0.25, anchor="n")
        tk.Label(center, text=t("Az előzmények zárolva vannak"), bg=BG, fg=TEXT,
                 font=(FONT_FAMILY, 18, "bold")).pack()
        tk.Label(center, text=t("Add meg a jelszót a megtekintésükhöz."), bg=BG, fg=GREY,
                 font=(FONT_FAMILY, 13)).pack(pady=(6, 18))
        box = RoundBox(center, lambda p: tk.Entry(p, textvariable=self.lock_pw, show="•",
                                                  **entry_kw()), height=38, pad=12)
        box.configure(width=300)
        box.pack()
        self._lock_entry = box.widget
        self._lock_entry.bind("<Return>", lambda e: self.try_unlock())
        self.lock_msg = tk.Label(center, text="", bg=BG, fg=DANGER, wraplength=300,
                                 font=(FONT_FAMILY, 12))
        self.lock_msg.pack(pady=(10, 0))
        RoundButton(center, t("Feloldás"), self.try_unlock, width=300, height=36).pack(pady=(10, 0))
        forgot = tk.Label(center, text=t("Elfelejtett jelszó"), bg=BG, fg=ACCENT_TEXT,
                          cursor="hand2",
                          font=get_font(12, underline=True))
        forgot.pack(pady=(16, 0))
        forgot.bind("<Button-1>", lambda e: self.forgot_password())

    def _apply_lock_state(self):
        """A zárolás látszó következményei: takaró az előzményeken, rejtett előző mappák."""
        if self.hist_locked:
            self._lock_overlay.place(x=0, y=0, relwidth=1, relheight=1)
            self._lock_overlay.lift()
            self.lock_pw.set("")
            self.lock_msg.configure(text="")
        else:
            self._lock_overlay.place_forget()
        self._refresh_history_list()
        self._update_nav_badges()
        try:
            self.folder_combo.configure(values=self._recent_values())
        except (tk.TclError, AttributeError):
            pass
        self._refresh_lock_ui()

    def _touch(self, _event=None):
        self._last_activity = time.time()

    def _lock_tick(self):
        """Beállított tétlenség után újra zárol."""
        try:
            pointer = self.root.winfo_pointerxy()  # az egér mozgása is aktivitás
            if pointer != self._last_pointer:
                self._last_pointer = pointer
                self._touch()
            if (self.lock and not self.hist_locked
                    and time.time() - self._last_activity > LOCK_IDLE_MINUTES * 60):
                self.lock_now()  # ha épp nyitva az oldal, a takaró azonnal rákerül
            self.root.after(5000, self._lock_tick)
        except tk.TclError:
            pass

    def lock_now(self):
        if not self.lock:
            return
        self.hist_locked = True
        self._apply_lock_state()

    def _check_password(self, password):
        """(rendben-e, hibaüzenet). Sok hibás próba után rövid várakozás van."""
        now = time.time()
        if now < self._lock_blocked_until:
            wait = int(self._lock_blocked_until - now) + 1
            return False, t('Túl sok hibás próba. Próbáld újra {wait} mp múlva.').format(wait=wait)
        if self.lock and check_lock(self.lock, password):
            self._lock_fails = 0
            return True, ""
        self._lock_fails += 1
        if self._lock_fails >= LOCK_MAX_FAILS:
            self._lock_fails = 0
            self._lock_blocked_until = now + LOCK_WAIT_SECONDS
            return False, t('Hibás jelszó. {lock_wait_seconds} mp várakozás következik.').format(lock_wait_seconds=LOCK_WAIT_SECONDS)
        return False, t("Hibás jelszó.")

    def try_unlock(self):
        ok, msg = self._check_password(self.lock_pw.get())
        if not ok:
            self.lock_msg.configure(text=msg)
            self.lock_pw.set("")
            return
        self.hist_locked = False
        self._last_activity = time.time()
        self._apply_lock_state()

    def forgot_password(self):
        """Elfelejtett jelszó: az előzmények törlődnek, a jelszavas védelem megszűnik."""
        if not show_confirm(
                self.root, t("Elfelejtett jelszó"),
                t("A jelszó visszaállításával az összes előzmény és a hozzájuk tartozó "
                "bélyegképek véglegesen törlődnek, és a jelszavas védelem kikapcsol.\n\n"
                "Folytatod?"), yes_text=t("Törlés és visszaállítás"), no_text=t("Mégse"), danger=True):
            return
        self.history = []
        save_json(HISTORY_FILE, self.history)
        prune_thumbs(self.history)
        self.lock = None
        self.hist_locked = False
        self.settings["history_lock"] = None
        self._save_settings()
        self._apply_lock_state()

    def lock_set_password(self):
        def check(values):
            if len(values[0]) < LOCK_MIN_LEN:
                return t('A jelszó legalább {lock_min_len} karakter legyen.').format(lock_min_len=LOCK_MIN_LEN)
            if values[0] != values[1]:
                return t("A két jelszó nem egyezik.")
            return None
        res = ask_password(self.root, t("Jelszó beállítása"),
                           t("Ezzel zárolhatod az előzményeket. Ha elfelejted, csak az előzmények "
                           "törlésével lehet visszaállítani."),
                           [t("Új jelszó"), t("Jelszó újra")], t("Beállítás"), validate=check)
        if not res:
            return
        self.lock = make_lock(res[0])
        self.settings["history_lock"] = self.lock
        self.hist_locked = False  # most adtad meg, ezért nyitva marad a következő zárolásig
        self._last_activity = time.time()
        self._save_settings()
        self._apply_lock_state()

    def lock_change_password(self):
        def check(values):
            ok, msg = self._check_password(values[0])
            if not ok:
                return msg
            if len(values[1]) < LOCK_MIN_LEN:
                return t('Az új jelszó legalább {lock_min_len} karakter legyen.').format(lock_min_len=LOCK_MIN_LEN)
            if values[1] != values[2]:
                return t("A két új jelszó nem egyezik.")
            return None
        res = ask_password(self.root, t("Jelszó módosítása"), "",
                           [t("Jelenlegi jelszó"), t("Új jelszó"), t("Új jelszó újra")], t("Módosítás"),
                           validate=check)
        if not res:
            return
        self.lock = make_lock(res[1])
        self.settings["history_lock"] = self.lock
        self._save_settings()
        self._refresh_lock_ui()

    def lock_disable(self):
        def check(values):
            ok, msg = self._check_password(values[0])
            return None if ok else msg
        res = ask_password(self.root, t("Védelem kikapcsolása"),
                           t("A jelszó megadása után az előzmények újra jelszó nélkül elérhetők."),
                           [t("Jelszó")], t("Kikapcsolás"), validate=check)
        if not res:
            return
        self.lock = None
        self.hist_locked = False
        self.settings["history_lock"] = None
        self._save_settings()
        self._apply_lock_state()

    def _build_lock_section(self, body, row):  # a Beállítások "Előzmények védelme" kártyája
        self._card_head(body, row, t("Előzmények védelme"),
                        t("Jelszóval elrejtheted az Előzmények oldalt (a futó letöltésekkel "
                          "együtt) és a korábbi letöltési útvonalak listáját a kíváncsi szemek "
                          "elől. Az app indítása után és {n} perc tétlenség után újra kéri a "
                          "jelszót.").format(n=LOCK_IDLE_MINUTES))
        self.lock_box = tk.Frame(body, bg=PANEL)
        self.lock_box.grid(row=row + 1, column=0, sticky="ew", pady=(4, 0))
        self.lock_box.columnconfigure(0, weight=1)
        self._refresh_lock_ui()
        return row + 2

    def _refresh_lock_ui(self):
        box = getattr(self, "lock_box", None)
        if box is None:
            return
        for w in box.winfo_children():
            w.destroy()
        self._fill_lock_ui(box)

    def _fill_lock_ui(self, box):
        small = (FONT_FAMILY, 12)

        def button(parent, text, command, width, danger=False):
            return secondary_button(parent, text, command, width=width, height=34,
                                    fg="DANGER" if danger else "TEXT", font=small)
        if not self.lock:
            tk.Label(box, text=t("Nincs bekapcsolva"), bg=PANEL, fg=GREY,
                     font=(FONT_FAMILY, 12)).grid(row=0, column=0, sticky="w", pady=(0, 8))
            button(box, t("Jelszó beállítása…"), self.lock_set_password, 170).grid(
                row=1, column=0, sticky="w")
            return
        tk.Label(box, text=t("Be van kapcsolva"), bg=PANEL, fg=TEXT,
                 font=(FONT_FAMILY, 13)).grid(row=0, column=0, sticky="w")
        tk.Label(box, text=t("Indítás után és {n} perc tétlenség után újra jelszót kér.").format(
            n=LOCK_IDLE_MINUTES), bg=PANEL, fg=GREY, font=small).grid(
            row=1, column=0, sticky="w", pady=(4, 0))
        btns = tk.Frame(box, bg=PANEL)
        btns.grid(row=3, column=0, sticky="w", pady=(12, 0))
        button(btns, t("Zárolás most"), self.lock_now, 120).pack(side="left")
        button(btns, t("Jelszó módosítása…"), self.lock_change_password, 170).pack(
            side="left", padx=(8, 0))
        button(btns, t("Kikapcsolás…"), self.lock_disable, 120, danger=True).pack(
            side="left", padx=(8, 0))


class HistoryMixin:
    """Az Előzmények fül: lista, részletek, műveletek."""

    def _build_history_tab(self, tab):
        """Az Előzmények oldal: felül a futó letöltések (FOLYAMATBAN), alatta a kész
        videók kártyái. Egy kártyára kattintva kinyílik a részletekkel és a gombokkal."""
        tab.columnconfigure(0, weight=1)
        self._search_var = tk.StringVar()
        self._search_open = False
        self._hist_view = []      # a látszó kártyák indexei az előzmények listájában
        self._hist_index = None   # a kinyitott kártya
        self._hist_url = ""
        self._hist_thumb_bytes = None
        self._hist_shown = HIST_PAGE
        self._hist_cards = {}     # előzmény index -> kártya elemei
        self._hist_photo_cache = {}
        self._sel_mode = False
        self._sel = set()
        self._sel_anchor = None
        self._fresh = {}          # (útvonal, dátum) -> mikor készült el (ebben a futásban)
        self.hist_default_btn = None
        ttk.Label(tab, text=t("Előzmények"), style="AboutTitle.TLabel").grid(
            row=0, column=0, sticky="w")
        self._hist_sort = "date"
        self._hist_kind = "all"
        self._missing = set()  # a lemezen már nem található fájlok útvonalai
        self._missing_gen = 0
        self._probed = set()  # a hosszukért már megnézett fájlok (futásonként egyszer)
        # a gombok külön sorban, a cím alatt: keskeny ablakban sem csúsznak a címre
        tools = tk.Frame(tab, bg=BG)
        tools.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        tools.columnconfigure(3, weight=1)
        small = (FONT_FAMILY, 12)
        self.search_btn = secondary_button(tools, t("Keresés"), self._toggle_search, width=100,
                                           height=32, font=small)
        self.search_btn.grid(row=0, column=0, padx=(0, 8))
        self.view_btn = secondary_button(tools, t("Nézet"), self._view_menu, width=84,
                                         height=32, font=small)
        self.view_btn.grid(row=0, column=1, padx=(0, 8))
        self.select_btn = secondary_button(tools, t("Kijelölés"), self.toggle_select_mode,
                                           width=100, height=32, font=small)
        self.select_btn.grid(row=0, column=2, padx=(0, 8))
        self.clear_done_btn = secondary_button(tools, t("Készek eltávolítása"),
                                               self._clear_done_jobs, width=170, height=32,
                                               font=small)
        self.clear_done_btn.grid(row=0, column=4, padx=(0, 8))
        self.clear_done_btn.grid_remove()
        # mint a torrent appok "teknős" gombja: egy kattintással be/ki
        self.speed_btn = secondary_button(tools, self._speed_label(), self.toggle_speed_limit,
                                          width=190, height=32, font=small)
        self.speed_btn.grid(row=0, column=5)
        self._refresh_speed_ui()
        head = tk.Frame(tab, bg=BG)
        head.grid(row=1, column=0, sticky="ew")
        head.columnconfigure(0, weight=1)
        self._history_sub = ttk.Label(head, text="", style="Sub.TLabel")
        self._history_sub.grid(row=0, column=0, sticky="w", pady=(4, 14))
        # a keresősor csak a Keresés gombra jelenik meg
        self._search_row = tk.Frame(head, bg=BG)
        self._search_row.columnconfigure(0, weight=1)
        box = RoundBox(self._search_row, lambda p: tk.Entry(
            p, textvariable=self._search_var, **entry_kw()), height=38, pad=12)
        box.grid(row=0, column=0, sticky="ew")
        self._search_entry = box.widget
        secondary_button(self._search_row, t("Szöveg törlése"), self._clear_search, width=130,
                         height=34, font=small).grid(row=0, column=1, padx=(8, 0))
        tk.Label(self._search_row,
                 text=t("Feltöltő, cím, dátum vagy weboldal neve (több szó is lehet)."),
                 bg=BG, fg=GREY, font=small).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 14))
        self._search_entry.bind("<Escape>", lambda e: self._toggle_search())
        self._search_var.trace_add("write", lambda *a: self._search_changed())
        for seq in ("<Command-f>", "<Control-f>"):
            self.root.bind(seq, self._open_search_shortcut, add="+")
        area = self._build_history_scroll_area(tab)

        # kijelölés mód sávja
        self.sel_bar = RoundCard(area)
        self.sel_bar.set_outline("ACCENT")
        self.sel_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        bar = self.sel_bar.inner
        bar.configure(padx=14, pady=8)
        bar.columnconfigure(0, weight=1)
        self.sel_label = tk.Label(bar, text="", bg=PANEL, fg=TEXT, anchor="w",
                                  font=get_font(13, "bold"))
        self.sel_label.grid(row=0, column=0, sticky="w")
        sel_btns = tk.Frame(bar, bg=PANEL)
        sel_btns.grid(row=0, column=1, sticky="e", padx=(12, 0))
        # a felirat tördelődik, ha nem fér el; a gombok nem takarják ki
        bar.bind("<Configure>", lambda e: self.sel_label.configure(
            wraplength=max(80, e.width - sel_btns.winfo_reqwidth() - 40)), add="+")
        secondary_button(sel_btns, t("Mind kijelölése"), self._hist_select_all, width=130,
                         height=30, font=small).pack(side="left", padx=(0, 6))
        self.sel_del_btn = RoundButton(sel_btns, t("Törlés"), self._delete_selected, width=100,
                                       height=30, bg="DANGER", fg="ACCENT_FG",
                                       hover="DANGER", font=get_font(12, "bold"))
        self.sel_del_btn.pack(side="left", padx=(0, 6))
        secondary_button(sel_btns, t("Kész"), self.toggle_select_mode, width=70, height=30,
                         font=small).pack(side="left")
        self.sel_bar.grid_remove()

        # futó letöltések
        self._build_jobs_section(area)

        # kész videók: a kártyák külön elemek a vásznon (self._hist_stack), alattuk a lábléc
        foot = tk.Frame(self.hist_canvas, bg=BG)
        foot.columnconfigure(0, weight=1)
        self._hist_stack.add(foot, footer=True)
        self.hist_more_btn = secondary_button(foot, "", self._hist_show_more, width=220,
                                              height=34, font=small)
        self.hist_more_btn.grid(row=0, column=0, pady=(6, 4))
        self.hist_more_btn.grid_remove()
        self.hist_empty = EmptyState(foot, "clock", t("Még nincs letöltés"),
                                     t("Az elkészült letöltéseid itt jelennek meg."))
        self.hist_empty.grid(row=1, column=0, sticky="ew", pady=(30, 0))
        self.hist_empty.grid_remove()
        self.hist_clear_btn = secondary_button(foot, t("Összes előzmény törlése"),
                                               self._clear_history, width=200, height=34,
                                               fg="DANGER", font=small)
        self.hist_clear_btn.grid(row=2, column=0, sticky="e", pady=(14, 4))

        for seq in (f"<{MOD_KEY}-a>", f"<{MOD_KEY}-A>"):
            self.root.bind_all(seq, self._hist_key_select_all, add="+")
        for seq in ("<Delete>", "<BackSpace>"):
            self.root.bind_all(seq, self._hist_key_delete, add="+")
        self._build_lock_overlay(tab)
        self._refresh_history_list()


    def _history_subtitle(self):
        active = sum(1 for j in self.jobs if j.state == "active")
        waiting = sum(1 for j in self.jobs if j.state == "waiting")
        parts = []
        if active or waiting:
            parts.append(t("{a} letöltés fut, {w} vár").format(a=active, w=waiting) if waiting
                         else t("{a} letöltés fut").format(a=active))
        if self._search_var.get().strip() or self._hist_kind != "all":
            parts.append(t('{n__hist_view} találat ({n_history} bejegyzésből)').format(
                n__hist_view=len(self._hist_view), n_history=len(self.history)))
        else:
            cap = history_cap(self.history_limit)
            if cap == 0:
                parts.append(t("Az előzmények ki vannak kapcsolva"))
            elif self.history:
                parts.append(t("{n} videó letöltve").format(n=len(self.history)))
        return " · ".join(parts) or t("Az elkészült letöltéseid itt jelennek meg.")

    def _refresh_hist_subtitle(self):
        try:
            self._history_sub.configure(text=self._history_subtitle())
        except (AttributeError, tk.TclError):
            pass

    def _refresh_history_list(self, keep_page=False, expand=None):
        """A kártyák újraépítése (keresés, nézet, új vagy törölt bejegyzés után).
        `expand`: ennek a bejegyzésnek (index) a kártyája nyitva épül fel."""
        self.root.after_idle(self._update_nav_badges)
        expanded = self.history[expand] if expand is not None and expand < len(self.history) \
            else self._selected_history_entry()
        self._hist_stack.clear()
        self._hist_cards = {}
        if not keep_page:
            self._hist_shown = HIST_PAGE
        if self.hist_locked:  # zárolva semmi nem látszik
            self._hist_view = []
            self._hist_index = None
            if self._search_open or self._search_var.get():
                self._close_search()
            self.hist_clear_btn.grid_remove()
            self.hist_more_btn.grid_remove()
            return
        query = self._search_var.get()
        self._hist_view = history_view(self.history, query, self._hist_sort, self._hist_kind)
        self._sel &= set(self._hist_view)
        self._hist_index = None
        if expanded is not None:
            self._hist_index = next((i for i in self._hist_view
                                     if self.history[i] is expanded), None)
        self._build_hist_cards(0, min(self._hist_shown, len(self._hist_view)))
        if self._hist_index is not None:
            # a kinyitott kártya akkor is azonnal elkészül, ha a sorrendben hátrébb van
            self._finish_hist_build()
        self._check_missing_async()
        self._refresh_hist_subtitle()
        for btn in (self.search_btn, self.view_btn, self.select_btn):
            btn.grid() if self.history else btn.grid_remove()
        if not self.history and self._search_open:
            self._close_search()
        if not self.history and self._sel_mode:
            self.toggle_select_mode()
        self._refresh_sel_bar()
        if self.history and not self._hist_view:  # van előzmény, de nincs találat
            self.hist_empty.kind = "search"
            self.hist_empty.title = t("Nincs találat")
            self.hist_empty.hint = (t("Próbálj másik kifejezést vagy szűrést.")
                                    if self._hist_kind != "all" else t("Próbálj másik kifejezést."))
            self.hist_empty._draw()
            self.hist_empty.grid()
            self.hist_clear_btn.grid()
        elif self.history:
            self.hist_empty.grid_remove()
            self.hist_clear_btn.grid()
        else:
            self.hist_empty.kind = "clock"
            off = self.history_limit == 0
            self.hist_empty.title = t("Az előzmények ki vannak kapcsolva") if off \
                else t("Még nincs letöltés")
            self.hist_empty.hint = (t("A Beállításokban bekapcsolhatod.") if off
                                    else t("Az elkészült letöltéseid itt jelennek meg."))
            self.hist_empty._draw()
            # futó letöltés mellett nem kell a nagy üres jelzés
            if any(j.ui for j in self.jobs):
                self.hist_empty.grid_remove()
            else:
                self.hist_empty.grid()
            self.hist_clear_btn.grid_remove()

    def _search_changed(self):
        """Gépelés közben nem építünk újra minden betűre: 200 ms szünet után."""
        job = getattr(self, "_search_job", None)
        if job is not None:
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
        self._search_job = self.root.after(200, self._search_apply)

    def _search_apply(self):
        self._search_job = None
        self._refresh_history_list()

    def _hist_show_more(self):
        self._finish_hist_build()
        start = self._hist_shown
        self._hist_shown += HIST_PAGE
        self._build_hist_cards(start, min(self._hist_shown, len(self._hist_view)))

    def _hist_group_of(self, entry):
        """Csoport dátum szerinti rendezésnél: Ma, Tegnap, Korábban."""
        try:
            day = datetime.fromisoformat(entry.get("date") or "").date()
        except (TypeError, ValueError):
            return t("KORÁBBAN")
        today = datetime.now().date()
        if day == today:
            return t("MA")
        if (today - day).days == 1:
            return t("TEGNAP")
        return t("KORÁBBAN")

    def _build_hist_cards(self, start, end):
        """A kártyák részletekben épülnek: az első HIST_CHUNK azonnal, a többi apránként a
        háttérben, így sok előzménynél sem akad meg az app (gépelés, kész letöltés)."""
        self._hist_gen = getattr(self, "_hist_gen", 0) + 1
        self._hist_build = [start, end]
        if not start:
            self._hist_last_group = None
        self.hist_more_btn.grid_remove()
        self._hist_build_chunk(self._hist_gen)

    def _hist_build_chunk(self, gen):
        if gen != getattr(self, "_hist_gen", 0) or self._hist_build is None:
            return
        start, end = self._hist_build
        stop = min(end, start + HIST_CHUNK)
        self._build_hist_range(start, stop)
        if stop < end:
            self._hist_build = [stop, end]
            try:
                self.root.after(1, self._hist_build_chunk, gen)
            except tk.TclError:
                pass
        else:
            self._hist_build = None
            self._hist_build_done(end)

    def _finish_hist_build(self):
        """A még hátralévő kártyák azonnali elkészítése."""
        if getattr(self, "_hist_build", None):
            start, end = self._hist_build
            self._hist_build = None
            self._build_hist_range(start, end)
            self._hist_build_done(end)

    def _hist_build_done(self, end):
        rest = len(self._hist_view) - end
        if rest > 0:
            self.hist_more_btn.set_text(t("Továbbiak ({n} még)").format(n=rest))
            self.hist_more_btn.grid()
        else:
            self.hist_more_btn.grid_remove()

    def _build_hist_range(self, start, end):
        frame = self.hist_canvas
        stack = self._hist_stack
        last_group = self._hist_last_group if start else None
        for pos in range(start, end):
            i = self._hist_view[pos]
            entry = self.history[i]
            if self._hist_sort == "date":
                group = self._hist_group_of(entry)
                if group != last_group:
                    title = t("LETÖLTVE · {x}").format(x=group) if pos == 0 else group
                    stack.add(tk.Label(frame, text=title, bg=BG, fg=GREY,
                                       font=get_font(10, "bold"), anchor="w"),
                              top=4 if pos == 0 else 12, bottom=6, padx=4)
                    last_group = group
            elif pos == 0:
                stack.add(tk.Label(frame, text=t("LETÖLTVE"), bg=BG, fg=GREY,
                                   font=get_font(10, "bold"), anchor="w"),
                          top=4, bottom=6, padx=4)
            self._build_hist_card(frame, i, entry)
        self._hist_last_group = last_group

    def _entry_meta(self, entry):
        """A kártya második sora: feltöltő · oldal · méret · idő."""
        parts = []
        uploader = " ".join(str(entry.get("uploader") or "").split())
        if uploader:
            parts.append(uploader)
        site = site_label(entry.get("url"))
        if site:
            parts.append(site)
        size = entry.get("size")
        if isinstance(size, (int, float)):
            parts.append(format_size(size, False))
        try:
            d = datetime.fromisoformat(entry.get("date") or "")
            parts.append(d.strftime("%H:%M") if d.date() == datetime.now().date()
                         else format_history_date(entry.get("date")))
        except (TypeError, ValueError):
            pass
        return " · ".join(parts)

    def _hist_photo(self, entry, size):
        path = thumb_file(entry)
        if not path:
            return None
        key = (path, size, PAL.get("PANEL"))
        photo = self._hist_photo_cache.get(key)
        if photo is None:
            try:
                with open(path, "rb") as f:
                    photo = self._make_thumbnail(f.read(), size)
            except OSError:
                photo = None
            if photo is not None:
                if len(self._hist_photo_cache) > 400:
                    self._hist_photo_cache.clear()
                self._hist_photo_cache[key] = photo
        return photo

    def _entry_status(self, entry):
        """(szöveg, szín) a kártya jobb felső sarkába."""
        if entry.get("path") in self._missing:
            return t("A fájl nem található"), DANGER
        if (entry.get("path"), entry.get("date")) in self._fresh:
            return t("●  Új"), ok_color()
        return t("✓  Letöltve"), GREY

    def _build_hist_card(self, parent, i, entry):
        """Összecsukva: nagy bélyegkép, mellette cím, feltöltő, feltöltés dátuma, hossz.
        Kinyitva alatta a többi adat és a gombok (animáció nélkül, azonnal)."""
        card = RoundCard(parent)
        self._hist_stack.add(card, bottom=8)
        inner = card.inner
        inner.columnconfigure(0, weight=1)
        hdr = tk.Frame(inner, bg=PANEL, cursor="hand2")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        hdr.columnconfigure(2, weight=1)
        ui = {"card": card, "hdr": hdr, "entry": entry, "detail": None, "open": False}
        ui["lead"] = tk.Canvas(hdr, width=22, height=22, bg=PANEL, highlightthickness=0, bd=0)
        ui["lead"].grid(row=0, column=0, padx=(0, 10))
        photo = self._hist_photo(entry, THUMB_BIG)
        if photo is not None:
            ui["thumb"] = tk.Label(hdr, image=photo, bg=PANEL, bd=0)
            ui["photo"] = photo
        else:
            ui["thumb"] = tk.Frame(hdr, width=THUMB_BIG[0], height=THUMB_BIG[1], bg=CHIP)
        ui["thumb"].grid(row=0, column=1, sticky="nw", padx=(0, 16))
        info = tk.Frame(hdr, bg=PANEL)
        info.grid(row=0, column=2, sticky="new")
        title = entry.get("title") or entry.get("name") or ""
        if len(title) > 120:
            title = title[:119] + "…"
        labels = [tk.Label(info, text=title, bg=PANEL, fg=TEXT, anchor="w", justify="left",
                           font=get_font(14, "bold"))]
        uploader = " ".join(str(entry.get("uploader") or "").split())
        site = site_label(entry.get("url"))
        line2 = " · ".join(x for x in (uploader, site) if x)
        if line2:
            labels.append(tk.Label(info, text=line2, bg=PANEL, fg=GREY, anchor="w",
                                   justify="left", font=get_font(12)))
        ui["facts"] = tk.Label(info, text=self._entry_facts(entry), bg=PANEL, fg=GREY,
                               anchor="w", justify="left", font=get_font(12))
        labels.append(ui["facts"])
        for k, lab in enumerate(labels):
            lab.pack(fill="x", pady=(0 if k == 0 else 4, 0))
        # a hosszú cím a kártya szélességéhez tördelődik, nem lóg ki
        info.bind("<Configure>", lambda e, labs=labels: [
            lab.configure(wraplength=max(40, e.width)) for lab in labs])
        text, color = self._entry_status(entry)
        ui["status"] = tk.Label(hdr, text=text, bg=PANEL, fg=color, font=get_font(12, "bold"))
        ui["status"].grid(row=0, column=3, sticky="ne", padx=(12, 0))

        def bind_tree(widget):
            widget.bind("<Button-1>", lambda e, k=i: self._hist_card_click(k, e), add="+")
            widget.bind("<Double-Button-1>", lambda e, k=i: self._hist_card_double(k))
            for child in widget.winfo_children():
                bind_tree(child)
        bind_tree(hdr)
        self._hist_cards[i] = ui
        self._paint_card(i)
        if i == self._hist_index:
            self._expand_card(i, scroll=False)
        return ui

    def _entry_facts(self, entry):
        """A cím alatti sor: eredeti feltöltés dátuma és hossz (ha ismert)."""
        parts = []
        up = entry_upload_date(entry)
        if up:
            parts.append(t("Feltöltve: {x}").format(x=up))
        dur = entry.get("duration")
        if isinstance(dur, (int, float)) and dur > 0:
            parts.append(t("Hossz: {x}").format(x=live_len(dur)))
        return " · ".join(parts) or self._entry_meta(entry)

    def _paint_card(self, i):
        """A kártya bal szélén nyíl vagy kijelölő kör, és a kerete."""
        ui = self._hist_cards.get(i)
        if not ui:
            return
        lead = ui["lead"]
        lead.delete("all")
        selected = i in self._sel
        if self._sel_mode:
            if selected:
                lead.create_oval(2, 2, 20, 20, fill=col("ACCENT"), outline=col("ACCENT"))
                lead.create_line(6, 11, 10, 15, 16, 7, fill=col("ACCENT_FG"), width=2,
                                 capstyle="round", joinstyle="round")
            else:
                lead.create_oval(2, 2, 20, 20, outline=col("GREY"), width=2)
        else:
            lead.create_text(11, 11, text="▾" if ui["open"] else "▸",
                             fill=col("GREY"), font=get_font(12))
        ui["card"].set_outline("ACCENT" if (selected and self._sel_mode) or ui["open"]
                               else "BORDER")

    def _hist_card_click(self, i, event):
        if self._sel_mode:
            shift = bool(event.state & 0x1)
            if shift and self._sel_anchor in self._hist_view and i in self._hist_view:
                a, b = sorted((self._hist_view.index(self._sel_anchor), self._hist_view.index(i)))
                self._sel |= set(self._hist_view[a:b + 1])
            elif i in self._sel:
                self._sel.discard(i)
            else:
                self._sel.add(i)
            self._sel_anchor = i
            for k in list(self._hist_cards):
                self._paint_card(k)
            self._refresh_sel_bar()
            return
        if self._hist_index == i:
            self._collapse_card(i)
        else:
            self._expand_card(i)

    def _hist_card_double(self, i):
        """Dupla kattintás: lejátszás az app lejátszójával (a kártya nyitva marad)."""
        if self._sel_mode:
            return
        if self._hist_index != i:
            self._expand_card(i)
        self._open_player_selected()

    def _collapse_card(self, i):
        ui = self._hist_cards.get(i)
        if self._hist_index == i:
            self._hist_index = None
            self._hist_url = ""
            self._hist_thumb_bytes = None
            self.hist_default_btn = None
        if not ui:
            return
        entry = ui["entry"]
        key = (entry.get("path"), entry.get("date"))
        if key in self._fresh:  # megnézted: az "Új" jelzés eltűnik
            del self._fresh[key]
            text, color = self._entry_status(entry)
            ui["status"].configure(text=text, fg=color)
        if ui["detail"] is not None:
            ui["detail"].destroy()
            ui["detail"] = None
        ui["open"] = False
        self._paint_card(i)

    def _expand_card(self, i, scroll=True):
        """Egy kártya kinyitása (egyszerre egy): a kép alatt, balra igazítva a többi adat,
        alatta a gombok. A mappa és a link kattintható, és ki is jelölhető."""
        if self._hist_index is not None and self._hist_index != i:
            self._collapse_card(self._hist_index)
        ui = self._hist_cards.get(i)
        if not ui or i >= len(self.history):
            return
        entry = self.history[i]
        self._hist_index = i
        self._hist_url = entry.get("url") or ""
        path = thumb_file(entry)
        try:
            with open(path, "rb") as f:
                self._hist_thumb_bytes = f.read()
        except (OSError, TypeError):
            self._hist_thumb_bytes = None
        if ui["detail"] is not None:
            ui["detail"].destroy()
        det = tk.Frame(ui["card"].inner, bg=PANEL)
        det.grid(row=1, column=0, sticky="ew", padx=(44, 12), pady=(0, 14))
        det.columnconfigure(1, weight=1)
        ui["detail"] = det
        size = entry.get("size")
        folder = entry.get("folder") or os.path.dirname(entry.get("path") or "")
        rows = [(t("Fájl"), entry.get("name") or "", None),
                (t("Mappa"), folder, self._reveal_selected),
                (t("Letöltve"), format_history_date(entry.get("date")), None),
                (t("Fájlméret"), format_size(size, True) if isinstance(size, (int, float))
                 else t("ismeretlen"), None),
                (t("Eredeti link"), self._hist_url or t("nincs mentve"),
                 self._open_link if self._hist_url else None)]
        for r, (key, value, action) in enumerate(rows):
            tk.Label(det, text=key, bg=PANEL, fg=GREY, anchor="w",
                     font=get_font(12)).grid(row=r, column=0, sticky="w", padx=(0, 16), pady=2)
            field = copyable_text(det, value, fg=ACCENT_TEXT if action else TEXT,
                                  on_click=action)
            field.grid(row=r, column=1, sticky="ew", pady=2)
        r = len(rows)
        if entry.get("path") in self._missing:
            tk.Label(det, text=t("A fájl nem található ezen az útvonalon."), bg=PANEL,
                     fg=DANGER, anchor="w", font=get_font(12)).grid(
                row=r, column=0, columnspan=2, sticky="w", pady=(4, 0))
            r += 1
        acts = tk.Frame(det, bg=PANEL)
        acts.grid(row=r, column=0, columnspan=2, sticky="w", pady=(12, 0))
        small = get_font(12)
        RoundButton(acts, t("▶  Lejátszás"), self._open_player_selected, width=110, height=30,
                    font=get_font(12, "bold")).pack(side="left", padx=(0, 6))
        self.hist_default_btn = secondary_button(acts, t("Lejátszás (alap)"),
                                                 self._open_default_selected, width=120,
                                                 height=30, font=small)
        self.hist_default_btn.pack(side="left", padx=(0, 6))
        secondary_button(acts, t("Törlés"), self._delete_selected, width=80, height=30,
                         fg="DANGER", font=small).pack(side="left")
        ui["open"] = True
        self._paint_card(i)
        self._refresh_default_player_label(entry["path"])
        if scroll:
            self.root.after_idle(lambda: self._scroll_card_into_view(i))

    def _fade_in_status(self, i):
        """A friss letöltés "Új" jelzése gyorsan előtűnik (csak ha épp látszik a kártya)."""
        ui = self._hist_cards.get(i)
        if not ui or not self._card_in_view(i):
            return
        target = ok_color()
        t0 = time.time()

        def step():
            p = min(1.0, (time.time() - t0) / (0.45 * ANIM_SLOW))
            try:
                ui["status"].configure(fg=blend_hex(target, PANEL, p))
            except tk.TclError:
                return
            if p < 1:
                self.root.after(16, step)
        step()

    def _card_in_view(self, i):
        ui = self._hist_cards.get(i)
        try:
            if not ui or self.notebook.index("current") != 2 or self.hist_locked:
                return False
            canvas = self.hist_canvas
            top = ui["card"].winfo_rooty() - canvas.winfo_rooty()
            return ui["card"].winfo_ismapped() and -ui["card"].winfo_height() < top \
                < canvas.winfo_height()
        except tk.TclError:
            return False

    def _scroll_card_into_view(self, i):
        """Ha a kinyitott kártya alja kilóg, annyit görgetünk, hogy látsszon."""
        ui = self._hist_cards.get(i)
        if not ui:
            return
        try:
            canvas = self.hist_canvas
            canvas.update_idletasks()
            box = self._hist_stack.bounds(ui["card"])
            if box is None:  # közben újraépült a lista
                return
            top, height = box
            bottom = top + height
            total, visible = self._scroll_metrics(canvas)
            view_top = canvas.yview()[0] * total
            if bottom > view_top + visible:
                target = min(top, bottom - visible + 10)
            elif top < view_top:
                target = top
            else:
                return
            canvas.yview_moveto(max(0, target) / total)
        except tk.TclError:
            pass

    # ---------- kijelölés mód ----------
    def toggle_select_mode(self):
        self._sel_mode = not self._sel_mode
        self._sel = set()
        self._sel_anchor = None
        if self._sel_mode and self._hist_index is not None:
            self._collapse_card(self._hist_index)
        self.select_btn.set_colors(*(("ACCENT", "ACCENT_FG", "ACCENT_HOVER", "")
                                     if self._sel_mode else
                                     ("CONTROL", "TEXT", "CONTROL_HOVER", "BORDER")))
        for k in list(self._hist_cards):
            self._paint_card(k)
        self._refresh_sel_bar()
        for job in self.jobs:  # kijelölésnél a futó letöltések halványak
            self._update_job_ui(job)

    def _refresh_sel_bar(self):
        if not self._sel_mode:
            self.sel_bar.grid_remove()
            return
        n = len(self._sel)
        self.sel_label.configure(text=t("{n} videó kijelölve").format(n=n) if n
                                 else t("Kattints a kártyákra a kijelöléshez"))
        self.sel_del_btn.set_text(t("Törlés ({n})").format(n=n) if n else t("Törlés"))
        self.sel_del_btn.set_state("normal" if n else "disabled")
        self.sel_bar.grid()

    def _hist_select_all(self, _event=None):
        if not self._sel_mode:
            self.toggle_select_mode()
        self._sel = set(self._hist_view)
        for k in list(self._hist_cards):
            self._paint_card(k)
        self._refresh_sel_bar()
        return "break"

    def _hist_page_active(self):
        try:
            return self.notebook.index("current") == 2 and not self.hist_locked
        except tk.TclError:
            return False

    def _hist_key_select_all(self, event):
        if self._hist_page_active() and not isinstance(event.widget, (tk.Entry, ttk.Entry,
                                                                      tk.Text)):
            return self._hist_select_all()

    def _hist_key_delete(self, event):
        if self._hist_page_active() and not isinstance(event.widget, (tk.Entry, ttk.Entry,
                                                                      tk.Text)):
            if self._sel_mode and self._sel or not self._sel_mode and self._hist_index is not None:
                self._delete_selected()
                return "break"

    # ---------- hiányzó fájlok ----------
    def _missing_done(self, gen, gone, lengths=None):
        if gen != self._missing_gen:
            return
        self._missing = gone
        if lengths:
            for entry in self.history:
                if entry.get("path") in lengths and "duration" not in entry:
                    entry["duration"] = lengths[entry["path"]]  # 0: nem sikerült, nem próbáljuk újra
            save_json(HISTORY_FILE, self.history)
            for i, ui in list(self._hist_cards.items()):
                try:
                    ui["facts"].configure(text=self._entry_facts(ui["entry"]))
                except (tk.TclError, KeyError):
                    pass
        self._apply_missing_marks()

    def _apply_missing_marks(self):
        """A kártyák állapota: hiányzó fájl, frissen kész vagy letöltve."""
        for i, ui in list(self._hist_cards.items()):
            if i >= len(self.history):
                continue
            text, color = self._entry_status(self.history[i])
            try:
                ui["status"].configure(text=text, fg=color)
            except tk.TclError:
                continue
            self._paint_card(i)

    def _open_history_entries(self, entries):
        """Az értesítésre vagy a kész letöltésre kattintva: Előzmények, kinyitva az első."""
        self._switch_tab("2")
        if self.hist_locked or not entries:
            return

        def find(entry):
            for i, e in enumerate(self.history):
                if e is entry or (e.get("path") == entry.get("path") and
                                  e.get("date") == entry.get("date")):
                    return i
            return None
        indices = [i for i in (find(e) for e in entries) if i is not None]
        if indices:
            self._open_history_index(indices[0])

    def _open_history_index(self, index):
        """Az Előzmények oldalon kinyitja és megmutatja az adott bejegyzést."""
        self._switch_tab("2")
        if self.hist_locked or index >= len(self.history):
            return
        if self._sel_mode:
            self.toggle_select_mode()
        if index not in self._hist_view:  # szűrés vagy keresés miatt nem látszik: alap nézet
            if getattr(self, "_search_open", False):
                self._close_search()
            else:
                self._search_var.set("")
            self._hist_kind = "all"
            self._refresh_history_list()
        if index not in self._hist_view:
            return
        pos = self._hist_view.index(index)
        if pos >= self._hist_shown:
            self._hist_shown = (pos // HIST_PAGE + 1) * HIST_PAGE
        self._refresh_history_list(keep_page=True, expand=index)

    def _selected_history_indices(self):
        """Kijelölés módban a kijelöltek (a nézet sorrendjében), különben a kinyitott."""
        if self._sel_mode:
            return [i for i in self._hist_view if i in self._sel and i < len(self.history)]
        i = self._hist_index
        return [i] if i is not None and i < len(self.history) else []

    def _selected_history_entry(self):
        i = getattr(self, "_hist_index", None)
        if i is not None and 0 <= i < len(self.history):
            return self.history[i]
        return None

    def _set_default_label(self, name):
        btn = self.hist_default_btn
        if btn is None:
            return
        if name and name.lower().endswith(" player") and len(name) > 12:
            name = name[:-7]  # "QuickTime Player" helyett "QuickTime": rövidebb gombfelirat
        try:
            btn.set_text(t('Lejátszás ({name})').format(name=name) if name
                         else t("Lejátszás (alap)"))
            fnt = tkfont.Font(root=self.root, font=btn._font)
            btn.configure(width=fnt.measure(btn._text) + 26)
        except tk.TclError:
            pass

    def _delete_selected(self):
        if self.hist_locked:
            return
        indices = self._selected_history_indices()
        if not indices:
            return
        if len(indices) == 1:
            entry = self.history[indices[0]]
            question = (t('Biztosan törlöd ezt a bejegyzést az előzményekből?\n\n{x}\n\nA fájl a lemezen megmarad.').format(x=history_label(entry)))
        else:
            names = "\n".join(history_label(self.history[i]) for i in indices[:5])
            more = t('\n... és még {x}').format(x=len(indices) - 5) if len(indices) > 5 else ""
            question = (t('Biztosan törlöd a kijelölt {n_indices} bejegyzést az előzményekből?\n\n{names}{more}\n\nA fájlok a lemezen megmaradnak.').format(n_indices=len(indices), names=names, more=more))
        if not show_confirm(self.root, t("Törlés az előzményből"), question,
                            yes_text=t("Törlés"), no_text=t("Mégse"), danger=True):
            return
        self._hist_index = None
        self._sel = set()
        self.history = remove_history_entries(self.history, indices)
        save_json(HISTORY_FILE, self.history)
        prune_thumbs(self.history)
        self._refresh_history_list(keep_page=True)

    def _render_hist_thumb(self):
        """Témaváltás után a kártyák újraépülnek (a bélyegképek sarka a kártya színű)."""
        try:
            self._refresh_history_list(keep_page=True)
        except (AttributeError, tk.TclError):
            pass

    def _build_history_scroll_area(self, tab):
        """Görgethető terület: hosszú link vagy kis ablak esetén sem csúszik ki semmi."""
        tab.rowconfigure(3, weight=1)
        wrap = tk.Frame(tab, bg=BG)
        wrap.grid(row=3, column=0, sticky="nsew")
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)
        self.hist_canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0, height=10)
        self.hist_bar = ttk.Scrollbar(wrap, orient="vertical", command=self.hist_canvas.yview)
        self.hist_canvas.configure(yscrollcommand=self._hist_scroll_set)
        self.hist_canvas.grid(row=0, column=0, sticky="nsew")
        # a fejléc és a futó letöltések egy elem, alatta minden kártya külön (CanvasStack);
        # jobb oldalon hely marad a görgetősávnak
        self._hist_stack = CanvasStack(self.hist_canvas)
        area = tk.Frame(self.hist_canvas, bg=BG)
        self._hist_stack.add(area, keep=True)
        area.columnconfigure(0, weight=1)
        return area

    def _hist_scroll_set(self, lo, hi):
        """A görgetősáv csak akkor látszik, ha nem fér el minden. Görgetéskor a
        képernyőn kívül megváltozott elemek (pl. új futó letöltés) is a helyükre kerülnek."""
        auto_scrollbar(self.hist_bar, lo, hi, row=0, column=1, sticky="ns")
        self._hist_stack.relayout_soon()

    def _hist_tab_visible(self):
        return self.hist_canvas.winfo_ismapped()

    def _hist_wheel(self, event, step=None):
        try:
            if self._hist_tab_visible():
                self._scroll_canvas(self.hist_canvas, event, step)
        except tk.TclError:
            return

    def set_player_engine(self, _event=None):
        label = self.player_engine_var.get()
        self.player_engine = next((k for k, v in PLAYER_ENGINES.items() if v == label),
                                  self.player_engine)
        self.settings["player_engine"] = self.player_engine
        self._save_settings()

    def set_history_limit(self, _event=None):
        """Az előzmények méretének váltása: csak kisebbre váltáskor törlődnek a régebbiek."""
        label = self.history_limit_var.get()
        new = next((v for v, text in HISTORY_LIMITS if text == label), self.history_limit)
        cap = history_cap(new)
        extra = 0 if cap is None else max(0, len(self.history) - cap)
        if extra:
            what = t("az összes bejegyzés") if cap == 0 else t('a {extra} legrégebbi bejegyzés').format(extra=extra)
            if not show_confirm(self.root, t("Előzmények méretének csökkentése"),
                                t('A kisebb méret miatt {what} törlődik az előzményekből.\n\nA letöltött fájlok a lemezen megmaradnak.').format(what=what),
                                yes_text=t("Törlés"), no_text=t("Mégse"), danger=True):
                self.history_limit_var.set(
                    dict(HISTORY_LIMITS).get(self.history_limit, HISTORY_LIMITS[1][1]))
                return
            self.history = self.history[:cap]
            save_json(HISTORY_FILE, self.history)
            prune_thumbs(self.history)
        self.history_limit = new
        self.settings["history_limit"] = new
        self._save_settings()
        self._history_sub.configure(text=self._history_subtitle())
        self._refresh_history_list()

    def _add_history(self, entry, refresh=True):
        cap = history_cap(self.history_limit)
        if cap == 0:  # nincs előzmény: semmi nem kerül a listába
            prune_thumbs(self.history)
            return
        self.history = add_history_entry(self.history, entry, cap)
        save_json(HISTORY_FILE, self.history)
        prune_thumbs(self.history)
        if refresh:
            self._refresh_history_list()

    def _view_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        sort_var = tk.StringVar(value=self._hist_sort)
        kind_var = tk.StringVar(value=self._hist_kind)
        menu.add_command(label=t("Rendezés"), state="disabled")
        for value, text in HIST_SORTS:
            menu.add_radiobutton(label=text, variable=sort_var, value=value,
                                 command=lambda v=value: self.set_history_view(sort=v))
        menu.add_separator()
        menu.add_command(label=t("Szűrés típus szerint"), state="disabled")
        for value, text in HIST_FILTERS:
            menu.add_radiobutton(label=text, variable=kind_var, value=value,
                                 command=lambda v=value: self.set_history_view(kind=v))
        b = self.view_btn
        try:
            menu.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height() + 2)
        finally:
            menu.grab_release()

    def set_history_view(self, sort=None, kind=None):
        if sort is not None:
            self._hist_sort = sort
        if kind is not None:
            self._hist_kind = kind
        self._refresh_history_list()

    # ---------- hiányzó fájlok ----------
    def _check_missing_async(self):
        """A fájlok meglétét háttérszál nézi: egy nem elérhető NAS ne fagyassza le az appot."""
        self._missing_gen += 1
        gen = self._missing_gen
        paths = [e.get("path") for e in self.history if e.get("path")]
        # a régebbi bejegyzésekből hiányzik a videó hossza: a fájlból pótoljuk (egyszer)
        no_len = [e["path"] for e in self.history if e.get("path") and "duration" not in e
                  and e["path"] not in self._probed][:HIST_PROBE_MAX]
        self._probed.update(no_len)  # egy gyors újabb frissítés ne nézze meg őket még egyszer

        def work():
            gone = {p for p in paths if not os.path.exists(p)}
            lengths = {}
            for path in no_len:
                if path in gone:
                    continue
                media = probe_media(path)
                lengths[path] = round(media["duration"]) if media and media["duration"] else 0
            try:
                self.root.after(0, lambda: self._missing_done(gen, gone, lengths))
            except (RuntimeError, tk.TclError):
                pass

        threading.Thread(target=work, daemon=True).start()

    def _toggle_search(self):
        """A Keresés gomb: megjeleníti vagy elrejti (és törli) a keresősort."""
        if self.hist_locked:
            return
        if self._search_open:
            self._close_search()
        else:
            self._search_open = True
            self._search_row.grid(row=1, column=0, sticky="ew")
            self._search_entry.focus_set()

    def _open_search_shortcut(self, _event=None):
        try:
            if self.notebook.index("current") == 2 and not self._search_open and self.history:
                self._toggle_search()
                return "break"
        except tk.TclError:
            pass

    def _close_search(self):
        self._search_open = False
        self._search_row.grid_remove()
        self._search_var.set("")  # a szűrés megszűnik, a teljes lista visszajön
        self.root.focus_set()

    def _clear_search(self):
        self._search_var.set("")
        self._search_entry.focus_set()

    def _reveal_selected(self):
        entry = self._selected_history_entry()
        if entry is None:
            return
        result = reveal_path(entry["path"])
        if result == "folder":
            show_dialog(self.root, "warning", t('A fájl már nem található, ezért a mappáját nyitottam meg.\n\n{x}').format(x=entry['path']))
        elif result is None:
            show_dialog(self.root, "warning", t('Nem találom a fájlt és a mappáját sem ezen az útvonalon:\n\n{x}').format(x=entry['path']))

    def _playable_entry(self):
        """A kiválasztott bejegyzés, ha a fájlja megvan; különben hibaüzenet és None."""
        entry = self._selected_history_entry()
        if entry is None:
            return None
        if entry["path"] in self._missing or not os.path.isfile(entry["path"]):
            show_dialog(self.root, "warning", t('A fájl már nem található ezen az útvonalon:\n\n{x}').format(x=entry['path']))
            return None
        return entry

    def _refresh_default_player_label(self, path):
        """Az alap lejátszó nevét a gombra írja. A lekérdezés háttérben fut, mert lassú lehet."""
        ext = os.path.splitext(path)[1].lower()
        if ext in _PLAYER_NAMES:
            self._set_default_label(_PLAYER_NAMES[ext])
            return
        self._set_default_label(None)

        def work():
            name = default_player_name(path)
            try:
                self.root.after(0, lambda: self._apply_player_label(path, name))
            except (RuntimeError, tk.TclError):
                pass
        threading.Thread(target=work, daemon=True).start()

    def _apply_player_label(self, path, name):
        entry = self._selected_history_entry()
        if entry is not None and os.path.splitext(entry["path"])[1].lower() == \
                os.path.splitext(path)[1].lower():
            self._set_default_label(name)

    def _open_default_selected(self):
        entry = self._playable_entry()
        if entry is not None and not open_default(entry["path"]):
            show_dialog(self.root, "warning", t("Nem sikerült megnyitni a fájlt az "
                        "alapértelmezett programmal."))

    def _open_player_selected(self):
        entry = self._playable_entry()
        if entry is None:
            return
        if self.player_engine == "builtin":
            self._open_builtin_player(entry)
        else:
            self._open_mpv_player(entry)

    def _open_builtin_player(self, entry):
        """A saját, ffmpeg-alapú lejátszó (a Beállításokban választható)."""
        if not HAS_PIL or not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            show_dialog(self.root, "warning", t("A beépített lejátszóhoz ffmpeg kell, de nincs "
                        "telepítve.\n") + ffmpeg_hint() + t("\n\n"
                        "Válthatsz az mpv lejátszóra a Beállításokban, vagy használhatod az "
                        "\"Alap lejátszóval\" gombot."))
            return
        info = probe_video(entry["path"])
        video_ok = bool(info and info["has_video"] and info["w"] >= 2 and info["h"] >= 2)
        if not info or not (video_ok or info["has_audio"]):
            show_dialog(self.root, "warning", t("Ezt a fájlt a beépített lejátszó nem tudja "
                        "lejátszani (nincs benne kép vagy hang, vagy nem olvasható).\n"
                        "Próbáld az \"Alap lejátszóval\" gombot."))
            return
        if not video_ok:
            info["has_video"] = False
            if not HAS_AUDIO:
                show_dialog(self.root, "warning", t("A hang lejátszásához a sounddevice csomag "
                            "kell, de nem érhető el.\nTelepítés: pip3 install sounddevice\n\n"
                            "Addig használhatod az \"Alap lejátszóval\" gombot."))
                return
        old = getattr(self, "_player", None)
        if old is not None and old._alive:
            old.close()
        self._player = VideoPlayer(self.root, entry["path"], history_label(entry), info,
                                   cover=self._hist_thumb_bytes, volume=self.player_volume,
                                   on_volume=self._remember_volume,
                                   geometry=self.player_geom["video" if video_ok else "audio"],
                                   on_geometry=self._remember_player_geom)

    def _open_mpv_player(self, entry):
        """Az mpv lejátszó (külön folyamat, gyors, HDR-képes)."""
        if not shutil.which("mpv"):
            show_dialog(self.root, "warning", t("A lejátszóhoz az mpv kell, de nincs telepítve.\n")
                        + mpv_hint() + t("\n\nVálthatsz a beépített lejátszóra a Beállításokban, "
                        "vagy használhatod az \"Alap lejátszóval\" gombot."))
            return
        old = getattr(self, "_player", None)
        if old is not None and old._alive:
            old.close()
        audio = entry_kind(entry) == "audio"
        try:
            self._player = MpvPlayer(self.root, entry["path"], history_label(entry),
                                     audio_only=audio, volume=self.player_volume,
                                     on_volume=self._remember_volume,
                                     geometry=self.player_geom["audio" if audio else "video"])
        except Exception:
            log_exc("MpvPlayer indítás")
            show_dialog(self.root, "warning", t("Nem sikerült elindítani az mpv lejátszót."))

    def _remember_player_geom(self, kind, geo):
        if kind in self.player_geom and PLAYER_GEO_RE.match(geo or ""):
            self.player_geom[kind] = geo
            self._remember_volume(self.player_volume)  # ugyanaz a késleltetett mentés

    def _remember_volume(self, value):
        self.player_volume = round(value, 3)
        job = getattr(self, "_vol_job", None)
        if job is not None:
            self.root.after_cancel(job)
        self._vol_job = self.root.after(800, self._save_settings)

    def _clear_history(self):
        if not self.history:
            return
        if not show_confirm(self.root, t("Összes előzmény törlése"),
                            t('Biztosan törlöd az összes előzményt ({n_history} bejegyzés)?\n\nA letöltött fájlok a lemezen megmaradnak.').format(n_history=len(self.history)),
                            yes_text=t("Törlés"), no_text=t("Mégse"), danger=True):
            return
        self.history = []
        save_json(HISTORY_FILE, self.history)
        prune_thumbs(self.history)
        self._refresh_history_list()

    def _open_link(self):
        if self._hist_url.startswith(("http://", "https://")):
            webbrowser.open(self._hist_url)


class SettingsMixin:
    """A Beállítások fül és a görgetése."""

    # ---------- sebességkorlát ----------
    def _apply_speed_limit(self):
        """A közös korlát érvényesítése; a futó letöltésekre azonnal hat."""
        on = self.speed_limit_on and self.speed_limit in SPEED_LIMITS_MB
        set_speed_limit(self.speed_limit * 1_000_000 if on else None,
                        lambda: sum(1 for j in list(self.jobs) if j.state == "active") or 1)
        self._refresh_speed_ui()

    def _speed_label(self):
        return t("Sebességkorlát: {x} MB/s").format(x=fmt_mb(self.speed_limit)) \
            if self.speed_limit_on else t("Sebességkorlát: ki")

    def _refresh_speed_ui(self):
        for name, value in (("speed_ctl", "on" if self.speed_limit_on else "off"),):
            ctl = getattr(self, name, None)
            if ctl is not None:
                ctl.set_value(value)
        var = getattr(self, "speed_var", None)
        if var is not None:
            var.set(t("Egyéni…") if self.speed_custom else f"{fmt_mb(self.speed_limit)} MB/s")
            self._show_custom(self.speed_custom_row, self.speed_custom,
                              self.speed_custom_var, fmt_mb(self.speed_limit))
        btn = getattr(self, "speed_btn", None)
        if btn is not None:
            btn.set_text(self._speed_label())
            btn.set_colors(*(("ACCENT", "ACCENT_FG", "ACCENT_HOVER", "")
                             if self.speed_limit_on else
                             ("CONTROL", "TEXT", "CONTROL_HOVER", "BORDER")))

    def set_speed_limit_on(self, mode):
        self.speed_limit_on = mode == "on"
        self._apply_speed_limit()
        self._save_settings()

    def toggle_speed_limit(self):
        self.set_speed_limit_on("off" if self.speed_limit_on else "on")

    def set_speed_limit_value(self, mb, custom=False):
        if mb is None or not SPEED_CUSTOM_RANGE[0] <= mb <= SPEED_CUSTOM_RANGE[1]:
            return False
        self.speed_limit = int(mb) if float(mb).is_integer() else round(mb, 2)
        self.speed_custom = custom
        self._apply_speed_limit()
        self._save_settings()
        return True

    def _on_speed_choice(self, _event=None):
        choice = self.speed_var.get()
        if choice == t("Egyéni…"):
            self.speed_custom = True
            self._show_custom(self.speed_custom_row, True, self.speed_custom_var,
                              fmt_mb(self.speed_limit))
            self.speed_custom_entry.focus_set()
            self.speed_custom_entry.select_range(0, "end")
        else:
            self.set_speed_limit_value(parse_number(choice))

    def _on_speed_custom(self, _event=None):
        ok = self.set_speed_limit_value(parse_number(self.speed_custom_var.get()), custom=True)
        self.speed_custom_msg.configure(
            text="" if ok else t("{a} és {b} MB/s közötti számot adj meg.").format(
                a=fmt_mb(SPEED_CUSTOM_RANGE[0]), b=fmt_mb(SPEED_CUSTOM_RANGE[1])))

    @staticmethod
    def _show_custom(row, show, var, value):
        if show:
            row.grid()
            if not var.get():
                var.set(value)
        else:
            row.grid_remove()

    def _custom_row(self, body, row, unit, on_apply):
        """Egyéni érték sora: kis mező, mértékegység, Enterre vagy kilépéskor érvényes."""
        line = tk.Frame(body, bg=PANEL)
        line.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        tk.Label(line, text=t("Egyéni érték:"), bg=PANEL, fg=GREY,
                 font=(FONT_FAMILY, 12)).pack(side="left", padx=(0, 8))
        var = tk.StringVar()
        box = RoundBox(line, lambda p: tk.Entry(p, textvariable=var, justify="center",
                                                **entry_kw()), height=32, pad=10)
        box.configure(width=90)
        box.pack(side="left")
        tk.Label(line, text=unit, bg=PANEL, fg=GREY, font=(FONT_FAMILY, 12)).pack(
            side="left", padx=(8, 0))
        msg = tk.Label(line, text="", bg=PANEL, fg=DANGER, font=(FONT_FAMILY, 12))
        msg.pack(side="left", padx=(12, 0))
        entry = box.widget
        add_context_menu(entry)
        entry.bind("<Return>", on_apply)
        entry.bind("<FocusOut>", on_apply)
        line.grid_remove()
        return line, var, entry, msg

    # ---------- egyszerre futó letöltések ----------
    def _parallel_text(self):
        if not self.max_parallel:
            return t("Minden letöltés egyszerre fut, nincs várakozó sor.")
        return t('Egyszerre legfeljebb {max_parallel} letöltés fut, a többi sorban vár.').format(
            max_parallel=self.max_parallel)

    def _parallel_value(self):
        if self.parallel_custom:
            return "custom"
        return "unlimited" if not self.max_parallel else str(self.max_parallel)

    def set_parallel_choice(self, value):
        if value == "custom":
            self.parallel_custom = True
            self.par_ctl.set_value("custom")
            self._show_custom(self.par_custom_row, True, self.par_custom_var,
                              str(self.max_parallel or MAX_PARALLEL))
            self.par_custom_entry.focus_set()
            self.par_custom_entry.select_range(0, "end")
            return
        self.parallel_custom = False
        self._set_parallel(0 if value == "unlimited" else int(value))

    def _on_parallel_custom(self, _event=None):
        n = parse_number(self.par_custom_var.get())
        ok = n is not None and n.is_integer() and 1 <= n <= PARALLEL_CUSTOM_MAX
        self.par_custom_msg.configure(text="" if ok else t(
            "1 és {b} közötti egész számot adj meg.").format(b=PARALLEL_CUSTOM_MAX))
        if ok:
            self.parallel_custom = True
            self._set_parallel(int(n))

    def _set_parallel(self, n):
        self.max_parallel = n
        try:
            self.par_ctl.set_value(self._parallel_value())
            self._show_custom(self.par_custom_row, self.parallel_custom, self.par_custom_var,
                              str(n))
            self.dl_sub.configure(text=self._parallel_text())
        except (AttributeError, tk.TclError):
            pass
        self._save_settings()
        self._pump()  # ha nőtt a keret, a várakozók azonnal indulnak

    def set_embed_metadata(self, mode):
        self.embed_metadata = mode == "on"
        self.meta_ctl.set_value(mode)
        self._save_settings()

    def set_sb_mode(self, mode):
        if mode not in SB_MODES:
            return
        self.sb_mode = mode
        self.sb_mode_ctl.set_value(mode)
        self._save_settings()
        self._update_sb_row()

    def _on_sb_categories(self):
        self.sb_categories = [k for k, v in self.sb_cat_vars.items() if v.get()]
        self._save_settings()
        self._update_sb_row()

    def set_notify_popup(self, mode):
        self.notify_popup = mode == "on"
        self.settings["notify_popup"] = self.notify_popup
        self._save_settings()

    def set_toast_anim(self, value):
        if value not in TOAST_ANIMS:
            return
        self.toast_anim = value
        self.settings["toast_anim"] = value
        self.toasts.anim = value
        self._save_settings()
        # rögtön látszik, milyen lesz
        self.toasts.show(t("Így jelenik meg az értesítés"), t('Animáció: {x}').format(x=TOAST_ANIMS[value]),
                         header=t("Minta"))

    def set_temp_local(self, mode):
        self.temp_local = mode == "local"
        self.settings["temp_local"] = self.temp_local
        self._save_settings()
        self._refresh_temp_ui()

    def _refresh_temp_ui(self):
        """A mappa sora csak a "Helyi lemez" módban látszik; mutatja a szabad helyet is."""
        if self.temp_local:
            self.temp_row.grid()
        else:
            self.temp_row.grid_remove()
        base = self.temp_dir or tempfile.gettempdir()
        shown = self.temp_dir or t("Alapértelmezett (a rendszer ideiglenes mappája)")
        try:
            free = shutil.disk_usage(base).free
            info = t('\nSzabad hely: {x}').format(x=format_size(free, True))
        except OSError:
            info = t("\nA mappa most nem érhető el, addig az alapértelmezett lesz használva.")
        self.temp_path_label.configure(text=shown + info)
        self.temp_reset_btn.set_state("normal" if self.temp_dir else "disabled")

    def choose_temp_dir(self):
        release_popups(self.root)
        path = filedialog.askdirectory(
            initialdir=self.temp_dir or tempfile.gettempdir(),
            title=t("Ideiglenes fájlok mappája"))
        if not path:
            return
        if not (os.path.isdir(path) and os.access(path, os.W_OK)):
            show_dialog(self.root, "error", t("Ebbe a mappába nem lehet írni."))
            return
        self.temp_dir = path
        self.settings["temp_dir"] = path
        self._save_settings()
        self._refresh_temp_ui()

    def reset_temp_dir(self):
        self.temp_dir = None
        self.settings["temp_dir"] = None
        self._save_settings()
        self._refresh_temp_ui()

    def set_notify_sound(self, mode):
        self.notify_sound = mode == "on"
        self.settings["notify_sound"] = self.notify_sound
        self._save_settings()

    # ---------- a Beállítások fül ----------
    def _set_scroll_set(self, lo, hi):
        """A görgetősáv csak akkor látszik, ha nem fér el minden beállítás."""
        auto_scrollbar(self.set_bar, lo, hi, row=0, column=1, sticky="ns")
        if hasattr(self, "_set_stack"):
            self._set_stack.relayout_soon()

    def _install_scroll_router(self):
        """Egy helyen kezeljük a görgetést: az egér alatti elemtől felfelé keressük a
        görgethető oldalt. Így nincs olyan elem (felirat, új kártya), amin megakadna."""
        self._scroll_areas = {self.set_canvas: (self._set_wheel, self._set_tab_visible),
                              self.hist_canvas: (self._hist_wheel, self._hist_tab_visible),
                              self.main_canvas: (self._main_wheel, self._main_tab_visible)}
        self.root.bind_all("<MouseWheel>", lambda e: self._route_scroll(e), add="+")
        self.root.bind_all("<Button-4>", lambda e: self._route_scroll(e, -1), add="+")
        self.root.bind_all("<Button-5>", lambda e: self._route_scroll(e, 1), add="+")
        try:
            self.root.bind_all("<TouchpadScroll>", lambda e: self._route_scroll(e, touch=True),
                               add="+")
        except tk.TclError:
            pass  # régebbi Tk, nincs ilyen esemény

    def _scroll_area_at(self, event):
        try:
            w = self.root.winfo_containing(event.x_root, event.y_root)
        except (tk.TclError, KeyError):
            w = None
        if w is None:
            w = event.widget if isinstance(event.widget, tk.Misc) else None
        while w is not None:
            if w in self._scroll_areas:
                return w
            w = getattr(w, "master", None)
        return None

    def _route_scroll(self, event, step=None, touch=False):
        canvas = self._scroll_area_at(event)
        if canvas is None:
            return
        handler, visible = self._scroll_areas[canvas]
        try:
            if not visible():
                return
            if touch:
                self._touchpad_scroll(canvas, event)
            else:
                handler(event, step)
        except tk.TclError:
            pass

    def _scroll_canvas(self, canvas, event, step=None):
        """Egérgörgő: kattanásonként SCROLL_WHEEL_PX képpont, rövid lassuló animációval."""
        if step is None:
            try:
                delta = float(event.delta)
            except (tk.TclError, TypeError, ValueError, AttributeError):
                return
            if delta == 0:
                return
            step = -1 if delta > 0 else 1
            mag = abs(delta)
            if mag >= 120:  # Windows
                step *= max(1, int(mag // 120))
        self._scroll_by(canvas, step * SCROLL_WHEEL_PX, smooth=True)

    @staticmethod
    def _scroll_metrics(canvas):
        """(teljes magasság, látható magasság) képpontban."""
        try:
            region = [float(v) for v in str(canvas.cget("scrollregion")).split()]
            total = region[3] - region[1] if len(region) == 4 else 0
        except (tk.TclError, ValueError):
            total = 0
        if total <= 0:
            box = canvas.bbox("all")
            total = (box[3] - box[1]) if box else 0
        return max(1.0, total), max(1, canvas.winfo_height())

    def _scroll_by(self, canvas, pixels, smooth):
        """Képpontos görgetés. Az érintőpad pontosan követi az ujjat (smooth=False), az
        egérgörgő lassulva csúszik a célig. Képkockánként legfeljebb egyszer rajzolunk."""
        total, visible = self._scroll_metrics(canvas)
        if total <= visible:
            return
        if getattr(canvas, "_sc_job", None) is None:
            # nincs futó mozgás: a jelenlegi helyzetből indulunk (közben a görgetősávval
            # vagy kódból is elmozdulhatott)
            canvas._sc_pos = canvas.yview()[0] * total
            canvas._sc_target = canvas._sc_pos
        canvas._sc_target = max(0.0, min(total - visible, canvas._sc_target + pixels))
        canvas._sc_smooth = smooth
        if getattr(canvas, "_sc_job", None) is None:
            canvas._sc_job = canvas.after(SCROLL_FRAME_MS, lambda: self._scroll_frame(canvas))

    @staticmethod
    def _scroll_frame(canvas):
        canvas._sc_job = None
        try:
            total, visible = SettingsMixin._scroll_metrics(canvas)
            target = max(0.0, min(total - visible, canvas._sc_target))
            diff = target - canvas._sc_pos
            if canvas._sc_smooth and abs(diff) > 0.6:
                canvas._sc_pos += diff * SCROLL_EASE   # lassulva közelít
            else:
                canvas._sc_pos = target
            canvas.yview_moveto(canvas._sc_pos / total)
            if abs(target - canvas._sc_pos) > 0.6:
                canvas._sc_job = canvas.after(SCROLL_FRAME_MS,
                                              lambda: SettingsMixin._scroll_frame(canvas))
        except tk.TclError:
            pass

    def _touchpad_scroll(self, canvas, event):
        """Tk 9 (Mac): az érintőpad és a Magic Mouse <TouchpadScroll> eseményt küld, nem MouseWheel-t."""
        try:
            # a %D két 16 bites előjeles számot tartalmaz: felül a vízszintes, alul a függőleges
            raw = int(event.delta)
        except (TypeError, ValueError):
            return
        dy = raw & 0xFFFF
        if dy >= 0x8000:
            dy -= 0x10000
        if dy == 0:
            return
        self._scroll_by(canvas, -dy * SCROLL_TOUCH_FACTOR, smooth=False)

    def _set_tab_visible(self):
        return self.set_canvas.winfo_ismapped()

    def _set_wheel(self, event, step=None):
        try:
            if not self._set_tab_visible():
                return
            self._scroll_canvas(self.set_canvas, event, step)
        except tk.TclError:
            return

    def _build_settings_tab(self, tab):
        """A Beállítások oldal: csoportokba rendezett kártyák egy görgethető oszlopban.
        Új beállításhoz egy új _card_... függvény kell, és fel kell venni a csoportjába."""
        tab.columnconfigure(0, weight=1)
        ttk.Label(tab, text=t("Beállítások"), style="AboutTitle.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(tab, text=t("Nyelv, megjelenés, értesítések, letöltés, előzmények és védelem"),
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 22))
        # görgethető terület: sok beállítás esetén sem csúszik ki semmi az ablakból
        tab.rowconfigure(2, weight=1)
        wrap = tk.Frame(tab, bg=BG)
        wrap.grid(row=2, column=0, sticky="nsew")
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)
        self.set_canvas = tk.Canvas(wrap, bg=BG, highlightthickness=0, bd=0, height=10)
        self.set_bar = ttk.Scrollbar(wrap, orient="vertical", command=self.set_canvas.yview)
        self.set_canvas.configure(yscrollcommand=self._set_scroll_set)
        self.set_canvas.grid(row=0, column=0, sticky="nsew")
        # minden kártya külön elem a vásznon (CanvasStack): a nem látszók nem rajzolódnak;
        # jobb oldalon hely marad a görgetősávnak, a gombok ne lógjanak bele
        self._set_stack = CanvasStack(self.set_canvas, end_pad=20)
        body = self.set_canvas
        self._set_body = body
        self._set_row = 0

        groups = (
            (t("ÁLTALÁNOS"), (self._card_language, self._card_theme,
                              self._card_notifications)),
            (t("LETÖLTÉS"), (self._card_parallel, self._card_speed, self._card_temp,
                             self._card_metadata,
                             self._card_sponsorblock, self._card_cookies)),
            (t("LEJÁTSZÁS"), (self._card_player,)),
            (t("ELŐZMÉNYEK"), (self._card_history_size, self._card_lock)),
            (t("KARBANTARTÁS"), (self._card_ytdlp, self._card_news)),
        )
        for title, builders in groups:
            self._set_stack.add(tk.Label(body, text=title, bg=BG, fg=GREY,
                                         font=get_font(10, "bold"), anchor="w"),
                                top=4 if self._set_row == 0 else 12, bottom=6, padx=4)
            self._set_row += 1
            for build in builders:
                build(self._new_card())
        self._about_refresh()


    # ---------- a Beállítások kártyái ----------
    def _new_card(self):
        """Új kártya a Beállítások oszlopába; a tartalma a visszaadott keretbe kerül."""
        card = RoundCard(self._set_body)
        self._set_stack.add(card, bottom=12)
        self._set_row += 1
        card.inner.configure(padx=18, pady=14)
        card.inner.columnconfigure(0, weight=1)
        return card.inner

    @staticmethod
    def _card_head(body, row, title, info=None):
        """Kártya címe, mellette az info ikon (a leírás csak rámutatva jelenik meg)."""
        line = tk.Frame(body, bg=PANEL)
        line.grid(row=row, column=0, sticky="w")
        tk.Label(line, text=title, bg=PANEL, fg=TEXT, font=get_font(14, "bold")).pack(
            side="left")
        if info:
            InfoIcon(line, info).pack(side="left", padx=(8, 0))
        return line

    @staticmethod
    def _card_combo(body, row, variable, values, on_select):
        """Teljes szélességű lenyíló lista a kártya címe alatt."""
        box = RoundBox(body, lambda p: ttk.Combobox(
            p, textvariable=variable, state="readonly", style="Flat.TCombobox",
            values=list(values)))
        box.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        box.widget.bind("<<ComboboxSelected>>", on_select)
        return box.widget

    def _card_language(self, body):
        self._card_head(body, 0, t("Nyelv"),
                        t("Az alkalmazás nyelve. Automatikus beállításnál a rendszer nyelvét "
                          "követi, ha az magyar, angol vagy német, egyébként angol. A váltás az "
                          "app újraindítása után lép életbe."))
        self._lang_options = [("auto", t("Automatikus (a rendszer nyelve)"))] + \
            list(LANGUAGES.items())
        self.lang_var = tk.StringVar(value=dict(self._lang_options)[self.language])
        self._card_combo(body, 1, self.lang_var, [label for _, label in self._lang_options],
                         lambda e: self.set_language_choice(next(
                             k for k, v in self._lang_options if v == self.lang_var.get())))

    def _card_theme(self, body):
        self._card_head(body, 0, t("Téma"), t("Az alkalmazás témájának kiválasztása."))
        self.style_var = tk.StringVar(value=THEME_STYLES[self.theme_style])
        self.style_box = self._card_combo(
            body, 1, self.style_var, THEME_STYLES.values(),
            lambda e: self.set_theme_style(next(
                k for k, v in THEME_STYLES.items() if v == self.style_var.get())))
        self.theme_ctl = SegmentedControl(
            body, [("dark", t("Sötét")), ("light", t("Világos")), ("system", t("Rendszer"))],
            self.theme_mode, self.set_theme_mode, width=300, height=32)
        self.theme_ctl.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def _card_notifications(self, body):
        self._card_head(body, 0, t("Értesítések"),
                        t("A letöltések végén az app egy kis értesítést mutat a sarokban, és "
                          "hangjelzést ad. Ezeket külön kapcsolhatod, és azt is beállíthatod, "
                          "hogyan jelenjen meg az értesítés."))
        _, self.notify_popup_ctl = labeled_control(
            body, 1, t("Értesítések a letöltések végén"), on_off_options(),
            "on" if self.notify_popup else "off", self.set_notify_popup, 130)
        _, self.notify_sound_ctl = labeled_control(
            body, 2, t("Hangjelzés a letöltések végén"), on_off_options(),
            "on" if self.notify_sound else "off", self.set_notify_sound, 130)
        _, self.toast_anim_ctl = labeled_control(
            body, 3, t("Értesítések animációja"), list(TOAST_ANIMS.items()),
            self.toast_anim, self.set_toast_anim, 260)

    def _card_temp(self, body):
        """Ideiglenes fájlok helye: NAS-ra letöltéshez a helyi lemez kíméli a hálózati tárat."""
        self._card_head(body, 0, t("Ideiglenes fájlok helye"),
                        t("Az alkalmazás letöltés közben ideiglenes fájlokkal dolgozik. Ez néha "
                          "gondot jelenthet, ha közvetlenül NAS gépre töltesz le, például a NAS "
                          "logja megtelik a letöltött videók bejegyzéseivel. Ennél a beállításnál "
                          "kijelölhetsz egy mappát, ahova az ideiglenes fájlok kerülnek, így a "
                          "célmappába csak a kész videó lesz átmásolva. Az ideiglenes fájlok "
                          "automatikusan törlődnek a videó sikeres letöltése és megszakítás után."))
        self.temp_ctl = SegmentedControl(
            body, [("local", t("Ideiglenes mappában")), ("folder", t("Célmappában"))],
            "local" if self.temp_local else "folder", self.set_temp_local,
            width=300, height=32)
        self.temp_ctl.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.temp_row = tk.Frame(body, bg=PANEL)
        self.temp_row.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.temp_row.columnconfigure(0, weight=1)
        self.temp_path_label = tk.Label(self.temp_row, text="", bg=PANEL, fg=TEXT,
                                        justify="left", anchor="w", wraplength=300,
                                        font=(FONT_FAMILY, 12))
        self.temp_path_label.grid(row=0, column=0, sticky="w")
        btns = tk.Frame(self.temp_row, bg=PANEL)
        btns.grid(row=0, column=1, sticky="e", padx=(10, 0))
        secondary_button(btns, t("Mappa…"), self.choose_temp_dir, width=90, height=32,
                         font=(FONT_FAMILY, 12)).pack(side="left")
        self.temp_reset_btn = secondary_button(btns, t("Alap"), self.reset_temp_dir, width=70,
                                               height=32, font=(FONT_FAMILY, 12))
        self.temp_reset_btn.pack(side="left", padx=(6, 0))
        self._refresh_temp_ui()

    def _card_parallel(self, body):
        self._card_head(body, 0, t("Egyszerre futó letöltések"),
                        t("Ennyi letöltés fut egyszerre, a többi sorban vár, és akkor indul, "
                          "amikor egy elkészül. Több egyszerre futó letöltés nem mindig "
                          "gyorsabb, mert osztoznak az interneten. Korlátlannál minden "
                          "letöltés azonnal indul."))
        self.par_ctl = SegmentedControl(
            body, [("3", "3"), ("5", "5"), ("10", "10"), ("custom", t("Egyéni")),
                   ("unlimited", t("Korlátlan"))],
            self._parallel_value(), self.set_parallel_choice, width=300, height=32)
        self.par_ctl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        (self.par_custom_row, self.par_custom_var, self.par_custom_entry,
         self.par_custom_msg) = self._custom_row(body, 2, t("letöltés"),
                                                 self._on_parallel_custom)
        self._show_custom(self.par_custom_row, self.parallel_custom, self.par_custom_var,
                          str(self.max_parallel))

    def _card_speed(self, body):
        """Sebességkorlát: az összes letöltés együtt legfeljebb ennyivel tölthet."""
        self._card_head(body, 0, t("Sebességkorlát"),
                        t("Ha bekapcsolod, a letöltések együtt legfeljebb ennyi sebességgel "
                          "töltenek, így a többi gép és alkalmazás is kényelmesen használhatja "
                          "az internetet. Futó letöltésre is azonnal hat. Gyorsan ki- és "
                          "bekapcsolhatod az Előzmények oldalon is."))
        self.speed_ctl = SegmentedControl(body, on_off_options(),
                                          "on" if self.speed_limit_on else "off",
                                          self.set_speed_limit_on, width=130, height=30)
        self.speed_ctl.grid(row=0, column=1, sticky="e")
        self.speed_var = tk.StringVar()
        self._card_combo(body, 1, self.speed_var,
                         [f"{v} MB/s" for v in SPEED_LIMITS_MB] + [t("Egyéni…")],
                         self._on_speed_choice)
        (self.speed_custom_row, self.speed_custom_var, self.speed_custom_entry,
         self.speed_custom_msg) = self._custom_row(body, 2, "MB/s", self._on_speed_custom)
        self._refresh_speed_ui()

    def _card_metadata(self, body):
        """Adatok a fájlba: borító, cím, előadó (mp3), fejezetek (videó)."""
        self._card_head(body, 0, t("Adatok beégetése a fájlba"),
                        t("A letöltött fájlba belekerül a borítókép, a cím, az előadó vagy a "
                          "feltöltő, videónál a fejezetek is. Így a zenelejátszók és a "
                          "médiaszerverek (például Plex, Jellyfin) szépen megjelenítik."))
        self.meta_ctl = SegmentedControl(body, on_off_options(),
                                         "on" if self.embed_metadata else "off",
                                         self.set_embed_metadata, width=130, height=30)
        self.meta_ctl.grid(row=0, column=1, sticky="e")

    def _card_sponsorblock(self, body):
        """SponsorBlock: mit kezdjen a jelölt részekkel, és mely részekkel."""
        self._card_head(body, 0, t("SponsorBlock"),
                        t("A SponsorBlock a nézők által jelölt részeket ismeri YouTube "
                          "videókban, például a szponzorált részeket vagy a bevezetőket. Ha egy "
                          "videóban vannak ilyenek, a letöltő oldalon egy pipával kérheted, hogy "
                          "az app kivágja vagy fejezetként jelölje őket. Itt állíthatod be, mi "
                          "történjen, és mely részekkel. Áttűnéssel a vágás helyén egy rövid "
                          "elsötétülés és felirat jelzi, hogy kimaradt valami. Ez lassabb, mert "
                          "az egész videót újra kell kódolni."))
        self.sb_mode_ctl = SegmentedControl(
            body, [(k, t(v)) for k, v in SB_MODES.items()], self.sb_mode, self.set_sb_mode,
            width=300, height=32)
        self.sb_mode_ctl.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        grid = tk.Frame(body, bg=PANEL)
        grid.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        grid.columnconfigure((0, 1), weight=1, uniform="sb")
        self.sb_cat_vars = {}
        for i, (key, label) in enumerate(SB_CATEGORIES.items()):
            var = tk.BooleanVar(value=key in self.sb_categories)
            make_check(grid, t(label), var, self._on_sb_categories).grid(
                row=i // 2, column=i % 2, sticky="w", pady=2)
            self.sb_cat_vars[key] = var

    def _card_cookies(self, body):
        """Böngésző sütik: alapból Nincs, csak ha egy oldalhoz szükség lenne rá."""
        self._card_head(body, 0, t("Böngésző sütik használata"),
                        t("Ezt alapból hagyd a „Nincs” lehetőségen. Csak akkor válts, ha egy "
                          "oldal bejelentkezést vagy sütit kér a tartalmak megjelenítéséhez."))
        # a mentett érték a belső név ("Nincs" vagy a böngésző), a lista a lefordított nevet mutatja
        self.browser_shown = tk.StringVar(value=browser_label(self.browser.get()))
        self._card_combo(body, 1, self.browser_shown, [browser_label(b) for b in BROWSERS],
                         lambda e: self.browser.set(next(
                             b for b in BROWSERS if browser_label(b) == self.browser_shown.get())))

    def _card_player(self, body):
        self._card_head(body, 0, t("Beépített lejátszó"),
                        t("Az mpv egy modernebb lejátszóval indítja a letöltött videókat. "
                          "Támogatja a HDR formátumokat, 4K és 60 fps videók esetén is megfelelő "
                          "teljesítményt nyújt, és több beállítási lehetősége van (jobb klikk a "
                          "videón). Az ffmpeg egy egyszerűbb beépített lejátszó, kevesebb "
                          "funkcióval és kevésbé jó teljesítménnyel, főleg régebbi gépekhez "
                          "ajánlott."))
        self.player_engine_var = tk.StringVar(value=PLAYER_ENGINES[self.player_engine])
        self._card_combo(body, 1, self.player_engine_var, PLAYER_ENGINES.values(),
                         self.set_player_engine)

    def _card_history_size(self, body):
        self._card_head(body, 0, t("Előzmények mérete"),
                        t("Itt az előzmények listában szereplő bejegyzések mennyiségét "
                          "állíthatod be. Ha a lista megtelt, az utolsó bejegyzés automatikusan "
                          "eltűnik a listából. Ha nagyobb értékről kisebbre állítod, szintén "
                          "eltűnnek a régebbi bejegyzések."))
        self.history_limit_var = tk.StringVar(
            value=dict(HISTORY_LIMITS).get(self.history_limit, HISTORY_LIMITS[1][1]))
        self._card_combo(body, 1, self.history_limit_var, [lbl for _, lbl in HISTORY_LIMITS],
                         self.set_history_limit)

    def _card_lock(self, body):
        self._build_lock_section(body, 0)

    def _card_ytdlp(self, body):
        self._card_head(body, 0, t("yt-dlp frissítése"),
                        t("Ahhoz, hogy a letöltő megfelelően működjön, időnként frissíteni "
                          "szükséges a yt-dlp plugint."))
        label_font = (FONT_FAMILY, 13)
        ver = tk.Frame(body, bg=PANEL)
        ver.grid(row=1, column=0, sticky="w", pady=(4, 0))
        tk.Label(ver, text=t('Telepített verzió: {ytdlp_version}').format(
            ytdlp_version=YTDLP_VERSION), bg=PANEL, fg=TEXT, font=label_font).pack(side="left")
        self.update_label = tk.Label(ver, text="", bg=PANEL, fg=ACCENT_TEXT, font=label_font)
        self.update_label.pack(side="left", padx=(10, 0))
        self.status_label = tk.Label(body, text="", bg=PANEL, fg=TEXT, justify="left",
                                     wraplength=440, font=(FONT_FAMILY, 12))
        self.status_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        btns = tk.Frame(body, bg=PANEL)
        btns.grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.check_btn = secondary_button(btns, t("Frissítés keresése"), self.check_ytdlp_update,
                                          width=170, height=36, font=label_font)
        self.check_btn.pack(side="left")
        self.update_btn = RoundButton(btns, t("Frissítés letöltése"), self.download_ytdlp_update,
                                      width=180, height=36, font=label_font)
        self.update_btn.pack(side="left", padx=(10, 0))

    def _card_news(self, body):
        self._card_head(body, 0, t("Újdonságok"),
                        t("Visszamenőleges verziótörténet az utókor számára."))
        btns = tk.Frame(body, bg=PANEL)
        btns.grid(row=1, column=0, sticky="w", pady=(8, 0))
        small = (FONT_FAMILY, 13)
        secondary_button(btns, t("Verziótörténet"), self.show_changelog, width=150,
                         height=36, font=small).pack(side="left")
        if not is_mac():  # Macen az alkalmazásmenü "About" pontja nyitja
            secondary_button(btns, t("Névjegy"), self.show_about, width=110, height=36,
                             font=small).pack(side="left", padx=(10, 0))

class UpdateMixin:
    """About ablak és az yt-dlp frissítése."""

    # ---------- Névjegy ablak (Macen az alkalmazásmenü "About Vid-Ripper" pontja) ----------
    def _setup_about_menu(self):
        if not is_mac():  # máshol a Beállítások végén a Névjegy gomb nyitja
            return
        try:
            self.root.createcommand("tkAboutDialog", self.show_about)
            # a Tk ettől teszi az alkalmazásmenübe a "Settings…" pontot, Cmd+, gyorsbillentyűvel
            self.root.createcommand("::tk::mac::ShowPreferences", self.show_settings)
        except Exception:
            log_exc("_setup_about_menu")

    def show_settings(self):
        """Beállítások oldal (Macen az alkalmazásmenüből vagy Cmd+, billentyűvel)."""
        try:
            self.root.deiconify()
            self._nav_go("set")
            bring_to_front(self.root)
        except tk.TclError:
            pass

    def _update_available(self):
        return bool(self._latest_ytdlp and is_newer(self._latest_ytdlp, YTDLP_VERSION))

    def _update_text(self):
        if self._installed_ver and is_newer(self._installed_ver, YTDLP_VERSION):
            return t("(letöltve, újraindítás után lép életbe)")
        if self._update_available():
            return t("(frissítés érhető el)")
        return ""

    def can_check_update(self):
        return not self._checking and self._update_busy is None

    def can_download_update(self):
        return (not self._checking and self._update_busy is None
                and self._update_available() and self._installed_ver != self._latest_ytdlp)

    def _refresh_update_banner(self):
        banner = getattr(self, "ytdlp_banner", None)
        if banner is None:
            return
        try:
            if self.can_download_update():
                banner.grid()
            elif self._update_busy is None:
                banner.grid_remove()
        except tk.TclError:
            pass

    def _open_update_settings(self):
        """A piros sávra kattintva: Beállítások, a yt-dlp frissítés kártyájához görgetve."""
        self._switch_tab("3")

        def scroll():
            try:
                top, _h = self._set_stack.bounds(self.update_btn) or (0, 0)
                total = max(1, self._set_stack.total)
                self.set_canvas.yview_moveto(max(0.0, (top - 40) / total))
            except (tk.TclError, AttributeError):
                pass
        self.root.after(80, scroll)

    def _periodic_update_check(self):
        """Ha sokáig nyitva van az app, időnként újra megnézi, van-e új yt-dlp."""
        self._start_update_check()
        self.root.after(UPDATE_CHECK_INTERVAL_MS, self._periodic_update_check)

    def _about_refresh(self):
        """A frissítéssel kapcsolatos feliratok és gombok állapotának újraolvasása."""
        self._refresh_update_banner()
        try:
            self.update_label.configure(text=self._update_text())
            self.status_label.configure(text=self._update_status)
            self.check_btn.set_state("normal" if self.can_check_update() else "disabled")
            self.update_btn.set_state("normal" if self.can_download_update() else "disabled")
        except (tk.TclError, AttributeError):
            pass

    def _set_update_status(self, text):
        self._update_status = text
        self._about_refresh()

    def _load_about_icon(self):
        """Az app ikonja az About ablakhoz. Ha nincs meg az icon.png, ikon nélkül jelenik meg."""
        if self._about_icon_img is not None:
            return self._about_icon_img
        path = resource_path("icon.png")
        if not os.path.exists(path):
            return None
        try:
            if HAS_PIL:
                img = Image.open(path).convert("RGBA").resize((112, 112), Image.LANCZOS)
                self._about_icon_img = ImageTk.PhotoImage(img)
            else:
                self._about_icon_img = tk.PhotoImage(file=path).subsample(9)
        except Exception:
            self._about_icon_img = None
        return self._about_icon_img

    def show_about(self):
        win = self._about_win
        if win is not None and win.winfo_exists():
            bring_to_front(win)
            return
        self._about_win = AboutDialog(self.root, self, self._load_about_icon())

    # ---------- Újdonságok (verziótörténet és a főképernyő értesítése) ----------
    def show_changelog(self):
        """Megnyitja az Újdonságok ablakot. Az első megnyitás után az értesítés eltűnik."""
        win = self._changelog_win
        if win is not None and win.winfo_exists():
            bring_to_front(win)
        else:
            self._changelog_win = ChangelogDialog(self.root)
        self.seen_version = APP_VERSION
        self._refresh_news_pill()
        self._save_settings()

    def _refresh_news_pill(self):
        """Az értesítés addig látszik, amíg az aktuális verzió újdonságait meg nem nyitották."""
        show = self.seen_version != APP_VERSION
        if show and not self.news_pill.winfo_ismapped():
            self.news_pill.pack(pady=(0, 8))
        elif not show and self.news_pill.winfo_ismapped():
            self.news_pill.pack_forget()

    # ---------- yt-dlp frissítés (keresés, letöltés, telepítés) ----------
    def check_ytdlp_update(self):
        """A "Frissítés keresése" gomb."""
        self._start_update_check(manual=True)

    def _start_update_check(self, manual=False):
        if self._checking:
            return
        self._checking = True
        if manual:
            self._set_update_status(t("Frissítés keresése..."))
        else:
            self._about_refresh()
        threading.Thread(target=self._check_update, args=(manual,), daemon=True).start()

    def _check_update(self, manual):
        release = fetch_ytdlp_release()
        self.root.after(0, self._update_check_done, release, manual)

    def _update_check_done(self, release, manual):
        self._checking = False
        if release:
            self._latest_release = release
            self._latest_ytdlp = release["version"]
        if manual:
            if not release:
                self._update_status = t("Nem sikerült megnézni az új verziót. Van internet?")
            elif not self._update_available():
                self._update_status = t("Az yt-dlp naprakész.")
            elif self._installed_ver == self._latest_ytdlp:
                self._update_status = (t("Az új verzió már le van töltve, indítsd újra az "
                                       "appot, hogy életbe lépjen."))
            else:
                self._update_status = t('Új verzió érhető el: {latest_ytdlp}').format(latest_ytdlp=self._latest_ytdlp)
        self._about_refresh()

    def download_ytdlp_update(self):
        """A "Frissítés letöltése" gomb: az új yt-dlp letöltése, ellenőrzése, telepítése."""
        release = self._latest_release
        if not release or not self.can_download_update():
            return
        self._update_busy = "download"
        self._set_update_status(t("Letöltés indul..."))
        threading.Thread(target=self._do_update, args=(release,), daemon=True).start()

    def _do_update(self, release):
        last = [None]

        def progress(done, total):
            pct = int(done * 100 / total) if total else None
            if pct != last[0]:
                last[0] = pct
                self.root.after(0, self._set_update_status,
                                t('Letöltés: {pct}%').format(pct=pct) if pct is not None else t("Letöltés..."))

        try:
            data = download_ytdlp_wheel(release, progress)
            self.root.after(0, self._set_update_status, t("Ellenőrzés és telepítés..."))
            install_ytdlp_wheel(data, YTDLP_LIB_DIR, release["version"])
            self.root.after(0, self._update_install_done, release["version"], None)
        except Exception as e:
            own = isinstance(e, RuntimeError)  # a saját, már magyar hibaüzeneteink
            text = str(e) if own else explain_error(str(e), self.browser.get())[0]
            self.root.after(0, self._update_install_done, release["version"], text)

    def _update_install_done(self, version, error):
        self._update_busy = None
        if error:
            self._set_update_status(t("A frissítés nem sikerült."))
            show_dialog(self.root, "error", t("Az yt-dlp frissítése nem sikerült.\n\n") + error)
            return
        self._installed_ver = version
        self._set_update_status(t('Kész: a(z) {version} verzió letöltve. Indítsd újra az appot, hogy életbe lépjen.').format(version=version))


class DownloaderMixin:
    """A Letöltő fül: link, adatok lekérése, lejátszási lista."""

    # ---------- a Letöltő fül görgetése ----------
    def _main_scroll_set(self, lo, hi):
        """A görgetősáv csak akkor látszik, ha a fül tartalma nem fér el (pl. teljes képernyőn
        Windowson, nagyobb skálázásnál): így a Letöltés gomb sosem csúszik ki az ablakból."""
        auto_scrollbar(self.main_bar, lo, hi, row=0, column=1, sticky="ns")

    def _main_tab_visible(self):
        return self.main_canvas.winfo_ismapped()

    def _main_wheel(self, event, step=None):
        try:
            if self._main_tab_visible():
                self._scroll_canvas(self.main_canvas, event, step)
        except tk.TclError:
            return

    def _build_downloader_tab(self, tab):
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        self.main_canvas = tk.Canvas(tab, bg=BG, highlightthickness=0, bd=0, height=10)
        self.main_bar = ttk.Scrollbar(tab, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self._main_scroll_set)
        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        main = ttk.Frame(self.main_canvas)
        win = self.main_canvas.create_window((0, 0), window=main, anchor="nw")
        track_scroll_body(self.main_canvas, main)
        self.main_canvas.bind("<Configure>", lambda e: self.main_canvas.itemconfigure(
            win, width=max(e.width - 22, 100)))
        self._main_body = main
        main.columnconfigure(0, weight=1)

        ttk.Label(main, text=t("Videó kiválasztása"), style="AboutTitle.TLabel").grid(
            row=0, column=0, sticky="w")
        ttk.Label(main, text=t("Másold be a videó linkjét, vagy több linket soronként."),
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 22))

        # figyelmeztetés, ha van új yt-dlp (régi yt-dlp-vel egyre több oldal nem működik)
        self.ytdlp_banner = RoundButton(
            main, t("⚠  Új yt-dlp frissítés érhető el, telepítsd a Beállításokban."),
            self._open_update_settings, height=38, bg="DANGER", fg="#ffffff", hover="DANGER",
            font=get_font(13, "bold"))
        self.ytdlp_banner.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        self.ytdlp_banner.grid_remove()

        # (a böngésző süti választó az About ablakban van, alapból "Nincs")

        # link: saját kártyában
        link_card = RoundCard(main)
        link_card.grid(row=5, column=0, sticky="ew", pady=(0, 16))
        link_card.inner.configure(padx=16, pady=14)
        link_card.inner.columnconfigure(0, weight=1)
        tk.Label(link_card.inner, text=t("Videó linkje"), bg=PANEL, fg=TEXT,
                 font=get_font(14, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        url_row = tk.Frame(link_card.inner, bg=PANEL)
        url_row.grid(row=1, column=0, sticky="ew")
        url_row.columnconfigure(0, weight=1)

        def clear_url():
            self.url.set("")
            url_box.widget.focus_set()

        url_box = RoundBox(url_row, lambda p: tk.Entry(p, textvariable=self.url, **entry_kw()),
                           height=36, pad=12, clear_command=clear_url)
        url_box.grid(row=0, column=0, sticky="ew")
        add_context_menu(url_box.widget)
        url_box.widget.bind("<<Paste>>", self._paste_url)
        self.url.trace_add("write", lambda *_: url_box.set_clear_visible(bool(self.url.get())))
        self._url_box = url_box
        # egy kiemelés oldalanként: itt csak a Letöltés gomb színes, ez másodlagos
        self.fetch_btn = secondary_button(url_row, t("Videó adatai"), self.fetch_info, width=130,
                                          height=36)
        self.fetch_btn.grid(row=0, column=1, padx=(10, 0))
        # az adatlekérés haladása: csak lekérés közben látszik
        self.fetch_bar = RoundProgress(url_row, height=6)
        self.fetch_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self.fetch_bar.grid_remove()

        # videó előnézet (bélyegkép + adatok), kezdetben rejtve
        self.preview = PreviewCard(main)
        self.preview.grid(row=6, column=0, sticky="ew", pady=(0, 16))
        self.preview.grid_remove()

        # a letöltés beállításai: egy kártya, soronként címkével és értékkel
        card = RoundCard(main)
        card.grid(row=7, column=0, sticky="ew", pady=(0, 18))
        self._opt_inner = card.inner
        self._opt_inner.columnconfigure(0, weight=1)
        self._build_resolution_row()
        self._build_quality_row()
        self._build_clip_row()
        self._build_subtitle_row()
        self._build_live_row()
        self._build_sponsorblock_row()
        self._build_folder_row()
        self._update_audio_ui()

        # letöltés
        # a fő gomb jobbra, a Mac-es szokás szerint (mellette balra a Megszakítás)
        dl_row = ttk.Frame(main)
        dl_row.grid(row=9, column=0, sticky="ew")
        dl_row.columnconfigure(0, weight=1)
        self.cancel_btn = secondary_button(dl_row, t("Megszakítás"), self.cancel_action,
                                      width=130, height=44, font=(FONT_FAMILY, 14))
        self.cancel_btn.grid(row=0, column=1, padx=(0, 10))
        self.cancel_btn.grid_remove()
        self.dl_btn = RoundButton(dl_row, t("\u2193  Letöltés"), self.start_download, width=200,
                                  height=44, font=(FONT_FAMILY, 14, "bold"))
        self.dl_btn.grid(row=0, column=2, sticky="e")
        self.dl_btn.set_state("disabled")

        self.status_label_main = ttk.Label(main, textvariable=self.status, style="Status.TLabel",
                                           wraplength=500)
        self.status_label_main.grid(row=10, column=0, sticky="w", padx=(4, 0), pady=(18, 0))
        # letöltésre kész állapot: a mentési név és a teendő külön sorban, más színnel
        ready = tk.Frame(main, bg=BG)
        ready.grid(row=10, column=0, sticky="ew", padx=(4, 0), pady=(18, 0))
        ready.columnconfigure(0, weight=1)
        tk.Label(ready, text=t("Mentés ezen a néven"), bg=BG, fg=GREY, anchor="w",
                 font=get_font(11)).grid(row=0, column=0, sticky="w")
        self.ready_name = tk.Label(ready, text="", bg=BG, fg=TEXT, anchor="w", justify="left",
                                   wraplength=500, font=get_font(13, "bold"))
        self.ready_name.grid(row=1, column=0, sticky="w", pady=(2, 10))
        self.ready_hint = tk.Label(ready, text=t("Válassz felbontást, majd nyomd meg a Letöltés "
                                   "gombot."), bg=BG, fg=ACCENT_TEXT, anchor="w",
                                   font=get_font(12))
        self.ready_hint.grid(row=2, column=0, sticky="w")
        self.ready_box = ready
        ready.bind("<Configure>", lambda e: self.ready_name.configure(
            wraplength=max(300, e.width - 8)), add="+")
        ready.grid_remove()



    # ---------- a letöltő oldal beállítás-sorai ----------
    def _option_row(self, index, text):
        """Egy sor a letöltés beállításai kártyán: elválasztó vonal, balra a felirat.
        (a sor kerete, a felirat sora, amibe jobbra a vezérlő kerül)"""
        row = tk.Frame(self._opt_inner, bg=PANEL)
        row.grid(row=index, column=0, sticky="ew")
        if index:
            tk.Frame(row, bg=CHIP, height=1).pack(side="top", fill="x")
        line = tk.Frame(row, bg=PANEL)
        line.pack(fill="x", padx=14, pady=10)
        tk.Label(line, text=text, bg=PANEL, fg=TEXT, font=(FONT_FAMILY, 13)).pack(side="left")
        return row, line

    def _build_resolution_row(self):
        res_row, line = self._option_row(0, t("Felbontás"))
        # a lehetőségek listáját ez a (nem látható) lenyíló tartja, a választás a kapszulán megy
        self.res_box = ttk.Combobox(line, textvariable=self.resolution, state="disabled",
                                    style="Chip.TCombobox", values=[], width=14,
                                    font=(FONT_FAMILY, 13))
        self.res_box.bind("<<ComboboxSelected>>", lambda e: self._on_resolution_change())
        self.res_seg_line = tk.Frame(res_row, bg=PANEL)
        self.res_seg_line.pack(fill="x", padx=14, pady=(0, 12))
        self.res_seg = None
        self.res_hint = tk.Label(self.res_seg_line, text=t("Előbb kérd le a videó adatait."),
                                 bg=PANEL, fg=GREY, font=(FONT_FAMILY, 12), anchor="w")
        self.res_hint.pack(fill="x")
        self.resolution.trace_add("write", lambda *a: self._res_seg_select())
        # HDR: csak akkor látszik, ha a videónak van HDR változata
        self.hdr_check = make_check(res_row, t("letöltés HDR minőségben"), self.hdr,
                                    self._on_hdr_change)
        # szűk ablakban a négyzet a felbontás alatt kap külön sort
        self.hdr_line = tk.Frame(res_row, bg=PANEL)
        self.hdr_row_parent = line
        line.bind("<Configure>", lambda e: self._place_hdr())


    def _build_quality_row(self):
        # a hangminőség csak a "Csak audio" választásakor látszik
        self.quality_row, line = self._option_row(1, t("Hangminőség"))
        qbox = ttk.Combobox(line, textvariable=self.quality, state="readonly",
                            style="Chip.TCombobox", values=QUALITIES, width=14,
                            font=(FONT_FAMILY, 13))
        qbox.pack(side="right")
        qbox.bind("<<ComboboxSelected>>", lambda e: self._refresh_details())




    def _build_folder_row(self):
        """Mappa: szerkeszthető lenyíló lista, beírható útvonal és a legutóbbi mappák."""
        _, line = self._option_row(5, t("Letöltési mappa"))
        secondary_button(line, t("Tallózás…"), self.choose_folder, width=100, height=28,
                    font=(FONT_FAMILY, 12)).pack(side="right", padx=(8, 0))
        self.folder_combo = ttk.Combobox(line, textvariable=self.folder,
                                         style="Chip.TCombobox", font=(FONT_FAMILY, 13),
                                         values=self._recent_values())
        self.folder_combo.pack(side="right", fill="x", expand=True, padx=(16, 0))
        add_context_menu(self.folder_combo)

    # ---------- segédek ----------
    def _extra_opts(self):
        opts = {}
        name = self.browser.get()
        if name and name != "Nincs":
            opts["cookiesfrombrowser"] = (name,)
        if HAS_IMPERSONATE:
            opts["impersonate"] = ImpersonateTarget.from_str("chrome")
        return opts

    def _recent_values(self):
        """A lenyílóban csak a most is létező mappák látszanak. Zárolt előzményeknél egy sem."""
        if self.hist_locked:
            return []
        return [f for f in self.recent_folders if os.path.isdir(f)]

    def _remember_folder(self, folder):
        self.recent_folders = add_recent_folder(self.recent_folders, folder)
        self.folder_combo.configure(values=self._recent_values())
        self._schedule_save()

    def choose_folder(self):
        path = filedialog.askdirectory(initialdir=self.folder.get())
        if path:
            self.folder.set(path)

    def set_status(self, text):
        self.status.set(text)
        box = getattr(self, "ready_box", None)
        if box is not None and box.winfo_manager():
            box.grid_remove()
            self.status_label_main.grid()

    def set_busy(self, busy):
        self.busy = busy
        if not busy:
            self._stop_fetch_ui()
        self.fetch_btn.set_state("disabled" if busy else "normal")
        if busy:
            self.dl_btn.set_state("disabled")
        else:
            self.dl_btn.set_state("normal" if self.res_box["values"] else "disabled")

    def _thumb_image(self, data, size=(168, 94), bg=None):
        """Lekerekített, a kártya színére illesztett bélyegkép (PIL kép) vagy None."""
        if not (HAS_PIL and data):
            return None
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            img.thumbnail(size)
            mask = Image.new("L", img.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, img.size[0] - 1, img.size[1] - 1), radius=10, fill=255)
            card = Image.new("RGB", img.size, hex_rgb(bg or PANEL))
            card.paste(img, (0, 0), mask)
            return card
        except Exception:
            return None

    def _make_thumbnail(self, data, size=(168, 94)):
        img = self._thumb_image(data, size)
        if img is None:
            return None
        try:
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    # ---------- videó adatainak lekérése ----------
    def _is_audio(self):
        return self.resolution.get() == AUDIO_LABEL

    def _selected_height(self):
        if self._is_audio():
            return None
        text = self.resolution.get().replace("p", "")
        return int(text) if text.isdigit() else None

    def _selected_kbps(self):
        digits = re.findall(r"\d+", self.quality.get())
        return int(digits[0]) if digits else int(DEFAULT_QUALITY.split()[0])

    def _hdr_available(self):
        return hdr_heights(self.info_data or {})

    def _hdr_wanted(self):
        return bool(self.hdr.get()) and not self._is_audio() and bool(self._hdr_available())

    def _update_audio_ui(self):
        """A hangminőség menü csak a "Csak audio" választásakor látszik,
        a HDR négyzet csak ha van HDR változat és nem hangot töltünk."""
        if self._is_audio():
            self.quality_row.grid()
        else:
            self.quality_row.grid_remove()
        self._hdr_show = bool(self.info_data) and not self._is_audio() \
            and not self._is_live() and bool(self._hdr_available())
        self._place_hdr()
        info = self.info_data or {}
        live = self._is_live()
        if info.get("duration") and not live:
            self.clip_row.grid()
        else:
            self.clip_row.grid_remove()
        if self._sub_keys and not self._is_audio() and not live:
            self.sub_row.grid()
        else:
            self.sub_row.grid_remove()
        if live:
            self.live_row.grid()
        else:
            self.live_row.grid_remove()
        self._update_sb_row()
        if hasattr(self, "dl_btn"):
            self.dl_btn.set_text(t("●  Felvétel indítása") if live else t("\u2193  Letöltés"))

    def _place_hdr(self):
        """A HDR négyzet a felbontás mellett áll, ha belefér, különben alatta külön sorban."""
        check, line = self.hdr_check, self.hdr_row_parent
        if not getattr(self, "_hdr_show", False):
            check.pack_forget()
            self.hdr_line.pack_forget()
            return
        need = line.winfo_children()[0].winfo_reqwidth() + check.winfo_reqwidth() + 50
        inline = line.winfo_width() >= need or line.winfo_width() <= 1
        target = line if inline else self.hdr_line
        if check.winfo_manager() == "pack" and check.pack_info().get("in") == target:
            return
        check.pack_forget()
        if inline:
            self.hdr_line.pack_forget()
            check.pack(in_=line, side="right", padx=(0, 14))
        else:
            self.hdr_line.pack(fill="x", padx=14, pady=(0, 10))
            check.pack(in_=self.hdr_line, side="right")
            check.lift()

    def _on_resolution_change(self):
        self._update_audio_ui()
        self._refresh_details()

    RES_SEG_MAX = 6  # ennyi felbontás fér el a kapszulán, a többi a "Más" menübe kerül

    def _set_res_values(self, values, state="readonly"):
        """A felbontások listája: a lenyíló (adat) és a kapszula (felület) együtt frissül."""
        self.res_box.configure(state=state, values=values)
        self._build_res_seg(list(values) if state != "disabled" else [])

    def _build_res_seg(self, values):
        if self.res_seg is not None:
            self.res_seg.destroy()
            self.res_seg = None
        if not values:
            if not self.res_hint.winfo_ismapped():
                self.res_hint.pack(fill="x")
            return
        self.res_hint.pack_forget()
        audio = [v for v in values if v == AUDIO_LABEL]
        video = [v for v in values if v != AUDIO_LABEL]
        shown, more = video[:self.RES_SEG_MAX], video[self.RES_SEG_MAX:]
        opts = [(v, v.replace(AUDIO_LABEL, t("Csak hang"))) for v in shown]
        self._res_more = more
        if more:
            opts.append(("__more", t("Más \u25be")))
        opts += [(v, t("Csak hang")) for v in audio]
        self.res_seg = SegmentedControl(self.res_seg_line, opts, self.resolution.get(),
                                        self._on_res_seg, width=360, height=32)
        self.res_seg.pack(fill="x")
        self._res_seg_select()

    def _on_res_seg(self, value):
        if value == "__more":
            menu = tk.Menu(self.root, tearoff=0)
            for v in self._res_more:
                menu.add_command(label=v, command=lambda v=v: self._pick_res(v))
            try:
                menu.tk_popup(self.res_seg.winfo_rootx() + self.res_seg.winfo_width() - 120,
                              self.res_seg.winfo_rooty() + self.res_seg.winfo_height())
            finally:
                menu.grab_release()
            self._res_seg_select()  # ha nem választott, maradjon a korábbi
            return
        self._pick_res(value)

    def _pick_res(self, value):
        self.resolution.set(value)
        self._on_resolution_change()

    def _res_seg_select(self):
        """A kapszula a mostani felbontást mutatja (a "Más" elemen a kiválasztott értékkel)."""
        seg = getattr(self, "res_seg", None)
        if seg is None:
            return
        cur = self.resolution.get()
        if cur in getattr(self, "_res_more", []):
            seg.set_label("__more", f"{cur} \u25be")
            seg.set_value("__more")
        else:
            if getattr(self, "_res_more", []):
                seg.set_label("__more", t("Más \u25be"))
            seg.set_value(cur)

    def _on_hdr_change(self):
        self._refresh_details()

    def _details_rows(self):
        info = self.info_data or {}
        uploader = info.get("uploader") or info.get("channel") or t("ismeretlen")
        if self._is_live():
            rows = [(t("Feltöltő"), uploader), (t("Típus"), t("Élő adás, most is megy"))]
            started = info.get("release_timestamp") or info.get("timestamp")
            if started:
                try:
                    when = datetime.fromtimestamp(int(started))
                    day = t("ma") if when.date() == datetime.now().date() \
                        else when.strftime(DATE_FORMATS.get(LANG, "%Y.%m.%d %H:%M")[:8])
                    rows.append((t("Elindult"), f"{day} {when.strftime('%H:%M')}"))
                except (ValueError, OSError, OverflowError):
                    pass
            rows.append((t("Méret"), t("a felvétel hosszától függ")))
            return rows
        rows = [(t("Feltöltő"), uploader),
                (t("Hossz"), format_duration(info.get("duration")))]
        start, end, _ = self._clip_range()
        part = None
        if start is not None and info.get("duration"):
            part = (end - start) / float(info["duration"])
            rows.append((t("Kijelölt rész"), t('{x}-tól {x2}-ig').format(x=format_duration(start) if start else '0:00', x2=format_duration(end))))
        if self._is_audio():
            size = estimate_audio_size(info, self._selected_kbps())
            if size and part is not None:
                size *= part
            rows.append((t("Becsült méret"), format_size(size, False) if size else t("ismeretlen")))
            return rows
        est = None
        if self._selected_height():
            hdr = self._hdr_wanted()
            est = estimate_size(info, self._selected_height(), hdr)
            if est is None and hdr:
                est = estimate_size(info, self._selected_height())
        if est:
            size, exact = est
            if part is not None:
                size, exact = size * part, False
            rows.append((t("Méret") if exact else t("Becsült méret"), format_size(size, exact)))
        else:
            rows.append((t("Becsült méret"), t("ismeretlen")))
        return rows

    def _ready_basename(self):
        name = build_basename(self.info_data, self._selected_height(), self._hdr_wanted())
        start, end, _ = self._clip_range()
        return name + clip_suffix(start, end) if start is not None else name

    def _set_ready_status(self):
        ext = ".mp3" if self._is_audio() else (".mkv" if self._hdr_wanted() else ".mp4")
        name = self._ready_basename() + ext
        # a régi, egy szövegben levő változat is megmarad (más részek és tesztek olvassák)
        self.status.set(t('Mentés ezen a néven: {name}\nVálassz felbontást, majd nyomd meg a Letöltés gombot.').format(name=name))
        box = getattr(self, "ready_box", None)
        if box is not None:
            self.ready_name.configure(text=name)
            self.ready_hint.configure(
                text=t("Válassz felbontást, majd nyomd meg a Felvétel indítása gombot.")
                if self._is_live() else t("Válassz felbontást, majd nyomd meg a Letöltés gombot."))
            self.status_label_main.grid_remove()
            box.grid()

    def _refresh_details(self):
        if self.info_data:
            self.preview.set_details(self._details_rows())
            if not self.busy and self._phase is None and self.preview.winfo_manager():
                self._set_ready_status()

    def _paste_url(self, _event=None):
        """Beillesztés: ha több link van a vágólapon (soronként egy), mind a mezőbe kerül,
        szóközzel elválasztva. Egy soros mezőbe az újsor amúgy sem férne bele."""
        widget = self._url_box.widget
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            return "break"
        links = extract_links(text)
        if len(links) >= 2:
            self.url.set(" ".join(links))
            widget.icursor("end")
            return "break"
        text = " ".join(text.split())
        try:
            widget.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        widget.insert("insert", text)
        return "break"

    def _downloaded_before(self, url):
        """A korábbi letöltés (előzmény) ehhez a linkhez. Zárolt vagy kikapcsolt előzménynél nincs."""
        if self.hist_locked or history_cap(self.history_limit) == 0:
            return None
        return find_downloaded(self.history, url, self._missing)

    def _ask_again(self, entry):
        when = format_history_date(entry.get("date"))
        return show_confirm(self.root, t("Ezt már letöltötted"),
                            t('Ezt a linket már letöltötted ({when}):\n\n{x}\n\nLetöltöd még egyszer?').format(when=when, x=entry['name']), yes_text=t("Letöltöm újra"), no_text=t("Mégsem"))

    def _fetch_multi(self, links):
        """Több beillesztett link: a lejátszási lista ablakában kiválasztható, majd mind a sorba kerül."""
        folder = self.folder.get().strip()
        if not os.path.isdir(folder):
            show_dialog(self.root, "warning", t("A kiválasztott mappa nem létezik."))
            return
        dups = [l for l in links if self._downloaded_before(l)]
        if dups:
            again = show_confirm(
                self.root, t("Ezeket már letöltötted"),
                t('{n_dups} linket korábban már letöltöttél (a {n_links} közül).\n\nLetöltöd ezeket is újra?').format(n_dups=len(dups), n_links=len(links)), yes_text=t("Igen, újra is"), no_text=t("Kihagyom őket"))
            if not again:
                links = [l for l in links if l not in dups]
        if not links:
            self.set_status(t("Minden link már le volt töltve."))
            return
        entries = [{"url": l, "title": l, "uploader": "", "duration": None} for l in links]
        self.set_status(t('{n_entries} link beillesztve.').format(n_entries=len(entries)))
        res_values = ["1080p", "720p", "480p", "360p", AUDIO_LABEL]
        default = self.resolution.get() if self.resolution.get() in res_values else "1080p"
        result = ask_playlist(self.root, t("Beillesztett linkek"), entries, False, res_values,
                              default)
        if result:
            self._queue_playlist(*result)
        else:
            self.set_status(t("A linkek letöltését elvetted."))

    def fetch_info(self):
        url = self.url.get().strip()
        if not url:
            show_dialog(self.root, "warning", t("Előbb másold be a videó linkjét."))
            return
        links = extract_links(url)
        if len(links) >= 2:
            self._fetch_multi(links)
            return
        dup = self._downloaded_before(url)
        if dup and not self._ask_again(dup):
            return
        self.set_busy(True)
        self._set_res_values([], state="disabled")
        self.resolution.set("")
        self.hdr.set(False)
        self.info_data = None
        self._setup_extras()
        self._update_audio_ui()
        self.preview.grid_remove()
        self.info_url = None

        self._fetch_id += 1
        self._fetch_cancel = threading.Event()
        self._phase = "fetch"
        self.cancel_btn.set_state("normal")
        self.cancel_btn.grid()
        self._start_fetch_ui(self._fetch_id)
        threading.Thread(target=self._fetch,
                         args=(self._fetch_id, url, self._extra_opts(), self._fetch_cancel),
                         daemon=True).start()
        self._arm_stall_timer(self._fetch_id, FETCH_STALL_SECONDS)

    def _fetch(self, fid, url, extra_opts, cancel):
        try:
            opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
                    "extract_flat": "in_playlist", "playlistend": PLAYLIST_MAX,
                    "logger": FetchLogger(
                        cancel, lambda m: self._post(self._fetch_message, fid, m))}
            opts.update(extra_opts)
            with yt_dlp.YoutubeDL(opts) as ydl:
                first_error = None
                try:
                    info = ydl.extract_info(url, download=False)
                except Exception as e:
                    if cancel.is_set():
                        return
                    info, first_error = None, e
                if info is not None and (info.get("_type") == "playlist" or (
                        info.get("entries") is not None and not info.get("formats"))):
                    entries = collect_playlist_entries(info)
                    if not entries:  # csatorna főoldal: a Videók fület nézzük meg
                        tab = find_videos_tab(info)
                        if tab:
                            info = ydl.extract_info(tab, download=False)
                            entries = collect_playlist_entries(info)
                    self._post(self._fetch_playlist_done, fid, info, entries)
                    return
                if info is None or not video_heights(info)[0]:
                    # a yt-dlp nem talált rendes videót: megnézzük az oldal kódját
                    self._post(self._fetch_progress, fid, 93, t("Videó keresése az oldalon"))
                    better = self._sniff_best(ydl, url, opts, info, cancel)
                    if better is not None:
                        info = better
                    elif info is None:
                        raise first_error
                self._post(self._fetch_progress, fid, 92, t("Bélyegkép letöltése"))
                thumb = None
                thumb_url = info.get("thumbnail")
                if thumb_url and HAS_PIL:
                    try:
                        thumb = ydl.urlopen(thumb_url).read()
                    except Exception:
                        thumb = None
            self._post(self._fetch_done, fid, url, info, thumb)
        except Exception as e:
            if cancel.is_set():
                return
            self.root.after(0, self._fetch_error, fid, str(e))

    def _sniff_best(self, ydl, page_url, base_opts, orig_info, cancel):
        """Ha a yt-dlp nem ismeri az oldalt, megkeressük benne a valódi videólinket.
        A legjobb (legmagasabb felbontású, leghosszabb) találatot adja, vagy None-t."""
        def fetch(u, referer):
            headers = {"Referer": referer} if referer else {}
            try:
                resp = ydl.urlopen(yt_dlp.networking.Request(u, headers=headers))
            except Exception:
                resp = ydl.urlopen(u)
            return resp.read(3_000_000).decode("utf-8", "replace")

        candidates = sniff_media_urls(fetch, page_url)[:5]
        if not candidates:
            return None
        opts = {k: v for k, v in base_opts.items() if k not in ("extract_flat", "playlistend")}
        opts["http_headers"] = {**(base_opts.get("http_headers") or {}), "Referer": page_url}

        def score(i):
            heights, has_video = video_heights(i)
            return (heights[0] if heights else 0, 1 if has_video else 0, i.get("duration") or 0)

        best, best_score = None, score(orig_info) if orig_info else (-1, -1, -1)
        with yt_dlp.YoutubeDL(opts) as sub:
            for cand in candidates:
                if cancel.is_set():
                    return None
                try:
                    cinfo = sub.extract_info(cand, download=False)
                except Exception:
                    continue
                if cinfo.get("_type") == "playlist" or not video_heights(cinfo)[1]:
                    continue
                sc = score(cinfo)
                if sc > best_score:
                    best, best_score = (cand, cinfo), sc
        if best is None:
            return None
        cand, cinfo = best
        for key in ("title", "uploader", "upload_date", "thumbnail", "duration"):
            if orig_info and orig_info.get(key) and (key != "duration" or not cinfo.get(key)):
                cinfo[key] = orig_info[key]
        if not cinfo.get("title") or str(cinfo["title"]).lower().endswith((".m3u8", ".mp4")):
            cinfo["title"] = page_title_from_url(page_url)
        cinfo["_phdl_media_url"] = cand
        return cinfo

    # ---------- az adatlekérés haladásjelzője ----------
    def _start_fetch_ui(self, fid):
        self._fetch_pct = 2.0
        self._fetch_stage = t("Indul")
        self._fetch_t0 = time.time()
        self.fetch_bar.set(self._fetch_pct)
        self.fetch_bar.grid()
        self._show_fetch_status()
        self.root.after(500, self._fetch_tick, fid)

    def _stop_fetch_ui(self):
        try:
            self.fetch_bar.grid_remove()
        except (tk.TclError, AttributeError):
            pass

    def _show_fetch_status(self):
        secs = int(time.time() - self._fetch_t0)
        self.set_status(t('Videó adatainak lekérése: {x}%  ({fetch_stage}, {secs} mp)').format(x=int(self._fetch_pct), fetch_stage=self._fetch_stage, secs=secs))

    def _fetch_message(self, fid, msg):
        if fid != self._fetch_id or self._phase != "fetch":
            return
        pct, stage = advance_fetch_pct(self._fetch_pct, msg)
        self._fetch_progress(fid, pct, stage)

    def _fetch_progress(self, fid, pct, stage=None):
        if fid != self._fetch_id or self._phase != "fetch":
            return
        self._fetch_pct = max(self._fetch_pct, pct)
        if stage:
            self._fetch_stage = stage
        self.fetch_bar.set(self._fetch_pct)
        self._show_fetch_status()

    def _fetch_tick(self, fid):
        """Lassan akkor is mozdul a sáv, ha az oldal nem szól semmit, így látszik, hogy él."""
        if fid != self._fetch_id or self._phase != "fetch":
            return
        if self._fetch_pct < FETCH_CAP:
            self._fetch_pct += (FETCH_CAP - self._fetch_pct) * 0.02
        self.fetch_bar.set(self._fetch_pct)
        self._show_fetch_status()
        self.root.after(500, self._fetch_tick, fid)

    def _fetch_done(self, fid, url, info, thumb_bytes):
        if fid != self._fetch_id:  # közben megszakítottuk, az eredményt eldobjuk
            return
        heights, has_video = video_heights(info)
        if not heights and not has_video and not (info.get("formats") or []):
            self._fetch_error(fid, t("Nem találtam elérhető felbontást ehhez a linkhez."))
            return
        self._phase = None
        self._cancel_stall_timer()
        self.cancel_btn.grid_remove()
        self.info_data = info
        self.info_url = url
        self.hdr.set(False)
        self._setup_extras()

        # a videós felbontások után a "Csak audio" lehetőség jön
        values = [f"{h}p" for h in heights]
        if not heights and has_video:  # a videó megvan, csak a felbontását nem ismerjük
            values.append(BEST_LABEL)
        values.append(AUDIO_LABEL)
        self._set_res_values(values)
        self.resolution.set(values[0])
        self._update_audio_ui()

        self._thumb_bytes = thumb_bytes
        pil = self._thumb_image(thumb_bytes)
        self._photo = ImageTk.PhotoImage(pil) if pil is not None else None
        self.preview.show(info.get("title") or t("Névtelen videó"),
                          self._details_rows(), self._photo, pil=pil, animate=True)
        self.preview.grid()
        self.set_busy(False)
        self._set_ready_status()

    def _fetch_playlist_done(self, fid, info, entries):
        """Lejátszási lista vagy csatorna: kiválasztó ablak, majd sorba állítás."""
        if fid != self._fetch_id:
            return
        self._phase = None
        self._cancel_stall_timer()
        self.cancel_btn.grid_remove()
        self.set_busy(False)
        if not entries:
            self.set_status(t("Nem találtam letölthető videót ezen a linken."))
            show_dialog(self.root, "warning", t("Nem találtam letölthető videót ezen a linken."))
            return
        folder = self.folder.get().strip()
        if not os.path.isdir(folder):
            show_dialog(self.root, "warning", t("A kiválasztott mappa nem létezik."))
            return
        self.set_status(t('Lejátszási lista: {n_entries} videó.').format(n_entries=len(entries)))
        res_values = ["1080p", "720p", "480p", "360p", AUDIO_LABEL]
        default = self.resolution.get() if self.resolution.get() in res_values else "1080p"
        result = ask_playlist(self.root, info.get("title") or t("Lejátszási lista"), entries,
                              len(entries) >= PLAYLIST_MAX, res_values, default)
        if result:
            self._queue_playlist(*result)
        else:
            self.set_status(t("A lejátszási lista letöltését elvetted."))

    def _queue_playlist(self, entries, label):
        folder = self.folder.get().strip()
        audio = label == AUDIO_LABEL
        digits = label.replace("p", "")
        height = None if audio else (int(digits) if digits.isdigit() else 720)
        if audio and not shutil.which("ffmpeg"):
            show_dialog(self.root, "warning", t("Az mp3 készítéséhez ffmpeg kell, de nincs "
                        "telepítve.\n") + ffmpeg_hint())
            return
        kbps, extra = self._selected_kbps(), self._extra_opts()
        room = MAX_JOBS - sum(1 for j in self.jobs if j.unfinished)
        added = 0
        for e in entries:
            if added >= room:
                break
            if any(j.unfinished and j.url == e["url"] and j.folder == folder
                   and j.height == height and j.audio == audio for j in self.jobs):
                continue
            job = DownloadJob(e["url"], height, folder,
                              build_basename({"title": e["title"]}, height), audio, kbps,
                              e.get("uploader") or "", None, extra)
            job.title = e.get("title") or ""
            job.lazy = True
            job.embed_meta = self.embed_metadata
            self.jobs.append(job)
            self._build_job_row(job)
            added += 1
        if added < len(entries):
            show_dialog(self.root, "warning", t('{added} videót tettem a sorba, a többi már szerepelt a listában, vagy betelt a sor.').format(added=added))
        self._remember_folder(folder)
        self.url.set("")
        self._pump()
        self._refresh_queue_summary(announce=True)

    def _resolve_lazy(self, job):
        """Lejátszási listás videó: indításkor kérjük le a pontos címet, dátumot és bélyegképet."""
        job.text = t("Adatok lekérése...")
        self._post(self._update_job_ui, job)
        opts = {"quiet": True, "no_warnings": True, "noplaylist": True,
                "logger": FetchLogger(job.cancel_event)}
        opts.update(job.extra_opts)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(job.url, download=False)
            thumb = None
            if info.get("thumbnail") and HAS_PIL:
                try:
                    thumb = ydl.urlopen(info["thumbnail"]).read()
                except Exception:
                    thumb = None
        job.basename = build_basename(info, job.height)
        job.uploader = info.get("uploader") or info.get("channel") or job.uploader
        job.title = info.get("title") or job.title
        job.upload_date = str(info.get("upload_date") or "")
        job.duration = info.get("duration") if not job.clip else job.clip[1] - job.clip[0]
        job.thumb = thumb
        job.lazy = False
        self._post(self._refresh_job_head, job)

    def _refresh_job_head(self, job):
        ui = job.ui
        if not ui:
            return
        try:
            name = job.name if len(job.name) <= 44 else job.name[:43] + "…"
            ui["name"].configure(text=name)
        except (tk.TclError, KeyError):
            pass
        self._render_job_thumb(job)

    def _fetch_error(self, fid, msg):
        if fid != self._fetch_id:
            return
        self._phase = None
        self._cancel_stall_timer()
        self.cancel_btn.grid_remove()
        self.set_busy(False)
        self.set_status(t("Nem sikerült lekérni a videó adatait."))
        text, retry = explain_error(msg, self.browser.get())
        self._offer_retry(t("A videó adatainak lekérése nem sikerült."), text, retry,
                          self.fetch_info)

    def _offer_retry(self, headline, text, retry_ok, action):
        """Hiba után megkérdezi, hogy újrapróbálja-e. Magától sosem próbálkozik újra."""
        if retry_ok:
            if show_confirm(self.root, t("Újrapróbálkozás"),
                            t('{headline}\n\n{text}\n\nÚjrapróbáljam?').format(headline=headline, text=text)):
                action()
        else:
            show_dialog(self.root, "error", f"{headline}\n\n{text}")

    # ---------- elakadt lekérés figyelése ----------
    def _arm_stall_timer(self, fid, seconds):
        self._cancel_stall_timer()
        self._stall_job = self.root.after(int(seconds * 1000), self._on_fetch_stall, fid)

    def _cancel_stall_timer(self):
        if self._stall_job is not None:
            try:
                self.root.after_cancel(self._stall_job)
            except Exception:
                pass
            self._stall_job = None

    def _on_fetch_stall(self, fid):
        self._stall_job = None
        if fid != self._fetch_id or self._phase != "fetch":
            return
        causes = [t("lassú vagy megszakadt az internet"),
                  t("az oldal nem válaszol"),
                  t("elavult az yt-dlp (a Beállítások fülön van frissítés keresés)")]
        if self.browser.get() != "Nincs":
            causes.append(t('a(z) {x} sütijeinek beolvasása várhat egy rendszerablakra (például jelszókérésre)').format(x=browser_label(self.browser.get())))
        message = (t('Az adatlekérés már több mint {fetch_stall_seconds:g} másodperce tart, valami akadozik.\n\nLehetséges okok:\n').format(fetch_stall_seconds=FETCH_STALL_SECONDS)
                   + "\n".join("• " + c for c in causes)
                   + t("\n\nMegszakítsam, és újrapróbáljam?"))
        retry = show_confirm(self.root, t("A lekérés elakadt"), message)
        if fid != self._fetch_id or self._phase != "fetch":
            return  # közben befejeződött
        if retry:
            self._cancel_fetch()
            self.fetch_info()
        else:
            self._arm_stall_timer(fid, FETCH_STALL_SECONDS)

    def _cancel_fetch(self):
        """A lekérést nem lehet erőszakkal leállítani, ezért a felület azonnal
        felszabadul, a háttérben futó lekérés eredményét pedig eldobjuk."""
        self._fetch_id += 1
        self._fetch_cancel.set()
        self._phase = None
        self._cancel_stall_timer()
        self.cancel_btn.grid_remove()
        self.set_busy(False)
        self.set_status(t("Az adatok lekérését megszakítottam."))

    def _reset_form(self):
        """Letöltés indítása után a felület készen áll a következő linkre."""
        self.url.set("")
        self._set_res_values([], state="disabled")
        self.resolution.set("")
        self.hdr.set(False)
        self.info_data = None
        self._setup_extras()
        self._update_audio_ui()
        self.preview.grid_remove()
        self.info_url = None
        self._thumb_bytes = None
        self.dl_btn.set_state("disabled")


class ExtrasMixin:
    """A letöltés kiegészítői: kijelölt rész, feliratok, élő adás felvétele, SponsorBlock és
    az adatok beégetése a fájlba (a letöltő oldal sorai és a hozzájuk tartozó letöltési rész)."""

    # ---------- közös ----------
    def _setup_extras(self):
        """Új videó adatainál: teljes videó, a feliratlista a videó feliratai alapján."""
        info = self.info_data or {}
        dur = info.get("duration")
        self.clip_ctl.set_value("full")
        self.clip_line.pack_forget()
        self._clip_mode = "full"
        self.clip_start.set("0:00")
        self.clip_end.set(format_duration(dur) if dur else "")
        choices = subtitle_choices(info) if info else []
        self._sub_keys = {label: key for key, label in choices}
        self.sub_combo.configure(values=[NO_SUB_LABEL] + [l for _, l in choices])
        self.sub_var.set(NO_SUB_LABEL)
        self.live_from_start.set(False)
        self.sb_var.set(False)
        self._sb_segments = []
        self._sb_video = None
        if is_youtube(info) and live_state(info) is None:
            vid = info["id"]
            self._sb_video = vid
            threading.Thread(target=lambda: self._post(
                self._sb_loaded, vid, fetch_sponsor_segments(vid)), daemon=True).start()
        if live_state(info) == "live" and can_record_from_start(info):
            self.live_check.pack(side="right")
        else:
            self.live_check.pack_forget()
        self._update_live_note()

    def _is_live(self):
        return live_state(self.info_data) == "live"

    def _selected_sub(self):
        if self._is_audio():
            return None
        return self._sub_keys.get(self.sub_var.get())

    # ---------- kijelölt rész ----------
    def _build_clip_row(self):
        # kijelölt rész: alapból a teljes videó, átkapcsolva kezdő és záró időpont
        self.clip_row, line = self._option_row(2, t("Letöltendő rész"))
        self.clip_ctl = SegmentedControl(line, [("full", t("Teljes videó")),
                                                ("part", t("Kijelölt rész"))],
                                         "full", self._on_clip_mode, width=230, height=28)
        self.clip_ctl.pack(side="right")
        self.clip_line = tk.Frame(self.clip_row, bg=PANEL)
        self.clip_start = tk.StringVar()
        self.clip_end = tk.StringVar()

        def time_field(text, var):
            tk.Label(self.clip_line, text=text, bg=PANEL, fg=GREY,
                     font=(FONT_FAMILY, 12)).pack(side="left", padx=(0, 6))
            box = RoundBox(self.clip_line, lambda p: tk.Entry(
                p, textvariable=var, justify="center", **entry_kw()), height=32, pad=10)
            box.configure(width=96)
            box.pack(side="left", padx=(0, 16))
            e = box.widget
            add_context_menu(e)
            var.trace_add("write", lambda *a: self._on_clip_edit())
            return e

        self.clip_start_entry = time_field(t("Kezdete"), self.clip_start)
        self.clip_end_entry = time_field(t("Vége"), self.clip_end)
        self.clip_info = tk.Label(self.clip_line, text="", bg=PANEL, fg=GREY,
                                  font=(FONT_FAMILY, 12), anchor="w")
        self.clip_info.pack(side="left", fill="x", expand=True)

    def _on_clip_mode(self, value):
        self._clip_mode = value
        self.clip_ctl.set_value(value)
        if value == "part":
            self.clip_line.pack(fill="x", padx=14, pady=(0, 12))
            self.clip_start_entry.focus_set()
            self.clip_start_entry.select_range(0, "end")
        else:
            self.clip_line.pack_forget()
        self._on_clip_edit()
        self._update_sb_row()

    def _clip_range(self):
        """(kezdet, vége, hibaüzenet). Teljes videónál (None, None, None)."""
        if getattr(self, "_clip_mode", "full") != "part":
            return None, None, None
        dur = int((self.info_data or {}).get("duration") or 0)
        start, end = parse_timecode(self.clip_start.get()), parse_timecode(self.clip_end.get())
        if start is None or end is None:
            return None, None, t("Az időpontot így add meg: 1:30 vagy 1:02:30.")
        if dur:
            end = min(end, dur)
        if end <= start:
            return None, None, t("A vége legyen később, mint a kezdete.")
        if dur and start >= dur:
            return None, None, t('A videó csak {x} hosszú.').format(x=format_duration(dur))
        return start, end, None

    def _on_clip_edit(self):
        if getattr(self, "_clip_mode", "full") == "part":
            start, end, err = self._clip_range()
            if err:
                self.clip_info.configure(text=err, fg=DANGER)
            else:
                self.clip_info.configure(text=t('{x} hosszú rész').format(x=format_duration(end - start)),
                                         fg=GREY)
        self._refresh_details()

    # ---------- feliratok ----------
    def _build_subtitle_row(self):
        # feliratok: csak akkor látszik, ha a videónak van felirata
        self.sub_row, line = self._option_row(3, t("Feliratok letöltése"))
        self.sub_var = tk.StringVar(value=NO_SUB_LABEL)
        self.sub_combo = ttk.Combobox(line, textvariable=self.sub_var, state="readonly",
                                      style="Chip.TCombobox", values=[NO_SUB_LABEL],
                                      width=24, font=(FONT_FAMILY, 13))
        self.sub_combo.pack(side="right")
        self._sub_keys = {}

    # ---------- élő adás felvétele ----------
    def _build_live_row(self):
        # élő adás: a "Letöltendő rész" helyén (élő adásnak nincs ismert hossza)
        self.live_row, line = self._option_row(2, t("Élő adás"))
        self.live_badge = tk.Label(line, text=" ● " + t("ÉLŐ") + " ", bg=DANGER, fg="#ffffff",
                                   font=(FONT_FAMILY, 11, "bold"))
        self.live_badge.pack(side="left", padx=(10, 0))
        # a fehér betű nem szerepszín: témaváltás után is fehér maradjon
        self.live_badge._retheme = lambda b=self.live_badge: b.configure(bg=DANGER, fg="#ffffff")
        self.live_from_start = tk.BooleanVar(value=False)
        self.live_check = make_check(line, t("Felvétel az adás elejétől"), self.live_from_start,
                                     self._update_live_note)
        self.live_note = tk.Label(self.live_row, text="", bg=PANEL, fg=GREY, anchor="w",
                                  justify="left", font=(FONT_FAMILY, 12))
        self.live_note.pack(fill="x", padx=14, pady=(0, 12))
        self.live_row.bind("<Configure>", lambda e: self.live_note.configure(
            wraplength=max(200, e.width - 30)), add="+")

    def _update_live_note(self):
        if self.live_from_start.get():
            text = t("A felvétel az adás elejétől indul, a már lement részt is letölti "
                     "(a YouTube az adás első néhány óráját őrzi meg). Ez lassabb, mint az "
                     "indítástól induló felvétel.")
        else:
            text = t("A felvétel az indítástól tart, amíg az adás véget nem ér, vagy amíg "
                     "le nem állítod.")
        self.live_note.configure(text=text)

    def _stop_live(self, job):
        """Leállítás és mentés: a felvett rész megmarad, utána a szokásos feldolgozás jön."""
        if not job.live or job.state != "active" or job.stop_event.is_set() \
                or job.cancel_event.is_set() or not job.can_cancel:
            return
        procs = live_procs(job.thread_id) if job.thread_id else []
        if not procs and not job.live_from_start:
            # a felvétel még el sem indult (az adatok lekérése tart): nincs mit menteni
            self._cancel_job(job)
            return
        job.stop_event.set()
        job.text = t("A felvétel mentése...")
        for proc in procs:
            # az ffmpeg a "q" betűre rendesen lezárja a fájlt
            try:
                proc.stdin.write(b"q")
                proc.stdin.flush()
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass
        self._update_job_ui(job)

    def _live_tick(self, job, tick_id=None):
        """Felvétel közben másodpercenként: eltelt idő és a fájlok mérete."""
        if not job.live or job.state != "active" or job.cancel_event.is_set() \
                or tick_id != getattr(job, "tick_id", None):
            return
        if job.can_cancel and not job.stop_event.is_set():
            size = 0
            folder = job.work_dir or job.folder
            try:
                for name in os.listdir(folder):
                    if name.startswith(job.basename):
                        size += os.path.getsize(os.path.join(folder, name))
            except OSError:
                pass
            parts = [t("● Felvétel: {elapsed}").format(elapsed=live_elapsed(job))]
            if size:
                parts.append(format_size(size, True))
            if job.live_from_start:
                parts.append(t("az adás elejétől"))
            job.text = "  ·  ".join(parts)
            self._update_job_ui(job)
        try:
            self.root.after(1000, self._live_tick, job, tick_id)
        except Exception:
            pass

    # ---------- SponsorBlock és adatok a fájlba ----------
    def _build_sponsorblock_row(self):
        # SponsorBlock: csak YouTube videónál, ha a videóban vannak jelölt részek
        self.sb_row, line = self._option_row(4, t("SponsorBlock"))
        self.sb_var = tk.BooleanVar(value=False)
        self.sb_check = make_check(line, "", self.sb_var, self._refresh_details)
        self.sb_check.pack(side="right")
        self.sb_info = tk.Label(self.sb_row, text="", bg=PANEL, fg=GREY, anchor="w",
                                justify="left", font=(FONT_FAMILY, 12))
        self.sb_info.pack(fill="x", padx=14, pady=(0, 12))
        self._sb_segments = []
        self._sb_video = None
        self.sb_row.grid_remove()

    def _sb_loaded(self, video_id, segments):
        if video_id != self._sb_video:
            return  # közben másik videót kértél le
        self._sb_segments = segments
        self._update_sb_row()

    def _sb_counts(self):
        return sponsor_summary(self._sb_segments, self.sb_categories)

    def _update_sb_row(self):
        """A SponsorBlock sor csak akkor látszik, ha a választott kategóriákban van jelölt
        rész, és nem kijelölt részt vagy élő adást töltesz."""
        if not hasattr(self, "sb_row"):
            return
        n, total = self._sb_counts()
        show = n > 0 and not self._is_live() and getattr(self, "_clip_mode", "full") == "full"
        if not show:
            self.sb_row.grid_remove()
            return
        self.sb_check.configure(text=t("Jelölt részek kivágása") if self.sb_mode != "mark"
                                else t("Jelölt részek fejezetként"))
        cats = sorted({c for c, _, _ in self._sb_segments if c in self.sb_categories},
                      key=list(SB_CATEGORIES).index)
        self.sb_info.configure(text=t("{n} rész, összesen {total}: {cats}").format(
            n=n, total=live_len(total), cats=", ".join(t(SB_CATEGORIES[c]).lower() for c in cats)))
        self.sb_row.grid()

    def _sb_wanted(self):
        if self.sb_var.get() and self.sb_row.winfo_manager():
            return (self.sb_mode, list(self.sb_categories))
        return None

    @staticmethod
    def _add_meta_opts(job, opts):
        """Adatok a fájlba és a SponsorBlock, a yt-dlp parancssorával azonos sorrendben:
        SponsorBlock lekérés, ..., ModifyChapters, FFmpegMetadata, EmbedThumbnail."""
        pps = opts.setdefault("postprocessors", [])
        sb = job.sponsorblock
        if sb:
            mode, cats = sb
            pps.insert(0, {"key": "SponsorBlock", "categories": set(cats),
                           "api": SPONSORBLOCK_API, "when": "after_filter"})
            if mode == "fade" and not job.hdr:
                pps.append({"key": "SponsorFade", "categories": set(cats),
                            "kbps": job.kbps if job.audio else None,
                            "progress": getattr(job, "fade_progress", None),
                            "should_stop": job.cancel_event.is_set,
                            "on_fallback": lambda why: setattr(job, "fade_failed", why)})
            else:
                # HDR videónál az áttűnés helyett is sima vágás (lásd sponsor_fade_cut)
                mode = "remove" if mode == "fade" else mode
                pps.append({"key": "ModifyChapters", "remove_chapters_patterns": [],
                            "remove_sponsor_segments": set(cats) if mode == "remove" else set(),
                            "remove_ranges": [],
                            "sponsorblock_chapter_title": "[SponsorBlock]: %(category_names)l",
                            "force_keyframes": False})
        if job.embed_meta or sb:
            pps.append({"key": "FFmpegMetadata", "add_chapters": True,
                        "add_metadata": bool(job.embed_meta), "add_infojson": False})
        if job.embed_meta and not job.live:
            pps.append({"key": "SafeEmbedThumbnail", "already_have_thumbnail": False,
                        "on_fail": lambda why: setattr(job, "thumb_failed", why)})
            opts["writethumbnail"] = True
            tmpl = opts.get("outtmpl")
            if isinstance(tmpl, str):
                opts["outtmpl"] = {"default": tmpl, "pl_thumbnail": ""}


class QueueMixin:
    """A letöltési sor és a futó letöltések kártyái (az Előzmények oldal tetején)."""

    # ---------- letöltések: sor, párhuzamos futás ----------
    def start_download(self):
        """A kiválasztott videót a letöltések sorába teszi. Egyszerre MAX_PARALLEL fut."""
        url = self.url.get().strip()
        folder = self.folder.get().strip()
        audio = self._is_audio()
        height = self._selected_height()
        best = self.resolution.get() == BEST_LABEL
        if not url or not (audio or height or best):
            return
        if not self.info_data or url != self.info_url:
            show_dialog(self.root, "warning",
                        t("A link megváltozott, kérd le újra a videó adatait."))
            return
        if not os.path.isdir(folder):
            show_dialog(self.root, "warning", t("A kiválasztott mappa nem létezik."))
            return
        if sum(1 for j in self.jobs if j.unfinished) >= MAX_JOBS:
            show_dialog(self.root, "warning",
                        t('Legfeljebb {max_jobs} letöltés lehet a listában. Várd meg, amíg néhány elkészül.').format(max_jobs=MAX_JOBS))
            return
        hdr = self._hdr_wanted()
        start, end, clip_err = self._clip_range()
        if clip_err:
            show_dialog(self.root, "warning", clip_err)
            return
        basename = self._ready_basename()
        if any(j.unfinished and j.folder == folder and j.basename == basename
               for j in self.jobs):
            show_dialog(self.root, "warning",
                        t("Ez a videó ebben a minőségben már szerepel a letöltések között."))
            return
        if not shutil.which("ffmpeg"):
            if audio:
                show_dialog(self.root, "warning",
                            t("Az mp3 készítéséhez ffmpeg kell, de nincs telepítve.\n")
                            + ffmpeg_hint())
                return
            show_dialog(
                self.root, "warning",
                t("Az ffmpeg nincs telepítve, ezért nem biztos, hogy mp4 lesz belőle.\n")
                + ffmpeg_hint())

        uploader = (self.info_data.get("uploader") or self.info_data.get("channel") or "")
        media = self.info_data.get("_phdl_media_url")
        extra = self._extra_opts()
        if media:  # az oldalból kikeresett videólink: az oldal a Referer
            extra = dict(extra)
            extra["http_headers"] = {**(extra.get("http_headers") or {}), "Referer": url}
        job = DownloadJob(media or url, height, folder, basename, audio, self._selected_kbps(),
                          uploader, self._thumb_bytes, extra, hdr)
        job.source_url = url
        job.title = self.info_data.get("title") or ""
        job.upload_date = str(self.info_data.get("upload_date") or "")
        job.duration = self.info_data.get("duration")
        if start is not None:
            job.clip = (start, end)
            job.duration = end - start
        job.sub = self._selected_sub()
        job.sponsorblock = self._sb_wanted()
        job.embed_meta = self.embed_metadata
        if self._is_live():
            job.live = True
            job.sub = None
            job.live_from_start = bool(self.live_from_start.get()) and \
                can_record_from_start(self.info_data)
        fly_data, fly_src = self._thumb_bytes, self.preview.thumb_geometry()
        self._remember_folder(folder)
        self._reset_form()
        self._add_job(job)
        self._fly_thumbnail(fly_data, fly_src)

    def _add_job(self, job):
        self.jobs.append(job)
        self._build_job_row(job)
        self._pump()
        self._refresh_queue_summary(announce=True)

    def _active_jobs(self):
        return [j for j in self.jobs if j.state == "active"]

    def _pump(self):
        """Elindítja a várakozó letöltéseket, amíg van szabad hely."""
        running = len(self._active_jobs())
        for job in self.jobs:
            if self.max_parallel and running >= self.max_parallel:
                break
            if job.state == "waiting":
                self._start_job(job)
                running += 1

    def _start_job(self, job):
        job.state = "active"
        job.text = t("Indul...")
        if job.live:
            job.live_started = time.monotonic()
            job.stop_event = threading.Event()
            job.tick_id = getattr(job, "tick_id", 0) + 1  # a régi számláló leáll
            self.root.after(1000, self._live_tick, job, job.tick_id)
        elif job.clip:
            job.tick_id = getattr(job, "tick_id", 0) + 1
            job.clip_started = time.monotonic()
            self.root.after(1000, self._clip_tick, job, job.tick_id)
        self._update_job_ui(job)
        threading.Thread(target=self._run_job, args=(job,), daemon=True).start()

    def _clip_tick(self, job, tick_id):
        """Kijelölt rész letöltésekor az ffmpeg nem küld haladást a yt-dlp-n át, ezért a
        -progress fájlból olvassuk ki másodpercenként."""
        if job.state != "active" or job.cancel_event.is_set() or not job.can_cancel \
                or tick_id != getattr(job, "tick_id", None):
            return
        done = read_ffmpeg_progress(getattr(job, "progress_file", "") or "")
        length = max(0.1, job.clip[1] - job.clip[0])
        if done is not None:
            pct = min(99.0, done / length * 100)
            self._job_progress(job, pct, t("Kijelölt rész: {pct}%  ({done} / {total})").format(
                pct=int(pct), done=live_len(done), total=live_len(length)))
        else:
            secs = int(time.monotonic() - job.clip_started)
            self._job_progress(job, None, t("Kijelölt rész előkészítése... {secs} mp").format(
                secs=secs))
        try:
            self.root.after(1000, self._clip_tick, job, tick_id)
        except Exception:
            pass

    def _post(self, func, *args):
        """Szálból biztonságosan szól a felületnek."""
        try:
            self.root.after(0, func, *args)
        except Exception:
            pass

    def _run_job(self, job):
        """A letöltés szála. Bármilyen váratlan hiba esetén is lezárja a letöltést (hiba vagy
        megszakítva), hogy ne maradjon örökre "Indul..." állapotban, foglalva a helyet."""
        try:
            self._run_job_inner(job)
        except Exception as e:
            log_exc("_run_job")
            if job.cancel_event.is_set():
                self._post(self._job_cancelled, job, 0)
            else:
                self._post(self._job_error, job, str(e))

    def _run_job_inner(self, job):
        if job.lazy:
            try:
                self._resolve_lazy(job)
            except Exception as e:
                if job.cancel_event.is_set():
                    self._post(self._job_cancelled, job, 0)
                else:
                    self._post(self._job_error, job, str(e))
                return
        # a % jelet duplázni kell, különben a yt-dlp sablonként értelmezné
        # Ideiglenes fájlok a gép helyi lemezén: a célmappába (pl. NAS) csak a kész videó
        # kerül át, így a hálózati tár naplóját nem töltik meg a köztes módosítások.
        tmp_dir = make_job_temp(self.temp_dir) if self.temp_local else None
        job.thread_id = threading.get_ident()
        job.work_dir = tmp_dir or job.folder
        install_live_tracking()  # a megszakítás és a kilépés leállíthatja az ffmpeg-et
        name_tmpl = job.basename.replace("%", "%%") + ".%(ext)s"
        outtmpl = name_tmpl if tmp_dir else os.path.join(job.folder, name_tmpl)
        opts = {
            "outtmpl": outtmpl,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "progress_hooks": [lambda d: self._job_hook(job, d)],
            "_vr_job": job,  # a sebességkorláthoz (install_speed_limit)
        }
        if job.audio:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                       "preferredcodec": "mp3",
                                       "preferredquality": str(job.kbps)}]
        else:
            h = job.height
            if job.hdr:
                # a HDR videó VP9.2/AV1, ez mp4-ben sok lejátszón nem megy: mkv a tároló
                opts["format"] = hdr_format_selector(h)
                opts["merge_output_format"] = "mkv"
            else:
                if h:
                    opts["format"] = (f"bv*[height<=?{h}][ext=mp4]+ba[ext=m4a]"
                                      f"/bv*[height<=?{h}]+ba/b[height<=?{h}]/b")
                else:  # ismeretlen felbontás: a legjobbat kérjük
                    opts["format"] = "bv*+ba/b"
                opts["merge_output_format"] = "mp4"
                opts["postprocessors"] = [{"key": "FFmpegVideoRemuxer",
                                           "preferedformat": "mp4"}]
        if job.clip:
            # csak a kijelölt rész: a vágásnál új kulcskép kerül a pontos időpontra
            opts["download_ranges"] = yt_dlp.utils.download_range_func(None, [job.clip])
            job.progress_file = os.path.join(tempfile.gettempdir(),
                                             f"vr-clip-{os.getpid()}-{job.id}.txt")
            enc = None if job.hdr else (
                ["-progress", job.progress_file] if job.audio
                else clip_encode_args(job.height, job.progress_file))
            if enc:
                opts["force_keyframes_at_cuts"] = True
                opts["external_downloader_args"] = {"ffmpeg_o": enc}
            else:
                # HDR vagy nincs gyors kódoló: újrakódolás nélkül, a legközelebbi kulcsképnél vág
                opts["external_downloader_args"] = {"ffmpeg_o": ["-progress", job.progress_file]}
        if job.sub:
            # a felirat külön .srt fájl a videó mellett, azonos névvel: a lejátszók
            # (az mpv is) maguktól betöltik
            auto = job.sub.startswith("auto:")
            opts["writesubtitles"] = not auto
            opts["writeautomaticsub"] = auto
            opts["subtitleslangs"] = [job.sub[5:] if auto else job.sub]
            opts["subtitlesformat"] = "srt/vtt/best"
            opts.setdefault("postprocessors", []).insert(
                0, {"key": "FFmpegSubtitlesConvertor", "format": "srt"})
        if job.live and job.live_from_start:
            opts["live_from_start"] = True
        job.fade_progress = lambda pct: self._post(
            self._job_processing, job, t("Áttűnések készítése: {pct}%").format(pct=int(pct)), pct)
        self._add_meta_opts(job, opts)
        if tmp_dir:
            opts["paths"] = {"home": job.folder, "temp": tmp_dir}
        opts.update(job.extra_opts)
        job.sub_failed = False
        job.fade_failed = None
        try:
            try:
                self._download_with_sub_retry(job, opts)
            except KeyboardInterrupt:
                # élő adás leállítása, ha a yt-dlp nem kezelte: ha a felvett rész megvan, kész
                path = find_output_file(job.folder, job.basename, job.ext)
                if job.cancel_event.is_set() or not job.stop_event.is_set() \
                        or not os.path.exists(path):
                    raise RuntimeError("Interrupted")
            self._post(self._job_done, job)
        except Exception as e:
            if job.cancel_event.is_set():
                removed = delete_partial_files(job.folder, job.basename)
                if job.sub:
                    removed += delete_subtitle_files(job.folder, job.basename)
                self._post(self._job_cancelled, job, removed)
            else:
                self._post(self._job_error, job, str(e))
        finally:
            if tmp_dir:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            if getattr(job, "progress_file", None):
                try:
                    os.remove(job.progress_file)
                except OSError:
                    pass

    def _download_with_sub_retry(self, job, opts):
        try:
            self._download_with_thumb_retry(job, opts)
        except Exception as e:
            # ha csak a felirat nem jött le, a videó attól még kell: újra, felirat nélkül
            if not job.sub or job.cancel_event.is_set() or "subtitle" not in str(e).lower():
                raise
            job.sub_failed = True
            for key in ("writesubtitles", "writeautomaticsub", "subtitleslangs"):
                opts.pop(key, None)
            opts["postprocessors"] = [pp for pp in opts.get("postprocessors", [])
                                      if pp.get("key") != "FFmpegSubtitlesConvertor"]
            self._download_with_thumb_retry(job, opts)

    @staticmethod
    def _download_with_thumb_retry(job, opts):
        """Ha a borítókép nem tölthető le (hibás vagy furcsa képlink), a yt-dlp az egész
        letöltést elbuktatja. Ilyenkor borító nélkül még egyszer."""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([job.url])
        except Exception as e:
            msg = str(e).lower()
            if not opts.get("writethumbnail") or job.cancel_event.is_set() or not any(
                    k in msg for k in ("thumbnail", "unable to handle request",
                                       "unsupported url scheme")):
                raise
            opts["writethumbnail"] = False
            opts["postprocessors"] = [pp for pp in opts.get("postprocessors", [])
                                      if pp.get("key") not in ("EmbedThumbnail", "SafeEmbedThumbnail")]
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([job.url])

    def _job_hook(self, job, d):
        if job.cancel_event.is_set():
            raise DownloadCancelled()
        if job.live:
            if d["status"] == "downloading":
                # az adás elejétől: a darabonként letöltő yt-dlp erre befejezi, és a felvett
                # részt összefűzi (élő adásnál ez a "leállítás és mentés")
                if job.stop_event.is_set():
                    raise KeyboardInterrupt
                return  # a felvett időt és méretet a _live_tick írja ki
            if d["status"] == "finished":
                self._post(self._job_processing, job, t("A felvétel mentése..."))
            return
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                pct = d.get("downloaded_bytes", 0) / total * 100
            elif d.get("fragment_count"):
                pct = d.get("fragment_index", 0) / d["fragment_count"] * 100
            else:
                pct = None
            now = time.monotonic()
            if now - getattr(job, "_last_post", 0.0) < 0.25 and (pct or 0) < 100:
                return  # legfeljebb ~4 frissítés másodpercenként
            job._last_post = now
            parts = []
            if pct is not None:
                parts.append(f"{pct:.0f}%")
            if d.get("speed"):
                parts.append(f"{d['speed'] / 1024 / 1024:.1f} MB/s")
            if d.get("eta") is not None:
                parts.append(t('még {x} mp').format(x=int(d['eta'])))
            self._post(self._job_progress, job, pct,
                       "  ".join(parts) if parts else t("Letöltés..."))
        elif d["status"] == "finished":
            # az összefűzést, átalakítást már nem lehet megszakítani
            what = t("mp3 átalakítás") if job.audio else t("mp4 összefűzés")
            self._post(self._job_processing, job, t('Feldolgozás ({what})...').format(what=what))

    def _job_progress(self, job, pct, text):
        if job.state != "active":
            return
        if pct is not None:
            job.pct = pct
        job.text = text
        self._update_job_ui(job)

    def _job_processing(self, job, text, pct=100):
        if job.state != "active":
            return
        job.can_cancel = False
        job.pct = pct
        job.text = text
        self._update_job_ui(job)

    def _job_done(self, job):
        path = find_output_file(job.folder, job.basename, job.ext)
        try:
            size = os.path.getsize(path)
        except OSError:
            size = None
        entry = {
            "name": os.path.basename(path),
            "uploader": job.uploader,
            "path": path,
            "folder": job.folder,
            "size": size,
            "url": job.source_url or job.url,
            "date": datetime.now().isoformat(timespec="seconds"),
        }
        thumb = save_thumb(job.thumb) if self.history_limit != 0 else None
        if thumb:
            entry["thumb"] = thumb
        if job.title:
            entry["title"] = job.title
        if getattr(job, "upload_date", ""):
            entry["upload_date"] = job.upload_date
        if getattr(job, "duration", None):
            entry["duration"] = job.duration
        self._add_history(entry, refresh=False)  # lent egyszer épül újra a lista
        job.entry = entry
        job.state = "done"
        job.path = path
        job.pct = 100
        job.can_cancel = False
        job.text = t("Kész, de a felirat nem jött le") if getattr(job, "sub_failed", False) \
            else t("Kész")
        if getattr(job, "fade_failed", None):
            # a szponzor rész így is kimaradt, csak az áttűnés nem készült el
            job.text = t("Kész, áttűnés nélkül (sima vágás)")
        if job.live and job.live_started and not job.live_from_start:
            job.text = t("Kész: {x} felvétel").format(x=live_elapsed(job))
        self._batch_ok.append(job)
        if self.history and self.history[0] is entry:
            # a kész videó az Előzmények kártyái közé kerül, "Kész, épp most" jelzéssel
            self._fresh[(entry.get("path"), entry.get("date"))] = time.time()
            self._remove_job_row(job)
            self._refresh_history_list(keep_page=True)
            # ha épp látszik, az "Új" jelzés előtűnik; a háttérben elkészültnél nincs animáció
            self.root.after(30, lambda: self._fade_in_status(0))
        else:
            self._update_job_ui(job)  # előzmények nélkül a kártya marad (eltávolításig)
            self._refresh_hist_subtitle()
        self._job_finished()

    def _job_cancelled(self, job, removed):
        job.state = "cancelled"
        job.text = t("Megszakítva")
        self._update_job_ui(job)
        self._remove_job_later(job, 1500)
        self._job_finished()

    def _job_error(self, job, msg):
        """A hibás letöltés a listában marad, onnan újrapróbálható vagy törölhető."""
        text, retry_ok = explain_error(msg, self.browser.get())
        job.state = "error"
        job.can_cancel = False
        job.retry_ok = retry_ok
        job.text = text if len(text) <= 420 else text[:419] + "…"
        job.failed_counted = True
        self._batch_failed += 1
        self._update_job_ui(job)
        if self.notify_popup:
            hide = self.hist_locked  # zárolt előzményeknél a cím és a kép sem látszik
            self.toasts.show(APP_NAME if hide else job.title or job.name,
                             "" if hide else job.uploader or "", kind="error",
                             thumb=None if hide else job.thumb,
                             header=t("Nem sikerült a letöltés"),
                             action=lambda: self._switch_tab("2"))
        self._job_finished()

    def _retry_job(self, job):
        if job.state != "error" or not job.retry_ok:
            return
        if sum(1 for j in self.jobs if j.unfinished) >= MAX_JOBS:
            show_dialog(self.root, "warning", t('Legfeljebb {max_jobs} letöltés lehet a sorban. Várd meg, amíg néhány elkészül.').format(max_jobs=MAX_JOBS))
            return
        self._forget_failure(job)
        job.state = "waiting"
        job.cancel_event = threading.Event()
        job.stop_event = threading.Event()
        job.can_cancel = True
        job.pct = 0
        job.text = t("Várakozik")
        self._update_job_ui(job)
        self._pump()
        self._refresh_queue_summary()

    def _dismiss_job(self, job):
        """A kész letöltés eltávolítása a listából (a fájl és az előzmény megmarad)."""
        if job.state == "done":
            self._remove_job_row(job)

    def _clear_done_jobs(self):
        for job in [j for j in self.jobs if j.state == "done"]:
            self._remove_job_row(job)

    def _delete_job(self, job):
        if job.state != "error":
            return
        self._forget_failure(job)
        delete_partial_files(job.folder, job.basename)
        if job.sub:
            delete_subtitle_files(job.folder, job.basename)
        self._remove_job_row(job)

    def _forget_failure(self, job):
        if job.failed_counted:
            job.failed_counted = False
            self._batch_failed = max(0, self._batch_failed - 1)

    def _job_finished(self):
        self._pump()
        self._refresh_queue_summary()
        if not any(j.unfinished for j in self.jobs):
            self._all_done()

    def _all_done(self):
        """Értesítés és hang csak akkor, amikor az összes letöltés elkészült."""
        ok, self._batch_ok = self._batch_ok, []
        failed, self._batch_failed = self._batch_failed, 0
        if not ok:
            return
        if len(ok) == 1 and not failed:
            message = t('{name}\n\nMappa: {folder}').format(name=ok[0].name, folder=ok[0].folder)
            self.set_status(t("Kész, a hangfájl a kiválasztott mappába került.") if ok[0].audio
                            else t("Kész, a videó a kiválasztott mappába került."))
        else:
            names = "\n".join("• " + j.name for j in ok[:6])
            if len(ok) > 6:
                names += t('\n… és még {x}').format(x=len(ok) - 6)
            message = t('Mind a(z) {n_ok} letöltés elkészült.\n\n{names}').format(n_ok=len(ok), names=names)
            if failed:
                message += t('\n\n{failed} letöltés nem sikerült.').format(failed=failed)
            self.set_status(t('Kész, {n_ok} letöltés elkészült.').format(n_ok=len(ok)))
        if self.notify_sound:
            play_done_sound(self.root)
        if self.notify_popup:  # értesítés a sarokban, nem kell OK-t nyomni
            first = ok[0]
            if len(ok) == 1:
                header = t("Kész a letöltés")
                sub = first.uploader or ""
            else:
                header = t('{n_ok} letöltés elkészült').format(n_ok=len(ok))
                sub = t('és még {x} videó').format(x=len(ok) - 1)
            if failed:
                header += t(', {failed} nem sikerült').format(failed=failed)
            entries = [j.entry for j in ok if getattr(j, "entry", None)]
            hide = self.hist_locked  # zárolt előzményeknél a cím és a kép sem látszik
            self.toasts.show(APP_NAME if hide else first.title or first.name,
                             "" if hide else sub, thumb=None if hide else first.thumb,
                             header=header, action=lambda: self._open_history_entries(entries))

    def _cancel_job(self, job):
        if job.state == "waiting":
            job.state = "cancelled"
            self._remove_job_row(job)
            self._job_finished()
        elif job.state == "active" and job.can_cancel and not job.cancel_event.is_set():
            job.cancel_event.set()
            job.text = t("Megszakítás...")
            if job.thread_id:
                # az ffmpeg-gel töltött részeknél (élő adás, kijelölt rész) a yt-dlp nem
                # figyeli a megszakítást, ezért az ffmpeg-et kell leállítani
                kill_procs(live_procs(job.thread_id))
            self._update_job_ui(job)

    def cancel_action(self):
        """A Megszakítás gomb a főképernyőn: az adatlekérést állítja le."""
        if self._phase == "fetch":
            self._cancel_fetch()

    def _remove_job_later(self, job, ms):
        try:
            self.root.after(ms, self._remove_job_row, job)
        except Exception:
            pass

    # ---------- futó letöltések (az Előzmények oldal tetején) ----------
    def _build_jobs_section(self, area):
        """FOLYAMATBAN: a futó, várakozó és hibás letöltések kártyái."""
        self.jobs_section = tk.Frame(area, bg=BG)
        self.jobs_section.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.jobs_section.columnconfigure(0, weight=1)
        head = tk.Frame(self.jobs_section, bg=BG)
        head.grid(row=0, column=0, sticky="ew", pady=(4, 6))
        head.columnconfigure(0, weight=1)
        tk.Label(head, text=t("FOLYAMATBAN"), bg=BG, fg=GREY, font=get_font(10, "bold"),
                 anchor="w").grid(row=0, column=0, sticky="w", padx=4)
        self.dl_sub = tk.Label(head, text=self._parallel_text(), bg=BG, fg=GREY,
                               font=get_font(11), justify="right", anchor="e")
        self.dl_sub.grid(row=0, column=1, sticky="e", padx=(12, 4))
        # keskeny ablaknál tördelődik, nem csúszik rá a FOLYAMATBAN feliratra
        head.bind("<Configure>", lambda e: self.dl_sub.configure(
            wraplength=max(120, e.width - 140)), add="+")
        self.dl_list = tk.Frame(self.jobs_section, bg=BG)
        self.dl_list.grid(row=1, column=0, sticky="ew")
        self.jobs_section.grid_remove()

    def _refresh_jobs_section(self):
        """A FOLYAMATBAN rész csak akkor látszik, ha van benne kártya."""
        self._update_nav_badges()
        self._refresh_hist_subtitle()
        try:
            if any(j.ui for j in self.jobs):
                self.jobs_section.grid()
            else:
                self.jobs_section.grid_remove()
            if self.history or any(j.ui for j in self.jobs):
                self.hist_empty.grid_remove()
            elif not self.hist_locked:
                self.hist_empty.grid()
        except (AttributeError, tk.TclError):
            pass

    def _build_job_row(self, job):
        card = RoundCard(self.dl_list)
        card.pack(fill="x", pady=(0, 8))
        inner = card.inner
        inner.columnconfigure(1, weight=1)
        ui = {"card": card}
        ui["thumb"] = tk.Label(inner, bg=PANEL, bd=0, highlightthickness=0)
        ui["thumb"].grid(row=0, column=0, sticky="nw", padx=(12, 0), pady=12)
        job.ui = ui
        self._render_job_thumb(job)

        body = tk.Frame(inner, bg=PANEL)
        body.grid(row=0, column=1, sticky="ew", padx=14, pady=(12, 12))
        body.columnconfigure(0, weight=1)
        top = tk.Frame(body, bg=PANEL)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        name = job.title or job.name
        name = name if len(name) <= 120 else name[:119] + "…"
        ui["name"] = tk.Label(top, text=name, bg=PANEL, fg=TEXT, anchor="w", justify="left",
                              font=get_font(13, "bold"))
        ui["name"].grid(row=0, column=0, sticky="w")
        btns = tk.Frame(top, bg=PANEL)
        btns.grid(row=0, column=1, padx=(10, 0), sticky="ne")
        # a hosszú cím tördelődik, nem csúszik a gombok alá
        top.bind("<Configure>", lambda e, lab=ui["name"], b=btns: lab.configure(
            wraplength=max(120, e.width - b.winfo_reqwidth() - 14)))
        small = (FONT_FAMILY, 12)
        ui["stop"] = RoundButton(btns, t("■  Leállítás és mentés"),
                                 lambda j=job: self._stop_live(j), width=180, height=28,
                                 font=small)
        ui["btn"] = secondary_button(btns, t("Megszakítás"), lambda j=job: self._cancel_job(j),
                                width=110, height=28, font=small)
        ui["retry"] = secondary_button(btns, t("Újrapróbálás"), lambda j=job: self._retry_job(j),
                                  width=110, height=28, font=small)
        ui["delete"] = secondary_button(btns, t("Törlés"), lambda j=job: self._delete_job(j),
                                   width=70, height=28, fg="DANGER", font=small)
        ui["remove"] = secondary_button(btns, t("Eltávolítás"), lambda j=job: self._dismiss_job(j),
                                   width=100, height=28, font=small)

        shown = job.source_url or job.url
        link_text = shown if len(shown) <= 58 else shown[:57] + "…"
        link = tk.Label(body, text=link_text, bg=PANEL, fg=ACCENT_TEXT, anchor="w",
                        cursor="hand2",
                        font=get_font(11, underline=True))
        link.grid(row=1, column=0, sticky="w", pady=(2, 8))
        link.bind("<Button-1>", lambda e, u=(job.source_url or job.url): self._open_url(u))

        ui["bar"] = RoundProgress(body, height=6)
        ui["bar"].grid(row=2, column=0, sticky="ew")
        ui["status"] = tk.Label(body, text=job.text, bg=PANEL, fg=GREY, anchor="w",
                                justify="left", wraplength=300, font=(FONT_FAMILY, 12))
        ui["status"].grid(row=3, column=0, sticky="w", pady=(6, 0))
        body.bind("<Configure>", lambda e, st=ui["status"]: st.configure(
            wraplength=max(120, e.width - 4)))
        # dupla kattintás a kész letöltésen: Előzmények, kijelölve ez a videó
        skip = {link} | {w for w in ui.values() if isinstance(w, RoundButton)}

        def bind_all_rows(widget):
            if widget not in skip:
                widget.bind("<Double-Button-1>", lambda e, j=job: self._job_double_click(j),
                            add="+")
                for child in widget.winfo_children():
                    bind_all_rows(child)
        bind_all_rows(card)
        self._update_job_ui(job)
        self._refresh_jobs_section()

    def _job_double_click(self, job):
        if job.state == "done" and getattr(job, "entry", None) is not None:
            self._open_history_entries([job.entry])

    def _open_url(self, url):
        if url.startswith(("http://", "https://")):
            webbrowser.open(url)

    def _render_job_thumb(self, job):
        ui = job.ui
        if not ui:
            return
        img = self._make_thumbnail(job.thumb, (96, 54)) if job.thumb else None
        ui["photo"] = img  # a képet tartani kell
        if img is None:  # amíg nincs kép: üres helyőrző, hogy a kártyák egy vonalban legyenek
            if getattr(self, "_blank_img", None) is None:
                self._blank_img = tk.PhotoImage(width=1, height=1)
            ui["thumb"].configure(image=self._blank_img, width=96, height=54, bg=CHIP)
        else:
            ui["thumb"].configure(image=img, width=img.width(), height=img.height(), bg=PANEL)
        ui["thumb"].grid()

    def _update_job_ui(self, job):
        ui = job.ui
        if not ui:
            return
        try:
            recording = job.live and job.state == "active" and job.can_cancel \
                and not job.stop_event.is_set() and not job.cancel_event.is_set()
            ui["bar"].set_live(recording)
            ui["bar"].set(100 if job.live and job.state == "done" else job.pct)
            failed = job.state == "error"
            ui["status"].configure(fg=DANGER if failed or recording else GREY)
            ui["card"].set_outline("DANGER" if failed else "BORDER")
            self._tick_job_text(job)
            cancellable = job.state in ("waiting", "active") and job.can_cancel \
                and not job.cancel_event.is_set()
            ui["btn"].set_state("normal" if cancellable else "disabled")
            for key in ("stop", "btn", "retry", "delete", "remove"):
                ui[key].pack_forget()
            if failed:
                if job.retry_ok:
                    ui["retry"].pack(side="left", padx=(0, 6))
                ui["delete"].pack(side="left")
            elif job.state == "done":
                ui["remove"].pack(side="left")
            else:
                if job.live and job.state == "active":
                    ui["stop"].set_state("normal" if recording else "disabled")
                    ui["stop"].pack(side="left", padx=(0, 6))
                ui["btn"].pack(side="left")
        except tk.TclError:
            pass

    def _tick_job_text(self, job):
        """A százalék nem ugrik, hanem gyorsan felpörög az új értékig (pl. 41, 43, 45%)."""
        ui = job.ui
        if not ui:
            return
        m = re.match(r"(\d+)%(.*)", job.text, re.S)
        if not m or job.state != "active":
            ui["shown_pct"] = None
            ui["status"].configure(text=job.text)
            return
        target, rest = int(m.group(1)), m.group(2)
        shown = ui.get("shown_pct")
        if shown is None or target < shown:
            shown = target
        elif shown < target:
            shown += max(1, round((target - shown) * 0.35))
        ui["shown_pct"] = shown
        try:
            ui["status"].configure(text=f"{shown}%{rest}")
            if shown < target and not ui.get("pct_job"):
                def again():
                    ui["pct_job"] = None
                    self._tick_job_text(job)
                ui["pct_job"] = self.root.after(30, again)
        except tk.TclError:
            pass

    def _remove_job_row(self, job):
        ui, job.ui = job.ui, None
        if ui:
            try:
                ui["card"].destroy()
            except tk.TclError:
                pass
        self.jobs = [j for j in self.jobs if j is not job or j.unfinished]
        self._refresh_jobs_section()
        self._refresh_queue_summary()

    def _refresh_queue_summary(self, announce=False):
        waiting = sum(1 for j in self.jobs if j.state == "waiting")
        active = sum(1 for j in self.jobs if j.state == "active")
        self._update_nav_badges()
        self._refresh_hist_subtitle()
        btn = getattr(self, "clear_done_btn", None)
        if btn is not None:
            if any(j.state == "done" and j.ui for j in self.jobs):
                btn.grid()
            else:
                btn.grid_remove()
        if announce and self._phase is None and self.info_data is None:
            self.set_status(t('Hozzáadva. Most {active} fut, {waiting} vár. Az Előzmények oldalon látod az állapotukat.').format(active=active, waiting=waiting))

class PHDL(LockMixin, HistoryMixin, SettingsMixin, UpdateMixin, ExtrasMixin,
           DownloaderMixin, QueueMixin):
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        # mentett beállítások és előzmények
        default_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        self.settings = sanitize_settings(load_json(SETTINGS_FILE, {}), default_folder)
        self.theme_mode = self.settings["theme"]
        self.theme_style = self.settings["style"]
        self.notify_popup = self.settings["notify_popup"]
        self.embed_metadata = self.settings["embed_metadata"]
        self.speed_limit = self.settings["speed_limit"]
        self.speed_limit_on = self.settings["speed_limit_on"]
        self.speed_custom = self.settings["speed_custom"] or \
            self.speed_limit not in SPEED_LIMITS_MB
        self.max_parallel = self.settings["max_parallel"]
        self.parallel_custom = self.settings["parallel_custom"] or \
            self.max_parallel not in PARALLEL_PRESETS + (0,)
        install_speed_limit()
        self._apply_speed_limit()
        self.sb_mode = self.settings["sb_mode"]
        self.sb_categories = list(self.settings["sb_categories"])
        self.toast_anim = self.settings["toast_anim"]
        self.notify_sound = self.settings["notify_sound"]
        self.history_limit = self.settings["history_limit"]
        self.temp_local = self.settings["temp_local"]
        self.player_volume = self.settings["player_volume"]
        self.player_engine = self.settings["player_engine"]
        self.player_geom = {"video": self.settings["player_geom_video"],
                            "audio": self.settings["player_geom_audio"]}
        self.seen_version = self.settings["seen_version"]  # None: friss telepítés
        self.temp_dir = self.settings["temp_dir"]  # None: a rendszer ideiglenes mappája
        cleanup_old_temp(self.temp_dir)
        self.lock = self.settings["history_lock"]  # None, ha nincs jelszó
        self.hist_locked = bool(self.lock)  # indításkor mindig zárolt, ha van jelszó
        self._lock_fails = 0
        self._lock_blocked_until = 0.0
        self._last_activity = time.time()
        self._sys_look = system_appearance() if needs_system(self.theme_style,
                                                             self.theme_mode) else None
        apply_palette(theme_palette(self.theme_style, self.theme_mode, self._sys_look))
        set_theme_radius(self.theme_style)
        root.configure(bg=BG)
        self.history = clean_history(load_json(HISTORY_FILE, []), history_cap(self.history_limit))
        self._save_job = None
        self.recent_folders = self.settings["recent_folders"]

        root.geometry(self.settings["geometry"] or DEFAULT_GEOMETRY)
        root.minsize(*MIN_SIZE)
        self._set_app_icon()

        self.folder = tk.StringVar(value=self.settings["folder"])
        self.url = tk.StringVar()
        self.resolution = tk.StringVar()
        self.hdr = tk.BooleanVar(value=False)
        self.quality = tk.StringVar(value=DEFAULT_QUALITY)
        self.browser = tk.StringVar(value=self.settings["cookie_browser"])
        self.language = self.settings["language"]

        notes = []
        if not HAS_IMPERSONATE:
            notes.append(t("néhány oldal nem fog működni, mert a curl_cffi csomag hiányzik"))
        if not HAS_PIL:
            notes.append(t("a bélyegképek nem látszanak, mert a pillow csomag hiányzik"))
        start_text = ""
        if notes:
            start_text = t("\nFigyelem: ").strip() + " " + "; ".join(notes) + "."
        self.status = tk.StringVar(value=start_text)
        self.busy = False
        self.jobs = []
        self._batch_ok = []
        self._batch_failed = 0
        self._phase = None  # None, "fetch" vagy "download"
        self._fetch_pct = 0.0
        self._fetch_stage = ""
        self._fetch_t0 = time.time()
        self._fetch_id = 0  # a lekérések azonosítója, a megszakított lekérés eredményét eldobjuk
        self._fetch_cancel = threading.Event()
        self._hist_url = ""
        self._about_win = None
        self._changelog_win = None
        self._player = None
        self._about_icon_img = None
        self._stall_job = None
        self._hist_index = None

        # a lekért videóadatok
        self.info_data = None
        self.info_url = None
        self._photo = None
        self._thumb_bytes = None

        # a yt-dlp frissítés-ellenőrzés állapota
        self._latest_ytdlp = None
        self._latest_release = None
        self._checking = False
        self._update_busy = None  # None vagy "download"
        self._installed_ver = None  # az appból letöltött, még nem aktív verzió
        self._update_status = YTDLP_NOTE or ""

        self._build_style()
        self._build_ui()
        self._install_scroll_router()
        self._refresh_news_pill()
        self._apply_lock_state()
        self._last_pointer = self.root.winfo_pointerxy()
        for seq in ("<Key>", "<ButtonPress>", "<MouseWheel>"):
            self.root.bind_all(seq, self._touch, add="+")
        self.root.after(5000, self._lock_tick)
        self._start_update_check()
        self.root.after(UPDATE_CHECK_INTERVAL_MS, self._periodic_update_check)
        self._setup_drop()
        self._setup_persistence()
        self._setup_about_menu()

    # ---------- téma ----------
    def set_theme_mode(self, mode):
        """A téma módjának váltása (sötét, világos vagy a rendszer szerint), mentéssel."""
        if mode not in THEME_MODES:
            return
        self.theme_mode = mode
        self.settings["theme"] = mode
        self._save_settings()
        if needs_system(self.theme_style, mode):
            self._sys_look = system_appearance()
            self._watch_system_theme()
        self._apply_theme()
        try:
            self.theme_ctl.set_value(mode)
        except (tk.TclError, AttributeError):
            pass

    def set_theme_style(self, style):
        """Téma választása (PH, YT, VD), mentéssel együtt."""
        if style not in THEME_STYLES or style == self.theme_style:
            return
        self.theme_style = style
        self.settings["style"] = style
        self._save_settings()
        if needs_system(style, self.theme_mode):
            self._sys_look = system_appearance()
        self._apply_theme()
        self._set_app_icon()
        try:
            self.brand.set_style(style)
            self.style_var.set(THEME_STYLES[style])
        except (tk.TclError, AttributeError):
            pass
        if needs_system(style, self.theme_mode):
            self._watch_system_theme()


    def _watch_system_theme(self):
        """Ha a téma a rendszert követi (VD vagy Rendszer mód), pár másodpercenként megnézzük,
        váltott-e a rendszer sötétre/világosra vagy más kiemelő színre."""
        if getattr(self, "_sys_watch", False):
            return
        self._sys_watch = True

        def tick():
            if not needs_system(self.theme_style, self.theme_mode):
                self._sys_watch = False
                return

            def work():
                look = system_appearance()
                try:
                    self.root.after(0, lambda: done(look))
                except Exception:
                    pass

            def done(look):
                if needs_system(self.theme_style, self.theme_mode) and look != self._sys_look:
                    self._sys_look = look
                    self._apply_theme()
                self.root.after(6000, tick)
            threading.Thread(target=work, daemon=True).start()
        self.root.after(6000, tick)

    def _apply_theme(self):
        new = theme_palette(self.theme_style, self.theme_mode, self._sys_look)
        radius_before = RADIUS
        set_theme_radius(self.theme_style)
        if new == PAL:
            if RADIUS != radius_before:
                retheme(self.root, PAL, PAL)  # csak a lekerekítés változott: újrarajzolás
            return
        old = dict(PAL)
        apply_palette(new)
        self._build_style()
        retheme(self.root, old, PAL)
        if self.info_data and self._thumb_bytes:
            self._photo = self._make_thumbnail(self._thumb_bytes)
            self.preview.show(self.info_data.get("title") or t("Névtelen videó"),
                              self._details_rows(), self._photo,
                              pil=self._thumb_image(self._thumb_bytes))
        self._render_hist_thumb()
        for job in self.jobs:
            self._render_job_thumb(job)

    # ---------- beállítások mentése ----------
    def _setup_persistence(self):
        self.browser.trace_add("write", self._schedule_save)
        self.folder.trace_add("write", self._schedule_save)
        self.root.bind("<Configure>", self._on_configure, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        try:  # Cmd+Q Macen
            self.root.createcommand("::tk::mac::Quit", self._on_close)
        except Exception:
            pass

    def _on_configure(self, event):
        if event.widget is self.root:
            self._schedule_save()
            # Macen az ablak mozgatása (főleg két kijelző között) után a saját rajzolású
            # elemek (oldalsáv, logó, gombok) néha üresen maradtak, amíg rájuk nem mutattál:
            # a mozgás végén mindet újrarajzoljuk
            job = getattr(self, "_repaint_job", None)
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
            self._repaint_job = self.root.after(180, self._repaint_chrome)

    def _repaint_chrome(self):
        self._repaint_job = None
        roots = [self.sidebar]  # az oldalak elemei a méretváltozáskor maguktól újrarajzolódnak
        # az oldalsáv háttere is (Macen mozgatás után néha feketén maradt): a színt újra
        # beállítva a Tk újrafesti
        side = [self.sidebar]
        while side:
            w = side.pop()
            try:
                if "bg" in w.keys():
                    w.configure(bg=w.cget("bg"))
                side.extend(w.winfo_children())
            except tk.TclError:
                pass
        stack = list(roots)
        while stack:
            w = stack.pop()
            draw = getattr(w, "_draw", None)
            if callable(draw):
                try:
                    draw()
                except Exception:
                    pass
            try:
                stack.extend(w.winfo_children())
            except tk.TclError:
                pass

    def _schedule_save(self, *_):
        if self._save_job is not None:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(600, self._save_settings)

    def _save_settings(self):
        if self._save_job is not None:
            try:
                self.root.after_cancel(self._save_job)
            except Exception:
                pass
            self._save_job = None
        data = dict(self.settings)
        data["cookie_browser"] = self.browser.get()
        data["recent_folders"] = self.recent_folders
        data["theme"] = self.theme_mode
        data["style"] = self.theme_style
        data["history_lock"] = self.lock
        data["notify_popup"] = self.notify_popup
        data["toast_anim"] = self.toast_anim
        data["notify_sound"] = self.notify_sound
        data["history_limit"] = self.history_limit
        data["temp_local"] = self.temp_local
        data["temp_dir"] = self.temp_dir
        data["seen_version"] = self.seen_version
        data["player_volume"] = self.player_volume
        data["player_engine"] = self.player_engine
        data["player_geom_video"] = self.player_geom["video"]
        data["player_geom_audio"] = self.player_geom["audio"]
        data["language"] = self.language
        data["embed_metadata"] = self.embed_metadata
        data["speed_limit"] = self.speed_limit
        data["speed_limit_on"] = self.speed_limit_on
        data["speed_custom"] = self.speed_custom
        data["max_parallel"] = self.max_parallel
        data["parallel_custom"] = self.parallel_custom
        data["sb_mode"] = self.sb_mode
        data["sb_categories"] = list(self.sb_categories)
        folder = self.folder.get().strip()
        if os.path.isdir(folder):
            data["folder"] = folder
        try:
            if self.root.winfo_viewable():
                data["geometry"] = self.root.geometry()
        except tk.TclError:
            pass
        self.settings = data
        save_json(SETTINGS_FILE, data)

    def set_language_choice(self, code):
        """A Nyelv választó: mentjük, és felajánljuk az újraindítást."""
        if code == self.language:
            return
        self.language = self.settings["language"] = code
        self._save_settings()
        if show_confirm(self.root, t("Nyelv"),
                        t("Az új nyelv az app újraindítása után lép életbe."),
                        yes_text=t("Újraindítás most"), no_text=t("Később")):
            self._on_close(restart=True)

    def _on_close(self, restart=False):
        running = [j for j in self.jobs if j.unfinished]
        text = t('Még {n_running} letöltés fut vagy vár. Ha kilépsz, ezek megszakadnak.\n\nBiztosan kilépsz?').format(n_running=len(running))
        if any(j.live and j.state == "active" for j in running):
            text += "\n\n" + t("Az élő felvételt előbb állítsd le a Leállítás és mentés gombbal, "
                               "különben elveszik.")
        if running and not show_confirm(
                self.root, t("Kilépés"), text, yes_text=t("Kilépés"), no_text=t("Mégse"),
                danger=True):
            return
        for job in running:
            job.cancel_event.set()
        kill_all_tracked()
        pl = getattr(self, "_player", None)
        if pl is not None:
            pl.close()
        self._save_settings()
        self.root.destroy()
        if restart:
            relaunch_app()

    # ---------- kinézet ----------
    def _set_app_icon(self):
        """Ablak-, tálca- és Dock-ikon a témához illően (theme_icon). Ha nincs icon.png,
        az app ikon nélkül is megy."""
        path = resource_path("icon.png")
        if not os.path.exists(path):
            return
        style = self.theme_style
        try:
            if not HAS_PIL:
                self._icon = tk.PhotoImage(file=path)
                self.root.iconphoto(True, self._icon)
                return
            img = theme_icon(style, path)
            if is_mac():
                # Macen nem a Tk-n át: az iconphoto induláskor néha nem hatott, és a kettő
                # felülírhatta egymást. A Dock ikon a mentett png-ből, AppKit-tel.
                cache = os.path.join(app_data_dir(), "icons")
                os.makedirs(cache, exist_ok=True)
                png = os.path.join(cache, f"icon_{style}_{APP_VERSION}.png")
                if not os.path.exists(png):
                    img.save(png)
                for name in os.listdir(cache):  # a korábbi verziók ikonjai
                    if name.endswith(".png") and not name.endswith(f"_{APP_VERSION}.png"):
                        try:
                            os.remove(os.path.join(cache, name))
                        except OSError:
                            pass
                self._dock_png = png
                for delay in (0, 400, 1500):  # induláskor a rendszer még átírhatja
                    self.root.after(delay, self._apply_dock_icon, png)
                return
            self._icon = ImageTk.PhotoImage(img.resize((256, 256), Image.LANCZOS))
            self.root.iconphoto(True, self._icon)
        except Exception:
            log_exc("_set_app_icon")

    def _apply_dock_icon(self, png):
        if png != getattr(self, "_dock_png", None):
            return  # közben újabb téma jött
        try:
            mac_set_dock_icon(png)
        except Exception:
            log_exc("mac_set_dock_icon")

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT, font=(FONT_FAMILY, 13))
        style.configure("Title.TLabel", foreground=TEXT, font=(FONT_FAMILY, 28, "bold"))
        style.configure("AboutTitle.TLabel", foreground=TEXT, font=(FONT_FAMILY, 22, "bold"))
        style.configure("Sub.TLabel", foreground=GREY, font=(FONT_FAMILY, 12))
        style.configure("Field.TLabel", foreground=GREY, font=(FONT_FAMILY, 12))
        style.configure("Dim.TLabel", foreground=GREY, font=(FONT_FAMILY, 13))
        style.configure("Status.TLabel", foreground=GREY, font=(FONT_FAMILY, 13))

        # fülek
        style.configure("TNotebook", background=BG, borderwidth=0, bordercolor=BG,
                        lightcolor=BG, darkcolor=BG, tabmargins=(14, 0, 0, 0))
        style.configure("TNotebook.Tab", background=PANEL, foreground=GREY,
                        padding=(20, 8), borderwidth=0, bordercolor=PANEL,
                        lightcolor=PANEL, darkcolor=PANEL, font=(FONT_FAMILY, 13))
        style.map("TNotebook.Tab",
                  background=[("selected", ACCENT), ("active", CONTROL_HOVER)],
                  foreground=[("selected", ACCENT_FG), ("active", TEXT)],
                  bordercolor=[("selected", ACCENT)],
                  lightcolor=[("selected", ACCENT)],
                  darkcolor=[("selected", ACCENT)],
                  padding=[("selected", (20, 8))],
                  expand=[("selected", (0, 0, 0, 0))])
        # a fókuszkeret nélküli fülelrendezés
        # a füleket a fenti kapcsoló váltja, a saját fülsor nem látszik
        style.layout("TNotebook.Tab", [])

        style.configure("Flat.TCombobox", fieldbackground=PANEL, background=PANEL,
                        foreground=TEXT, arrowcolor=TEXT, bordercolor=PANEL,
                        lightcolor=PANEL, darkcolor=PANEL, borderwidth=0,
                        padding=4, arrowsize=18, insertcolor=TEXT,
                        selectbackground=PANEL, selectforeground=TEXT)
        style.map("Flat.TCombobox",
                  fieldbackground=[("readonly", PANEL), ("disabled", PANEL)],
                  foreground=[("readonly", TEXT), ("disabled", GREY)],
                  selectbackground=[("readonly", PANEL)],
                  selectforeground=[("readonly", TEXT)],
                  bordercolor=[("focus", PANEL)],
                  lightcolor=[("focus", PANEL)],
                  darkcolor=[("focus", PANEL)])

        style.configure("Chip.TCombobox", fieldbackground=CHIP, background=CHIP,
                        foreground=TEXT, arrowcolor=TEXT, bordercolor=CHIP,
                        lightcolor=CHIP, darkcolor=CHIP, borderwidth=0,
                        padding=(8, 3), arrowsize=18, insertcolor=TEXT,
                        selectbackground=CHIP, selectforeground=TEXT)
        style.map("Chip.TCombobox",
                  fieldbackground=[("readonly", CHIP), ("disabled", CHIP)],
                  foreground=[("readonly", TEXT), ("disabled", GREY)],
                  selectbackground=[("readonly", CHIP)],
                  selectforeground=[("readonly", TEXT)],
                  bordercolor=[("focus", CHIP)],
                  lightcolor=[("focus", CHIP)],
                  darkcolor=[("focus", CHIP)])

        style.configure("Vertical.TScrollbar", background=SCROLL, troughcolor=PANEL,
                        bordercolor=PANEL, arrowcolor=GREY, lightcolor=SCROLL,
                        darkcolor=SCROLL, arrowsize=14)
        style.map("Vertical.TScrollbar", background=[("active", GREY)])

        # a lenyíló mezők értékét az egérgörgő ne tudja véletlenül átváltani:
        # csak a lenyíló menüből lehet választani (a görgetés az oldalt mozgatja)
        # (az 'all' szintű elosztó ettől még görgeti az oldalt a lenyíló fölött is)
        for seq in ("<MouseWheel>", "<Shift-MouseWheel>", "<Button-4>", "<Button-5>",
                    "<TouchpadScroll>"):
            try:
                self.root.bind_class("TCombobox", seq, lambda e: None)
            except tk.TclError:
                pass

        self.root.option_add("*TCombobox*Listbox.background", PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", ACCENT_FG)

    def _build_ui(self):
        # bal oldali sáv: felirat, Letöltő / Előzmények / Beállítások, alul Ko-fi és verzió
        side = tk.Frame(self.root, bg=SIDEBAR, width=SIDEBAR_WIDTH)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self.sidebar = side
        tk.Frame(self.root, bg=BORDER, width=1).pack(side="left", fill="y")
        content = tk.Frame(self.root, bg=BG)
        content.pack(side="left", fill="both", expand=True)
        self.content = content

        self.brand = BrandMark(side, self.theme_style)
        self.brand.pack(anchor="w", padx=18, pady=(22, 20))
        tk.Label(side, text=t("KÖNYVTÁR"), bg=SIDEBAR, fg=GREY, font=get_font(10, "bold"),
                 anchor="w").pack(fill="x", padx=20, pady=(0, 6))
        self.nav = {}
        for key, icon, text, tab in (("dl", "⬇", t("Letöltő"), None), ("hist", "◷", t("Előzmények"), 2),
                                     ("set", "⚙", t("Beállítások"), 3)):
            item = NavItem(side, icon, text, lambda k=key: self._nav_go(k))
            item.pack(fill="x", padx=10, pady=1)
            self.nav[key] = item
        tk.Frame(side, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Label(side, text=f"v.{APP_VERSION}\n{CREDIT}", bg=SIDEBAR, fg=GREY,
                 justify="center", font=(FONT_FAMILY, 10)).pack(side="bottom", pady=(0, 14))
        self.kofi_btn = RoundButton(
            side, t("\u2665  Ko-fi támogatás"), lambda: webbrowser.open(SUPPORT_URL),
            width=SIDEBAR_WIDTH - 36, height=38, bg="CONTROL", fg="TEXT",
            hover="CONTROL_HOVER", outline="BORDER", font=(FONT_FAMILY, 12, "bold"))
        self.kofi_btn.pack(side="bottom", pady=(0, 10))
        # diszkrét értesítés frissítés vagy első indítás után, kattintásig látszik
        self.news_row = tk.Frame(side, bg=SIDEBAR)
        self.news_row.pack(side="bottom", fill="x", padx=14)
        self.news_pill = tk.Label(
            self.news_row, text=t("●  Újdonságok ebben a verzióban"), wraplength=SIDEBAR_WIDTH - 50,
            bg=PANEL, fg=ACCENT_TEXT, cursor="hand2", padx=10, pady=5, justify="left",
            highlightthickness=1, highlightbackground=BORDER, font=(FONT_FAMILY, 11))
        # felengedésre nyílik, mint a gombok: lenyomásra a Mac a főablakot hozná vissza előre
        self.news_pill.bind("<ButtonRelease-1>", lambda e: self.show_changelog())
        self.news_pill.bind("<Enter>", lambda e: self.news_pill.configure(
            font=get_font(11, underline=True)))
        self.news_pill.bind("<Leave>", lambda e: self.news_pill.configure(
            font=(FONT_FAMILY, 11)))

        # Cmd/Ctrl+K: keresőmenü (a bal sávban is látszik, hogy van ilyen)
        self.cmd_menu = CommandMenu(self)
        search = NavItem(side, "\u2315", t("Keresés"), self.cmd_menu.toggle)
        search.set_badge("\u2318K" if is_mac() else t("Ctrl+K"))
        search.pack(side="bottom", fill="x", padx=10, pady=(0, 10), after=self.kofi_btn)
        self.nav_search = search
        self.root.bind_all(f"<{MOD_KEY}-k>", self.cmd_menu.toggle)
        self.root.bind_all(f"<{MOD_KEY}-K>", self.cmd_menu.toggle)
        self.toasts = ToastStack(content, self.toast_anim)

        self._dl_sub = 0

        self.notebook = ttk.Notebook(content)
        self.notebook.pack(fill="both", expand=True, pady=(4, 0))
        # fülváltáskor ez a háttérszínű takaró húzódik el az új fül elől
        self._veil = tk.Frame(self.notebook, bg=BG)
        self._veil_job = None
        main = ttk.Frame(self.notebook, padding=(28, 18, 28, 18))
        downloads = ttk.Frame(self.notebook, padding=(28, 18, 28, 18))
        history = ttk.Frame(self.notebook, padding=(28, 18, 28, 18))
        settings = ttk.Frame(self.notebook, padding=(28, 18, 28, 18))
        self.notebook.add(main, text=t("Letöltő"))
        self.notebook.add(downloads, text=t("Aktív letöltések"))
        self.notebook.add(history, text=t("Előzmények"))
        self.notebook.add(settings, text=t("Beállítások"))
        # a futó letöltések az Előzmények oldalon vannak; a régi fül sorszáma megmarad,
        # hogy a többi oldal sorszáma ne változzon, de soha nem látszik
        self.notebook.hide(downloads)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed, add="+")

        self._build_downloader_tab(main)
        self._build_history_tab(history)
        self._build_settings_tab(settings)

    def _switch_tab(self, value):
        """Fülváltás animáció nélkül (az oldalsávos elrendezéshez az azonnali váltás illik)."""
        try:
            new, old = int(value), self.notebook.index("current")
        except (ValueError, tk.TclError):
            return
        if new == 1:  # a régi "Aktív letöltések": ma az Előzmények teteje
            new = 2
        if new == old:
            return
        self._veil_end()
        try:
            self.notebook.select(new)
        except tk.TclError:
            pass

    def _veil_end(self):
        if self._veil_job is not None:
            try:
                self.root.after_cancel(self._veil_job)
            except Exception:
                pass
            self._veil_job = None
        try:
            self._veil.place_forget()
        except tk.TclError:
            pass

    def _veil_step(self):
        self._veil_job = None
        t = (time.time() - self._veil_t0) / (0.10 * ANIM_SLOW)
        if t >= 1:
            self._veil_end()
            return
        e = 1 - (1 - t) ** 2  # lassulva érkezik
        try:
            width = self.notebook.winfo_width()
            cut = int(e * width)
            x = cut if self._veil_dir > 0 else 0
            self._veil.place(x=x, y=0, width=max(1, width - cut), relwidth=0, relheight=1)
            self._veil_job = self.root.after(12, self._veil_step)
        except tk.TclError:
            self._veil_end()

    def _fly_thumbnail(self, data, src):
        """A letöltés indításakor a bélyegkép egy íven az oldalsáv Előzmények sorához repül."""
        if not (HAS_PIL and data and src):
            return
        base = self._thumb_image(data, (src[2], src[3]), bg=BG)
        if base is None:
            return
        root = self.root
        try:
            ctl = self.nav["hist"]  # az oldalsáv Előzmények sorába repül
            tx = ctl.winfo_rootx() - root.winfo_rootx() + ctl.winfo_width() - 24
            ty = ctl.winfo_rooty() - root.winfo_rooty() + ctl.winfo_height() / 2
            c0x = src[0] - root.winfo_rootx() + base.width / 2
            c0y = src[1] - root.winfo_rooty() + base.height / 2
            label = tk.Label(root, bd=0, highlightthickness=0, bg=BG)
        except tk.TclError:
            return
        # az ív vezérlőpontja: előbb felfelé, aztán oldalra, ez ad lendületet
        qx, qy = c0x + (tx - c0x) * 0.15, ty + (c0y - ty) * 0.15
        t0, dur = time.time(), 0.32 * ANIM_SLOW

        def finish():
            try:
                label.destroy()
            except tk.TclError:
                pass

        def step():
            t = min(1.0, (time.time() - t0) / dur)
            e = t * t * (3 - 2 * t)
            cx = (1 - e) ** 2 * c0x + 2 * (1 - e) * e * qx + e * e * tx
            cy = (1 - e) ** 2 * c0y + 2 * (1 - e) * e * qy + e * e * ty
            scale = 1 - 0.78 * e
            w, h = max(20, int(base.width * scale)), max(12, int(base.height * scale))
            try:
                photo = ImageTk.PhotoImage(base.resize((w, h), Image.BILINEAR))
                label.configure(image=photo)
                label.image = photo
                label.place(x=int(cx - w / 2), y=int(cy - h / 2))
                label.lift()
                if t < 1:
                    root.after(16, step)
                else:
                    finish()
            except tk.TclError:
                finish()
        step()

    # ---------- linkek behúzása ----------
    def _setup_drop(self):
        """A böngészőből behúzott link (vagy több link) az ablak bármely részére ejthető."""
        self.drop_ready = False
        if not HAS_DND:
            return
        try:
            tkinterdnd2.TkinterDnD._require(self.root)
            for widget in (self.sidebar, self.content):
                widget.drop_target_register(tkinterdnd2.DND_TEXT, tkinterdnd2.DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_ready = True
        except Exception:
            log_exc("_setup_drop")

    def _dropped_links(self, data):
        links = extract_links(data)
        if links:
            return links
        # fájlok: a böngésző linkfájljai (.url, .webloc) vagy szövegfájl linkekkel
        try:
            paths = self.root.tk.splitlist(data)
        except tk.TclError:
            paths = []
        for path in paths:
            try:
                if os.path.isfile(path) and os.path.getsize(path) < 1_000_000:
                    with open(path, encoding="utf-8", errors="ignore") as f:
                        links += [u for u in extract_links(f.read()) if u not in links]
            except OSError:
                pass
        return links

    def _on_drop(self, event):
        links = self._dropped_links(getattr(event, "data", "") or "")
        action = getattr(event, "action", "copy")
        if not links:
            return action
        self._dl_sub = 0
        self._switch_tab("0")
        if self.busy or self._phase is not None:
            show_dialog(self.root, "warning", t("Várd meg, amíg az előző videó adatai "
                                               "megérkeznek, utána húzd be újra a linket."))
            return action
        self.url.set("\n".join(links))
        self.fetch_info()
        return action

    def _nav_go(self, key):
        """Kattintás a bal oldali sávban: a Letöltő a legutóbbi aloldalára nyílik."""
        tab = {"dl": 0, "hist": 2, "set": 3}[key]
        self._switch_tab(str(tab))

    def _update_nav_badges(self):
        try:
            n = 0 if self.hist_locked else sum(1 for j in self.jobs if j.state == "active")
            self.nav["dl"].set_badge("")
            # futó letöltésnél mozgó lefelé nyíl és a futók száma, egyébként semmi
            self.nav["hist"].set_activity(n)
        except (AttributeError, KeyError, tk.TclError):
            pass

    def _on_tab_changed(self, _event=None):
        try:
            index = self.notebook.index("current")
        except tk.TclError:
            return
        for key, tabs in (("dl", (0,)), ("hist", (1, 2)), ("set", (3,))):
            self.nav[key].set_selected(index in tabs)
        if index == 2 and self.hist_locked:
            self.root.after(50, self._lock_entry.focus_set)
        if index == 2 and not self.hist_locked:
            self._check_missing_async()  # közben törölhettél fájlt, vagy visszajött a NAS
        if index == 3 and self._latest_ytdlp is None:
            # ha az induláskori ellenőrzés nem sikerült (pl. nem volt net), újrapróbáljuk
            self._start_update_check()


def relaunch_app():
    """Az app újraindítása (a nyelvváltás után). Macen a kész app az open paranccsal,
    Linuxon az AppImage fájl indul újra (a kicsomagolt mappa a kilépéskor eltűnik)."""
    try:
        if getattr(sys, "frozen", False):
            exe = os.environ.get("APPIMAGE") or sys.executable
            bundle = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", ".."))
            if is_mac() and bundle.endswith(".app"):
                cmd = ["open", "-n", bundle]
            else:
                cmd = [exe]
        else:
            cmd = [sys.executable, os.path.abspath(__file__)]
        kw = {"close_fds": True}
        if not is_win():
            kw["start_new_session"] = True
        subprocess.Popen(cmd, **kw)
    except Exception:
        log_exc("relaunch_app")


def self_test():
    """Hibakereséshez: "--selftest" kapcsolóval kiírja, melyik ffmpeg és mpv indulna."""
    print(f"{APP_NAME} {APP_VERSION}, yt-dlp {YTDLP_VERSION}, hang: {HAS_AUDIO}, "
          f"nyelv: {LANG} ({t('Beállítások')}), behúzás: {HAS_DND}")
    for name, flag in (("ffmpeg", "-version"), ("ffprobe", "-version"), ("mpv", "--version")):
        path = shutil.which(name)
        first = ""
        if path:
            try:
                first = subprocess.run([path, flag], capture_output=True, text=True,
                                       timeout=20).stdout.splitlines()[0]
            except Exception as e:
                first = f"HIBA: {e}"
        print(f"{name}: {path or 'nincs'}  {first}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        self_test()
        sys.exit(0)
    enable_sharp_scaling()
    root = tk.Tk()
    install_error_logging(root)
    PHDL(root)
    root.after(1500, hide_support_folders)  # addigra az adatok mappa is létrejön
    root.mainloop()
    # a háttérszálak (yt-dlp, ffmpeg) ne tartsák életben az appot kilépés után
    kill_all_tracked()
    for stream in (sys.stdout, sys.stderr):
        # ablakos (konzol nélküli) Windows appnál ezek None-ok
        try:
            if stream is not None:
                stream.flush()
        except Exception:
            pass
    os._exit(0)
