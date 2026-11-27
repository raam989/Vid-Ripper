"""A Vid-Ripper angol (EN) és német (DE) szövegei.

A kulcs a magyar szöveg, pontosan úgy, ahogy a PHDL.py-ban a t("...") hívásban szerepel. Ha
egy szöveg hiányzik, az app a magyart mutatja. A kapcsos zárójeles részeket ({n}, {name})
a program tölti ki, ezeket a fordításban is meg kell hagyni.
"""

EN = {
    'Bugfixek, finomhangolások':
        'Bug fixes and refinements',
    'ÁLTALÁNOS':
        'GENERAL',
    'LETÖLTÉS':
        'DOWNLOADS',
    'LEJÁTSZÁS':
        'PLAYBACK',
    'ELŐZMÉNYEK':
        'HISTORY',
    'KARBANTARTÁS':
        'MAINTENANCE',
    'A letöltések végén az app egy kis értesítést mutat a sarokban, és hangjelzést ad. Ezeket külön kapcsolhatod, és azt is beállíthatod, hogyan jelenjen meg az értesítés.':
        'When downloads finish, the app shows a small notification in the corner and plays a sound. You can switch these separately and choose how the notification appears.',
    'Videó- és zeneletöltő Macre, Windowsra és Linuxra. Bemásolod a linket, a többit az app intézi.':
        'A video and music downloader for Mac, Windows and Linux. Paste the link, the app does the rest.',
    'Letöltés YouTube-ról és több száz más oldalról, akár 4K-ban és HDR-ben':
        'Downloads from YouTube and hundreds of other sites, up to 4K and HDR',
    'Zene mentése mp3-ba, választható minőségben':
        'Save music as mp3 in the quality you choose',
    'Lejátszási listák és teljes csatornák letöltése, a kívánt videók kiválasztásával':
        'Download playlists and whole channels, picking the videos you want',
    'Élő adások felvétele, akár az adás elejétől':
        'Record live streams, even from the beginning',
    'Egy videónak csak a kiválasztott része is letölthető':
        'Download just a selected part of a video',
    'Szponzorált részek kivágása YouTube videókból (SponsorBlock)':
        'Cut sponsored segments from YouTube videos (SponsorBlock)',
    'Borítókép, cím és fejezetek a letöltött fájlokban':
        'Cover image, title and chapters in the downloaded files',
    'Egyszerre több letöltés, várakozási sorral':
        'Several downloads at once, with a queue',
    'Kereshető, rendezhető előzmények, jelszavas védelemmel':
        'Searchable, sortable history with password protection',
    'Figyelmeztetés a már letöltött linkekre':
        "Warning for links you've already downloaded",
    'Kíméletes letöltés NAS-ra':
        'Gentle downloading to a NAS',
    'Gyors keresés egy billentyűparanccsal':
        'Quick search with a keyboard shortcut',
    'Négy téma, sötét és világos módban':
        'Four themes, in dark and light mode',
    'Magyar, angol és német nyelv':
        'Hungarian, English and German',
    'Beépített yt-dlp frissítés':
        'Built-in yt-dlp updates',
    'Új Névjegy: rövid bemutatás és a funkciók listája':
        'New About window: a short introduction and the list of features',
    'Adatok beégetése a fájlba':
        'Embed details in the file',
    'A letöltött fájlba belekerül a borítókép, a cím, az előadó vagy a feltöltő, videónál a fejezetek is. Így a zenelejátszók és a médiaszerverek (például Plex, Jellyfin) szépen megjelenítik.':
        'The downloaded file gets the cover image, title, artist or uploader, and for videos the chapters too. Music players and media servers (such as Plex or Jellyfin) then show them nicely.',
    'SponsorBlock':
        'SponsorBlock',
    'A SponsorBlock a nézők által jelölt részeket ismeri YouTube videókban, például a szponzorált részeket vagy a bevezetőket. Ha egy videóban vannak ilyenek, a letöltő oldalon egy pipával kérheted, hogy az app kivágja vagy fejezetként jelölje őket. Itt állíthatod be, mi történjen, és mely részekkel. Áttűnéssel a vágás helyén egy rövid elsötétülés és felirat jelzi, hogy kimaradt valami. Ez lassabb, mert az egész videót újra kell kódolni.':
        'SponsorBlock knows the parts of YouTube videos that viewers have marked, such as sponsored segments or intros. If a video has any, you can tick a box on the download page to have the app cut them out or mark them as chapters. Here you choose what happens and to which parts. With the fade, a short fade to black and a caption show where something was cut. This is slower, because the whole video has to be re-encoded.',
    '{n} mp':
        '{n} s',
    'Jelölt részek kivágása':
        'Cut out marked parts',
    'Jelölt részek fejezetként':
        'Marked parts as chapters',
    '{n} rész, összesen {total}: {cats}':
        'Parts: {n}, {total} in total: {cats}',
    'Szponzor':
        'Sponsor',
    'Saját reklám':
        'Self-promotion',
    'Feliratkozás, like kérése':
        'Subscribe and like reminders',
    'Bevezető':
        'Intro',
    'Zárás, stáblista':
        'Outro, credits',
    'Előzetes, összefoglaló':
        'Preview, recap',
    'Mellékszál, töltelék':
        'Tangent, filler',
    'Nem zenei rész klipben':
        'Non-music part',
    'Fejezetként jelölés':
        'Mark as chapters',
    'Borítókép, cím és előadó kerül a letöltött fájlokba, videónál a fejezetek is (Beállítások)':
        'Cover image, title and artist are embedded in downloaded files, chapters too for videos (Settings)',
    'SponsorBlock: YouTube videókban a szponzorált részeket és hasonlókat kivághatod vagy fejezetként jelölheted':
        'SponsorBlock: cut out or mark as chapters the sponsored and similar parts of YouTube videos',
    'Linkeket az ablakba húzva is elindíthatod a letöltést':
        'You can also start a download by dragging links into the window',
    'Ha új yt-dlp érhető el, a letöltő oldalon piros sáv jelzi':
        'When a new yt-dlp is available, a red bar shows it on the download page',
    'Az FB-R téma megszűnt, helyette a VD-R lett beállítva':
        'The FB-R theme was removed; VD-R is used instead',
    '⚠  Új yt-dlp frissítés érhető el, telepítsd a Beállításokban.':
        '⚠  A new yt-dlp update is available, install it in Settings.',
    'Várd meg, amíg az előző videó adatai megérkeznek, utána húzd be újra a linket.':
        "Wait until the previous video's details arrive, then drag the link in again.",
    'A felvétel mentése...':
        'Saving the recording...',
    'Élő adás':
        'Live stream',
    'A felvétel az adás elejétől indul, a már lement részt is letölti (a YouTube az adás első néhány óráját őrzi meg). Ez lassabb, mint az indítástól induló felvétel.':
        'The recording starts from the beginning of the stream and also downloads the part that has already aired (YouTube keeps the first few hours of a stream). This is slower than recording from now.',
    'A felvétel az indítástól tart, amíg az adás véget nem ér, vagy amíg le nem állítod.':
        'Records from when you start until the stream ends or you stop it.',
    '■  Leállítás és mentés':
        '■  Stop and save',
    'Felvétel az adás elejétől':
        'Record from the beginning',
    'Az élő felvételt előbb állítsd le a Leállítás és mentés gombbal, különben elveszik.':
        'Stop the live recording first with Stop and save, otherwise it will be lost.',
    '●  Felvétel indítása':
        '●  Start recording',
    'Típus':
        'Type',
    'Élő adás, most is megy':
        'Live stream, on air now',
    'a felvétel hosszától függ':
        'depends on the recording length',
    'Kész: {x} felvétel':
        'Done: {x} recorded',
    'az adás elejétől':
        'from the beginning',
    'ÉLŐ':
        'LIVE',
    'ma':
        'today',
    'Válassz felbontást, majd nyomd meg a Felvétel indítása gombot.':
        'Choose a resolution, then press Start recording.',
    '● Felvétel: {elapsed}':
        '● Recording: {elapsed}',
    'Az élő adás még nem kezdődött el. Próbáld újra, amikor elindul.':
        "The live stream hasn't started yet. Try again when it begins.",
    'Elindult':
        'Started',
    'Élő adások felvétele: az indítástól vagy YouTube-on az adás elejétől, a Leállítás és mentés gombbal bármikor megállítható':
        'Record live streams: from now, or on YouTube from the beginning; Stop and save ends it at any time',
    'Ctrl+K':
        'Ctrl+K',
    'Az app angolul és németül is elérhető. Alapból a rendszer nyelvén indul, a Beállításokban átállítható':
        'The app is now available in English and German. It starts in the system language, and you can change it in Settings',
    'Telepítés Macen: brew install mpv':
        'Install on Mac: brew install mpv',
    'Telepítés Windowson: töltsd le az mpv.exe-t (mpv.io), és tedd az app mellé.':
        'Install on Windows: download mpv.exe (mpv.io) and put it next to the app.',
    'Telepítés: sudo apt install mpv':
        'Install: sudo apt install mpv',
    'Telepítés Macen: brew install ffmpeg':
        'Install on Mac: brew install ffmpeg',
    'Telepítés Windowson: winget install ffmpeg, vagy tedd az ffmpeg.exe és az ffprobe.exe fájlt az app mellé.':
        'Install on Windows: winget install ffmpeg, or put ffmpeg.exe and ffprobe.exe next to the app.',
    'Telepítés Linuxon: sudo apt install ffmpeg (vagy a saját csomagkezelőddel).':
        'Install on Linux: sudo apt install ffmpeg (or with your own package manager).',
    'A letöltött yt-dlp ({new_ver}) nem indult el, ezért a beépített verziót használom.':
        "The downloaded yt-dlp ({new_ver}) didn't start, so the built-in version is used.",
    'ismeretlen':
        'unknown',
    'Nincs':
        'None',
    'Csak audio (mp3)':
        'Audio only (mp3)',
    'Legjobb elérhető':
        'Best available',
    'Korlátlan':
        'Unlimited',
    "A Safari sütijeihez az appnak Teljes lemezhozzáférés kell (Rendszerbeállítások → Adatvédelem és biztonság). Egyszerűbb, ha az Beállítások fülön a 'Nincs' opciót választod.":
        "Safari cookies need Full Disk Access for the app (System Settings → Privacy & Security). It's easier to choose 'None' in Settings.",
    'Elfogyott a hely a lemezen. Szabadíts fel helyet, vagy válassz másik mappát.':
        'The disk is full. Free up some space or choose another folder.',
    'Nincs jogosultságom a kiválasztott mappába írni. Válassz másik mappát.':
        "I can't write to the selected folder. Choose another folder.",
    'Az ffmpeg hiányzik vagy nem működik. ':
        'ffmpeg is missing or not working. ',
    'Ezt a linket az yt-dlp nem ismeri fel. Ellenőrizd, hogy a videó oldalának a linkjét másoltad-e be.':
        "yt-dlp doesn't recognize this link. Check that you copied the link of the video page.",
    'Ez a felbontás ehhez a videóhoz nem érhető el. Kérd le újra a videó adatait, és válassz másikat.':
        "This resolution isn't available for this video. Get the video details again and choose another one.",
    'Az oldal túl sok kérést kapott tőlünk (429). Várj pár percet, utána próbáld újra.':
        'The site got too many requests from us (429). Wait a few minutes, then try again.',
    'Az oldal 410-es hibát adott: a videó megszűnt, vagy az oldal nem szolgálja ki az appot. Ha más videóval is ez van, nézd meg a Beállítások fülön, van-e yt-dlp frissítés.':
        "The site returned error 410: the video is gone, or the site won't serve the app. If other videos do the same, check Settings for a yt-dlp update.",
    'Az oldal elutasította a kérést (403). Lehet, hogy az oldal védelme blokkolt, vagy elavult az yt-dlp: nézd meg a Beállítások fülön, van-e frissítés.':
        'The site refused the request (403). Its protection may have blocked it, or yt-dlp is outdated: check Settings for an update.',
    'A videó nem található: lehet, hogy törölték, vagy privát lett.':
        'Video not found: it may have been deleted or made private.',
    'A videó megtekintéséhez bejelentkezés kell. A Beállítások fülön kiválaszthatod a böngészőt, amelyből az app átveszi a sütiket.':
        'You need to sign in to watch this video. In Settings you can choose a browser to take the cookies from.',
    'Az oldal szervere hibázik. Próbáld meg később.':
        "The site's server has a problem. Try again later.",
    'Nem érem el az oldalt. Ellenőrizd az internetkapcsolatot; ha az működik, lehet, hogy az oldal éppen nem válaszol.':
        "Can't reach the site. Check your internet connection; if it works, the site may not be responding right now.",
    'Ismeretlen hiba történt.':
        'An unknown error occurred.',
    " A Beállítások fülön a sütik a(z) {cookie_browser} böngészőből jönnek; próbáld meg a 'Nincs' opcióval.":
        " Cookies currently come from {cookie_browser} (Settings); try the 'None' option.",
    '{text}\n\nRészletek: {detail}':
        '{text}\n\nDetails: {detail}',
    'A PyPI nem ad letölthető csomagot ehhez a verzióhoz.':
        'PyPI has no downloadable package for this version.',
    'A letöltött fájl ellenőrző összege nem egyezik a PyPI-n megadottal, ezért nem telepítem.':
        "The checksum of the downloaded file doesn't match the one on PyPI, so it won't be installed.",
    'Érvénytelen verziószám.':
        'Invalid version number.',
    'Ez a verzió már használatban van.':
        'This version is already in use.',
    'A csomag nem tartalmazza az yt-dlp fájljait.':
        "The package doesn't contain the yt-dlp files.",
    'Gyanús fájlútvonal a csomagban.':
        'Suspicious file path in the package.',
    'A csomag verziója nem egyezik a várttal.':
        "The package version doesn't match the expected one.",
    'Névtelen videó':
        'Untitled video',
    'Angol':
        'English',
    'Francia':
        'French',
    'Magyar':
        'Hungarian',
    'Német':
        'German',
    'Spanyol':
        'Spanish',
    'Cseh':
        'Czech',
    'Holland':
        'Dutch',
    'Lengyel':
        'Polish',
    'Olasz':
        'Italian',
    'Portugál':
        'Portuguese',
    'Horvát':
        'Croatian',
    'Orosz':
        'Russian',
    'Román':
        'Romanian',
    'Szlovák':
        'Slovak',
    'Ukrán':
        'Ukrainian',
    'Dán':
        'Danish',
    'Finn':
        'Finnish',
    'Norvég':
        'Norwegian',
    'Svéd':
        'Swedish',
    'Szerb':
        'Serbian',
    'Török':
        'Turkish',
    'Arab':
        'Arabic',
    'Görög':
        'Greek',
    'Hindi':
        'Hindi',
    'Japán':
        'Japanese',
    'Koreai':
        'Korean',
    'Kínai':
        'Chinese',
    '{label} (automatikus)':
        '{label} (automatic)',
    '{label} (automatikus fordítás)':
        '{label} (auto-translated)',
    'Linuxon egyetlen fájl az egész app: kicsomagolás után dupla kattintással indul, telepítés nélkül. A lejátszó és az ffmpeg is benne van':
        'On Linux the whole app is a single file: unpack it and double-click to start, no installation. The player and ffmpeg are included',
    'Egy videónak elég csak egy részét letölteni: add meg, honnan meddig':
        'You can download just part of a video: set where it starts and ends',
    'Ha a videónak van felirata, azt is letöltheted. A felirat a videó mellé kerül, a lejátszó magától betölti':
        "If a video has subtitles, you can download them too. They're saved next to the video and the player loads them automatically",
    'Az app új neve Vid-Ripper. A beállításaid és az előzményeid megmaradtak':
        'The app is now called Vid-Ripper. Your settings and history were kept',
    'Több téma közül választhatsz, mindegyik lehet sötét, világos vagy a rendszerhez igazodó':
        'Several themes to choose from, each in dark, light or following the system',
    'Átláthatóbb Beállítások: a magyarázatok az i ikon mögött vannak':
        'Clearer Settings: explanations are behind the i icon',
    'Letöltés után kis értesítés jelenik meg a sarokban, kattintásra megmutatja a videót az Előzményekben':
        'After a download a small notification appears in the corner; click it to see the video in History',
    'Gyors keresés: Cmd+K (Windowson és Linuxon Ctrl+K), oldalak, beállítások és előzmények egy helyen':
        'Quick search: Cmd+K (Ctrl+K on Windows and Linux), pages, settings and history in one place',
    'Új felület oldalsávval, a letöltő tetején a Videó kiválasztása és az Aktív letöltések':
        'New layout with a sidebar, with Choose video and Active downloads at the top of the downloader',
    'Az elkészült letöltések a listában maradnak, amíg el nem távolítod őket':
        'Finished downloads stay in the list until you remove them',
    'Az Előzményekben egyszerre több videót is kijelölhetsz és törölhetsz':
        'In History you can select and delete several videos at once',
    'Windowson a program mappájában csak az indítófájl látszik':
        'On Windows only the launcher is visible in the program folder',
    'Új lejátszó (mpv): akadás nélkül játszik le nagy felbontásban és teljes képernyőn is':
        'New player (mpv): smooth playback even at high resolution and in full screen',
    'A régi beépített lejátszó a Beállításokban továbbra is választható':
        'The old built-in player can still be chosen in Settings',
    'HDR letöltés, ha a videónak van HDR változata':
        'HDR download when the video has an HDR version',
    'Az app Macen, Windowson és Linuxon is fut':
        'The app runs on Mac, Windows and Linux',
    'Beépített lejátszó a letöltött videókhoz és mp3-akhoz, teljes képernyővel és kis ablakos móddal':
        'Built-in player for downloaded videos and mp3s, with full screen and a small window mode',
    'NAS-ra is kíméletesen tölt le: a félkész fájlok a gépen készülnek, a célmappába csak a kész videó kerül':
        'Gentle on NAS drives: unfinished files are made on the computer, only the finished video goes to the target folder',
    'Az Előzmények kereshető, rendezhető és szűrhető, a már letöltött linkre az app figyelmeztet':
        "History can be searched, sorted and filtered, and the app warns about links you've already downloaded",
    'Az Előzmények jelszóval zárolható':
        'History can be locked with a password',
    'Egyszerre több letöltés, lejátszási listák és csatornák letöltése, mp3 mentés':
        'Several downloads at once, playlist and channel downloads, saving as mp3',
    'Előzmények':
        'History',
    'ffmpeg (kompatibilitás)':
        'ffmpeg (compatibility)',
    'mpv (ajánlott)':
        'mpv (recommended)',
    'Dátum (újabb elöl)':
        'Date (newest first)',
    'Név (A-tól Z-ig)':
        'Name (A to Z)',
    'Méret (nagyobb elöl)':
        'Size (largest first)',
    'Csak mp3 (hang)':
        'mp3 only (audio)',
    'Csak videó':
        'Video only',
    'Minden':
        'All',
    'Várakozik':
        'Waiting',
    'Link megnyitása':
        'Opening link',
    'Formátumok beolvasása':
        'Reading formats',
    'Oldal letöltése':
        'Downloading page',
    'Bélyegkép letöltése':
        'Downloading thumbnail',
    'Adatok lekérése':
        'Getting details',
    'Kivágás':
        'Cut',
    'Másolás':
        'Copy',
    'Beillesztés':
        'Paste',
    'Összes kijelölése':
        'Select all',
    'Beúszás':
        'Slide in',
    'Áttűnés':
        'Fade',
    '↑↓ választás   Enter: megnyitás   Esc: bezárás':
        '↑↓ select   Enter: open   Esc: close',
    'Letöltő':
        'Downloader',
    'Videó kiválasztása':
        'Choose video',
    'Aktív letöltések':
        'Active downloads',
    'Oldal':
        'Page',
    'Beállítások':
        'Settings',
    'Link beillesztése a vágólapról':
        'Paste link from clipboard',
    'Művelet':
        'Action',
    'Újdonságok ebben a verzióban':
        "What's new in this version",
    'Téma':
        'Theme',
    'Téma: {label}':
        'Theme: {label}',
    'Megjelenés: Sötét':
        'Appearance: Dark',
    'Megjelenés: Világos':
        'Appearance: Light',
    'Előzmény':
        'History',
    '  Nincs találat':
        '  No results',
    'Figyelem':
        'Attention',
    'Hiba':
        'Error',
    'Letöltés kész':
        'Download complete',
    '{n_entries} videót találtam':
        'Found {n_entries} videos',
    ' (az első {playlist_max}-ra korlátoztam)':
        ' (limited to the first {playlist_max})',
    '. Pipáld ki, amit le szeretnél tölteni.':
        '. Tick the ones you want to download.',
    'Mind':
        'All',
    'Egyik sem':
        'None',
    'Minőség':
        'Quality',
    'Sorba állítás':
        'Add to queue',
    'Mégse':
        'Cancel',
    '{n} kijelölve':
        '{n} selected',
    '{app} névjegye':
        'About {app}',
    'Alkalmazás verziója':
        'App version',
    'yt-dlp verziója':
        'yt-dlp version',
    'Újdonságok':
        "What's new",
    'Jelenlegi verzió: v.{app_version}':
        'Current version: v.{app_version}',
    'Korábbi, 1.0 előtti verziók':
        'Earlier versions, before 1.0',
    '   jelenlegi':
        '   current',
    'A hang nem elérhető':
        'Sound not available',
    '  (normál)':
        '  (normal)',
    '{x}{x2} mp':
        '{x}{x2} s',
    'Az mpv lejátszó nem indult el rendesen (hibakód: {code}).\nHa a fájl más programban lejátszható, nézd meg, hogy az mpv teljes és friss-e.\n':
        "The mpv player didn't start properly (error code: {code}).\nIf the file plays in other programs, check that mpv is complete and up to date.\n",
    'Windowson ehhez a videókártya friss illesztőprogramja is kell.':
        'On Windows this also needs an up-to-date graphics driver.',
    'Igen':
        'Yes',
    'Nem':
        'No',
    'Az előzmények zárolva vannak':
        'History is locked',
    'Add meg a jelszót a megtekintésükhöz.':
        'Enter the password to view it.',
    'Feloldás':
        'Unlock',
    'Elfelejtett jelszó':
        'Forgot password',
    'Túl sok hibás próba. Próbáld újra {wait} mp múlva.':
        'Too many wrong attempts. Try again in {wait} s.',
    'Hibás jelszó. {lock_wait_seconds} mp várakozás következik.':
        'Wrong password. Please wait {lock_wait_seconds} s.',
    'Hibás jelszó.':
        'Wrong password.',
    'A jelszó visszaállításával az összes előzmény és a hozzájuk tartozó bélyegképek véglegesen törlődnek, és a jelszavas védelem kikapcsol.\n\nFolytatod?':
        'Resetting the password permanently deletes the whole history with its thumbnails, and turns off password protection.\n\nContinue?',
    'Törlés és visszaállítás':
        'Delete and reset',
    'A jelszó legalább {lock_min_len} karakter legyen.':
        'The password must be at least {lock_min_len} characters.',
    'A két jelszó nem egyezik.':
        "The two passwords don't match.",
    'Jelszó beállítása':
        'Set password',
    'Ezzel zárolhatod az előzményeket. Ha elfelejted, csak az előzmények törlésével lehet visszaállítani.':
        'This locks your history. If you forget the password, it can only be reset by deleting the history.',
    'Beállítás':
        'Set',
    'Jelszó újra':
        'Repeat password',
    'Új jelszó':
        'New password',
    'Az új jelszó legalább {lock_min_len} karakter legyen.':
        'The new password must be at least {lock_min_len} characters.',
    'A két új jelszó nem egyezik.':
        "The two new passwords don't match.",
    'Jelszó módosítása':
        'Change password',
    'Jelenlegi jelszó':
        'Current password',
    'Módosítás':
        'Change',
    'Új jelszó újra':
        'Repeat new password',
    'Védelem kikapcsolása':
        'Turn off protection',
    'A jelszó megadása után az előzmények újra jelszó nélkül elérhetők.':
        'After entering the password, history will be accessible without a password again.',
    'Jelszó':
        'Password',
    'Kikapcsolás':
        'Turn off',
    'Előzmények védelme':
        'History protection',
    'Nincs bekapcsolva':
        'Not turned on',
    'Jelszó beállítása…':
        'Set password…',
    'Be van kapcsolva':
        'Turned on',
    'Zárolás most':
        'Lock now',
    'Jelszó módosítása…':
        'Change password…',
    'Kikapcsolás…':
        'Turn off…',
    'Nézet':
        'View',
    'Keresés':
        'Search',
    'Szöveg törlése':
        'Clear text',
    'Feltöltő, cím, dátum vagy weboldal neve (több szó is lehet).':
        'Uploader, title, date or website name (several words allowed).',
    'Összes előzmény törlése':
        'Clear all history',
    'Még nincs letöltés':
        'No downloads yet',
    'Az elkészült letöltéseid itt jelennek meg.':
        'Your finished downloads will appear here.',
    'Lejátszás (alap)':
        'Play (default)',
    'Letöltve':
        'Downloaded',
    'Méret':
        'Size',
    '{n__hist_view} találat ({n_history} bejegyzésből)':
        '{n__hist_view} results (of {n_history} entries)',
    'Az előzmények ki vannak kapcsolva':
        'History is turned off',
    'a {extra} legrégebbi bejegyzés':
        'the {extra} oldest entries',
    'az összes bejegyzés':
        'all entries',
    'Előzmények méretének csökkentése':
        'Reduce history size',
    'A kisebb méret miatt {what} törlődik az előzményekből.\n\nA letöltött fájlok a lemezen megmaradnak.':
        'Because of the smaller size, {what} will be removed from history.\n\nThe downloaded files stay on disk.',
    'Törlés':
        'Delete',
    'Nincs találat':
        'No results',
    'Próbálj másik kifejezést vagy szűrést.':
        'Try another search term or filter.',
    'Próbálj másik kifejezést.':
        'Try another search term.',
    'A Beállításokban bekapcsolhatod.':
        'You can turn it on in Settings.',
    'Rendezés':
        'Sort',
    'Szűrés típus szerint':
        'Filter by type',
    'A fájl már nem található, ezért a mappáját nyitottam meg.\n\n{x}':
        'The file no longer exists, so its folder was opened.\n\n{x}',
    'Nem találom a fájlt és a mappáját sem ezen az útvonalon:\n\n{x}':
        "Can't find the file or its folder at this path:\n\n{x}",
    'A fájl már nem található ezen az útvonalon:\n\n{x}':
        'The file no longer exists at this path:\n\n{x}',
    'Lejátszás ({name})':
        'Play ({name})',
    'Nem sikerült megnyitni a fájlt az alapértelmezett programmal.':
        "Couldn't open the file with the default program.",
    'A beépített lejátszóhoz ffmpeg kell, de nincs telepítve.\n':
        "The built-in player needs ffmpeg, but it isn't installed.\n",
    '\n\nVálthatsz az mpv lejátszóra a Beállításokban, vagy használhatod az "Alap lejátszóval" gombot.':
        '\n\nYou can switch to the mpv player in Settings, or use the "Play (default)" button.',
    'Ezt a fájlt a beépített lejátszó nem tudja lejátszani (nincs benne kép vagy hang, vagy nem olvasható).\nPróbáld az "Alap lejátszóval" gombot.':
        'The built-in player can\'t play this file (it has no picture or sound, or can\'t be read).\nTry the "Play (default)" button.',
    'A hang lejátszásához a sounddevice csomag kell, de nem érhető el.\nTelepítés: pip3 install sounddevice\n\nAddig használhatod az "Alap lejátszóval" gombot.':
        'Playing sound needs the sounddevice package, but it isn\'t available.\nInstall: pip3 install sounddevice\n\nUntil then you can use the "Play (default)" button.',
    'A lejátszóhoz az mpv kell, de nincs telepítve.\n':
        "The player needs mpv, but it isn't installed.\n",
    '\n\nVálthatsz a beépített lejátszóra a Beállításokban, vagy használhatod az "Alap lejátszóval" gombot.':
        '\n\nYou can switch to the built-in player in Settings, or use the "Play (default)" button.',
    'Nem sikerült elindítani az mpv lejátszót.':
        "Couldn't start the mpv player.",
    'Biztosan törlöd ezt a bejegyzést az előzményekből?\n\n{x}\n\nA fájl a lemezen megmarad.':
        'Remove this entry from history?\n\n{x}\n\nThe file stays on disk.',
    '\n... és még {x}':
        '\n... and {x} more',
    'Biztosan törlöd a kijelölt {n_indices} bejegyzést az előzményekből?\n\n{names}{more}\n\nA fájlok a lemezen megmaradnak.':
        'Remove the {n_indices} selected entries from history?\n\n{names}{more}\n\nThe files stay on disk.',
    'Törlés az előzményből':
        'Remove from history',
    'Biztosan törlöd az összes előzményt ({n_history} bejegyzés)?\n\nA letöltött fájlok a lemezen megmaradnak.':
        'Clear the whole history ({n_history} entries)?\n\nThe downloaded files stay on disk.',
    'nincs mentve':
        'not saved',
    'Animáció: {x}':
        'Animation: {x}',
    'Így jelenik meg az értesítés':
        'This is how notifications look',
    'Minta':
        'Preview',
    'Alapértelmezett (a rendszer ideiglenes mappája)':
        "Default (the system's temporary folder)",
    '\nSzabad hely: {x}':
        '\nFree space: {x}',
    '\nA mappa most nem érhető el, addig az alapértelmezett lesz használva.':
        "\nThe folder isn't available right now, the default is used until then.",
    'Ideiglenes fájlok mappája':
        'Temporary files folder',
    'Ebbe a mappába nem lehet írni.':
        "This folder isn't writable.",
    'Nyelv, megjelenés, értesítések, letöltés, előzmények és védelem':
        'Language, appearance, notifications, downloads, history and protection',
    'Nyelv':
        'Language',
    'Az alkalmazás nyelve. Automatikus beállításnál a rendszer nyelvét követi, ha az magyar, angol vagy német, egyébként angol. A váltás az app újraindítása után lép életbe.':
        "The language of the app. Automatic follows the system language if it's Hungarian, English or German, otherwise English. The change takes effect after restarting the app.",
    'Automatikus (a rendszer nyelve)':
        'Automatic (system language)',
    'Az alkalmazás témájának kiválasztása.':
        "Choose the app's theme.",
    'Rendszer':
        'System',
    'Sötét':
        'Dark',
    'Világos':
        'Light',
    'Értesítések':
        'Notifications',
    'Értesítések a letöltések végén':
        'Notify when downloads finish',
    'Hangjelzés a letöltések végén':
        'Sound when downloads finish',
    'Be':
        'On',
    'Ki':
        'Off',
    'Értesítések animációja':
        'Notification animation',
    'Ideiglenes fájlok helye':
        'Temporary files location',
    'Az alkalmazás letöltés közben ideiglenes fájlokkal dolgozik. Ez néha gondot jelenthet, ha közvetlenül NAS gépre töltesz le, például a NAS logja megtelik a letöltött videók bejegyzéseivel. Ennél a beállításnál kijelölhetsz egy mappát, ahova az ideiglenes fájlok kerülnek, így a célmappába csak a kész videó lesz átmásolva. Az ideiglenes fájlok automatikusan törlődnek a videó sikeres letöltése és megszakítás után.':
        'While downloading, the app works with temporary files. This can be a problem if you download straight to a NAS, for example its log fills up with entries about the downloads. Here you can choose a folder for the temporary files, so only the finished video is copied to the target folder. Temporary files are deleted automatically after a successful download or a cancel.',
    'Célmappában':
        'In the target folder',
    'Ideiglenes mappában':
        'In a temporary folder',
    'Mappa…':
        'Folder…',
    'Alap':
        'Default',
    'Előzmények mérete':
        'History size',
    'Itt az előzmények listában szereplő bejegyzések mennyiségét állíthatod be. Ha a lista megtelt, az utolsó bejegyzés automatikusan eltűnik a listából. Ha nagyobb értékről kisebbre állítod, szintén eltűnnek a régebbi bejegyzések.':
        'Set how many entries the history list keeps. When the list is full, the oldest entry disappears automatically. If you lower the value, older entries are removed too.',
    'Beépített lejátszó':
        'Built-in player',
    'Az mpv egy modernebb lejátszóval indítja a letöltött videókat. Támogatja a HDR formátumokat, 4K és 60 fps videók esetén is megfelelő teljesítményt nyújt, és több beállítási lehetősége van (jobb klikk a videón). Az ffmpeg egy egyszerűbb beépített lejátszó, kevesebb funkcióval és kevésbé jó teljesítménnyel, főleg régebbi gépekhez ajánlott.':
        'mpv opens your downloaded videos in a more modern player. It supports HDR, runs well even with 4K and 60 fps videos, and has more options (right-click the video). ffmpeg is a simpler built-in player with fewer features and lower performance, mainly for older computers.',
    'Böngésző sütik használata':
        'Use browser cookies',
    'Ezt alapból hagyd a „Nincs” lehetőségen. Csak akkor válts, ha egy oldal bejelentkezést vagy sütit kér a tartalmak megjelenítéséhez.':
        'Leave this on “None” by default. Only change it if a site asks you to sign in or needs cookies to show its content.',
    'yt-dlp frissítése':
        'Update yt-dlp',
    'Ahhoz, hogy a letöltő megfelelően működjön, időnként frissíteni szükséges a yt-dlp plugint.':
        'For the downloader to keep working, yt-dlp needs an update from time to time.',
    'Telepített verzió: {ytdlp_version}':
        'Installed version: {ytdlp_version}',
    'Frissítés keresése':
        'Check for updates',
    'Frissítés letöltése':
        'Download update',
    'Visszamenőleges verziótörténet az utókor számára.':
        'The full version history, for posterity.',
    'Verziótörténet':
        'Version history',
    'Névjegy':
        'About',
    '(letöltve, újraindítás után lép életbe)':
        '(downloaded, takes effect after restart)',
    '(frissítés érhető el)':
        '(update available)',
    'Frissítés keresése...':
        'Checking for updates...',
    'Nem sikerült megnézni az új verziót. Van internet?':
        "Couldn't check for a new version. Are you online?",
    'Az yt-dlp naprakész.':
        'yt-dlp is up to date.',
    'Az új verzió már le van töltve, indítsd újra az appot, hogy életbe lépjen.':
        'The new version is already downloaded, restart the app to use it.',
    'Új verzió érhető el: {latest_ytdlp}':
        'New version available: {latest_ytdlp}',
    'Letöltés indul...':
        'Starting download...',
    'Letöltés...':
        'Downloading...',
    'Letöltés: {pct}%':
        'Downloading: {pct}%',
    'Ellenőrzés és telepítés...':
        'Checking and installing...',
    'A frissítés nem sikerült.':
        'The update failed.',
    'Az yt-dlp frissítése nem sikerült.\n\n':
        'Updating yt-dlp failed.\n\n',
    'Kész: a(z) {version} verzió letöltve. Indítsd újra az appot, hogy életbe lépjen.':
        'Done: version {version} downloaded. Restart the app to use it.',
    'Másold be a videó linkjét, vagy több linket soronként.':
        'Paste a video link, or several links, one per line.',
    'Videó linkje':
        'Video link',
    'Videó adatai':
        'Video details',
    'Felbontás':
        'Resolution',
    'Előbb kérd le a videó adatait.':
        'Get the video details first.',
    'letöltés HDR minőségben':
        'download in HDR quality',
    'Hangminőség':
        'Audio quality',
    'Letöltendő rész':
        'Part to download',
    'Teljes videó':
        'Whole video',
    'Kijelölt rész':
        'Selected part',
    'Kezdete':
        'Start',
    'Vége':
        'End',
    'Feliratok letöltése':
        'Download subtitles',
    'Letöltési mappa':
        'Download folder',
    'Tallózás…':
        'Browse…',
    'Megszakítás':
        'Cancel',
    '↓  Letöltés':
        '↓  Download',
    'Mentés ezen a néven':
        'Save as',
    'Válassz felbontást, majd nyomd meg a Letöltés gombot.':
        'Choose a resolution, then press Download.',
    'Az időpontot így add meg: 1:30 vagy 1:02:30.':
        'Enter the time like this: 1:30 or 1:02:30.',
    'A vége legyen később, mint a kezdete.':
        'The end must be later than the start.',
    'A videó csak {x} hosszú.':
        'The video is only {x} long.',
    '{x} hosszú rész':
        '{x} long part',
    'Csak hang':
        'Audio only',
    'Más ▾':
        'More ▾',
    'Feltöltő':
        'Uploader',
    'Hossz':
        'Length',
    '{x}-tól {x2}-ig':
        '{x} to {x2}',
    'Becsült méret':
        'Estimated size',
    'Mentés ezen a néven: {name}\nVálassz felbontást, majd nyomd meg a Letöltés gombot.':
        'Save as: {name}\nChoose a resolution, then press Download.',
    'Ezt már letöltötted':
        'Already downloaded',
    'Ezt a linket már letöltötted ({when}):\n\n{x}\n\nLetöltöd még egyszer?':
        'You already downloaded this link ({when}):\n\n{x}\n\nDownload it again?',
    'Letöltöm újra':
        'Download again',
    'Mégsem':
        'Cancel',
    'A kiválasztott mappa nem létezik.':
        "The selected folder doesn't exist.",
    'Ezeket már letöltötted':
        'Already downloaded',
    'Igen, újra is':
        'Yes, those too',
    'Kihagyom őket':
        'Skip them',
    '{n_dups} linket korábban már letöltöttél (a {n_links} közül).\n\nLetöltöd ezeket is újra?':
        'Links downloaded before: {n_dups} of {n_links}.\n\nDownload these again too?',
    'Minden link már le volt töltve.':
        'All links were already downloaded.',
    '{n_entries} link beillesztve.':
        'Links pasted: {n_entries}.',
    'Beillesztett linkek':
        'Pasted links',
    'A linkek letöltését elvetted.':
        'You dismissed downloading the links.',
    'Előbb másold be a videó linkjét.':
        'Paste the video link first.',
    'Videó keresése az oldalon':
        'Looking for the video on the page',
    'Indul':
        'Starting',
    'Videó adatainak lekérése: {x}%  ({fetch_stage}, {secs} mp)':
        'Getting video details: {x}%  ({fetch_stage}, {secs} s)',
    'Nem találtam elérhető felbontást ehhez a linkhez.':
        "Couldn't find an available resolution for this link.",
    'Nem találtam letölthető videót ezen a linken.':
        "Couldn't find a downloadable video at this link.",
    'Lejátszási lista: {n_entries} videó.':
        'Playlist: {n_entries} videos.',
    'Lejátszási lista':
        'Playlist',
    'A lejátszási lista letöltését elvetted.':
        'You dismissed downloading the playlist.',
    'Az mp3 készítéséhez ffmpeg kell, de nincs telepítve.\n':
        "Making an mp3 needs ffmpeg, but it isn't installed.\n",
    '{added} videót tettem a sorba, a többi már szerepelt a listában, vagy betelt a sor.':
        'Videos added to the queue: {added}. The rest were already in the list, or the queue is full.',
    'Adatok lekérése...':
        'Getting details...',
    'Nem sikerült lekérni a videó adatait.':
        "Couldn't get the video details.",
    'A videó adatainak lekérése nem sikerült.':
        'Getting the video details failed.',
    'Újrapróbálkozás':
        'Retry',
    '{headline}\n\n{text}\n\nÚjrapróbáljam?':
        '{headline}\n\n{text}\n\nTry again?',
    'lassú vagy megszakadt az internet':
        'the internet is slow or disconnected',
    'az oldal nem válaszol':
        "the site isn't responding",
    'elavult az yt-dlp (a Beállítások fülön van frissítés keresés)':
        'yt-dlp is outdated (check for an update in Settings)',
    'a(z) {x} sütijeinek beolvasása várhat egy rendszerablakra (például jelszókérésre)':
        'reading the {x} cookies may be waiting for a system dialog (for example a password prompt)',
    'Az adatlekérés már több mint {fetch_stall_seconds:g} másodperce tart, valami akadozik.\n\nLehetséges okok:\n':
        'Getting the details has taken more than {fetch_stall_seconds:g} seconds, something is stuck.\n\nPossible causes:\n',
    '\n\nMegszakítsam, és újrapróbáljam?':
        '\n\nCancel and try again?',
    'A lekérés elakadt':
        'Getting details is stuck',
    'Az adatok lekérését megszakítottam.':
        'Getting the details was cancelled.',
    'A link megváltozott, kérd le újra a videó adatait.':
        'The link changed, get the video details again.',
    'Legfeljebb {max_jobs} letöltés lehet a listában. Várd meg, amíg néhány elkészül.':
        'The list can hold at most {max_jobs} downloads. Wait until some are finished.',
    'Ez a videó ebben a minőségben már szerepel a letöltések között.':
        'This video is already among the downloads in this quality.',
    'Az ffmpeg nincs telepítve, ezért nem biztos, hogy mp4 lesz belőle.\n':
        "ffmpeg isn't installed, so the result may not be an mp4.\n",
    'Indul...':
        'Starting...',
    'még {x} mp':
        '{x} s left',
    'mp3 átalakítás':
        'converting to mp3',
    'mp4 összefűzés':
        'merging mp4',
    'Feldolgozás ({what})...':
        'Processing ({what})...',
    'Kész, de a felirat nem jött le':
        "Done, but the subtitles didn't download",
    'Kész':
        'Done',
    'Megszakítva':
        'Cancelled',
    'Nem sikerült a letöltés':
        'Download failed',
    'Legfeljebb {max_jobs} letöltés lehet a sorban. Várd meg, amíg néhány elkészül.':
        'The queue can hold at most {max_jobs} downloads. Wait until some are finished.',
    '{name}\n\nMappa: {folder}':
        '{name}\n\nFolder: {folder}',
    'Kész, a hangfájl a kiválasztott mappába került.':
        'Done, the audio file is in the selected folder.',
    'Kész, a videó a kiválasztott mappába került.':
        'Done, the video is in the selected folder.',
    '\n… és még {x}':
        '\n… and {x} more',
    'Mind a(z) {n_ok} letöltés elkészült.\n\n{names}':
        'All downloads finished ({n_ok}).\n\n{names}',
    '\n\n{failed} letöltés nem sikerült.':
        '\n\nFailed downloads: {failed}.',
    'Kész, {n_ok} letöltés elkészült.':
        'Done, downloads finished: {n_ok}.',
    'Kész a letöltés':
        'Download complete',
    '{n_ok} letöltés elkészült':
        'Downloads finished: {n_ok}',
    'és még {x} videó':
        'and {x} more videos',
    ', {failed} nem sikerült':
        ', failed: {failed}',
    'Megszakítás...':
        'Cancelling...',
    'Készek eltávolítása':
        'Remove finished',
    'Egyszerre legfeljebb {max_parallel} letöltés fut, a többi sorban vár.':
        'Up to {max_parallel} downloads run at once, the rest wait in the queue.',
    'Újrapróbálás':
        'Retry',
    'Eltávolítás':
        'Remove',
    'néhány oldal nem fog működni, mert a curl_cffi csomag hiányzik':
        "some sites won't work because the curl_cffi package is missing",
    'a bélyegképek nem látszanak, mert a pillow csomag hiányzik':
        "thumbnails won't show because the pillow package is missing",
    '\nFigyelem: ':
        '\nNote: ',
    'Az új nyelv az app újraindítása után lép életbe.':
        'The new language takes effect after restarting the app.',
    'Később':
        'Later',
    'Újraindítás most':
        'Restart now',
    'Kilépés':
        'Quit',
    'Még {n_running} letöltés fut vagy vár. Ha kilépsz, ezek megszakadnak.\n\nBiztosan kilépsz?':
        'Downloads still running or waiting: {n_running}. If you quit, they will be cancelled.\n\nQuit anyway?',
    'KÖNYVTÁR':
        'LIBRARY',
    '♥  Ko-fi támogatás':
        '♥  Support on Ko-fi',
    '●  Újdonságok ebben a verzióban':
        "●  What's new in this version",
    'január':
        'January',
    'február':
        'February',
    'március':
        'March',
    'április':
        'April',
    'május':
        'May',
    'június':
        'June',
    'július':
        'July',
    'augusztus':
        'August',
    'szeptember':
        'September',
    'október':
        'October',
    'november':
        'November',
    'december':
        'December',
    "Az Újdonságok ablak mindig előre nyílik, és simább lett a görgetés.": "The What's new window now always opens in front, and scrolling is smoother.",
    'Kivágás áttűnéssel':
        'Cut with fade',
    'Kivágott szponzor tartalom':
        'Sponsored content removed',
    'Kivágott rész: {x}':
        'Removed: {x}',
    'Kivágott rész':
        'Part removed',
    'Áttűnések készítése: {pct}%':
        'Adding fades: {pct}%',
    'SponsorBlock: kivágás áttűnéssel is, így a vágás helyén egy rövid elsötétülés és felirat jelzi, hogy kimaradt valami.':
        'SponsorBlock: cutting with a fade too, so a short fade to black and a caption show where something was removed.',
    'Kijelölt rész: {pct}%  ({done} / {total})':
        'Selected part: {pct}%  ({done} / {total})',
    'Kijelölt rész előkészítése... {secs} mp':
        'Preparing the selected part... {secs} s',
    'Kijelölt rész letöltése: gyorsabb, látszik a haladás, és a megszakítás is működik.':
        'Downloading a selected part: faster, shows progress, and cancelling works.',
    'Kilépéskor nem jön hibaablak Windowson.':
        'No more error window when quitting on Windows.',
    'Kész, áttűnés nélkül (sima vágás)':
        'Done, without the fade (plain cut)',
    'SponsorBlock hibajavítások':
        'SponsorBlock bug fixes',
    'Hibajavítások és dupla kattintásos műveletek hozzáadása':
        'Bug fixes and new double-click actions',
    'Sebességkorlát: {x} MB/s':
        'Speed limit: {x} MB/s',
    'Sebességkorlát: ki':
        'Speed limit: off',
    'Sebességkorlát':
        'Speed limit',
    'Ha bekapcsolod, a letöltések együtt legfeljebb ennyi sebességgel töltenek, így a többi gép és alkalmazás is kényelmesen használhatja az internetet. Futó letöltésre is azonnal hat. Gyorsan ki- és bekapcsolhatod az Előzmények oldalon is.':
        'When on, all downloads together stay below this speed, so other devices and apps can still use the internet comfortably. It takes effect right away, even for running downloads. You can also switch it on and off quickly on the History page.',
    'Egyéni':
        'Custom',
    'Egyéni…':
        'Custom…',
    'Egyéni érték:':
        'Custom value:',
    'letöltés':
        'downloads',
    '{a} és {b} MB/s közötti számot adj meg.':
        'Enter a number between {a} and {b} MB/s.',
    '1 és {b} közötti egész számot adj meg.':
        'Enter a whole number between 1 and {b}.',
    'Egyszerre futó letöltések':
        'Simultaneous downloads',
    'Minden letöltés egyszerre fut, nincs várakozó sor.':
        'All downloads run at once, nothing waits in a queue.',
    'Ennyi letöltés fut egyszerre, a többi sorban vár, és akkor indul, amikor egy elkészül. Több egyszerre futó letöltés nem mindig gyorsabb, mert osztoznak az interneten. Korlátlannál minden letöltés azonnal indul.':
        "This many downloads run at once, the rest wait in the queue and start when one finishes. More simultaneous downloads aren't always faster, because they share the internet connection. With Unlimited, every download starts right away.",
    'Finomhangolások, az app ikonjának téma szerinti változtatása és letöltési limitek testreszabhatósága.':
        'Fine-tuning, an app icon that changes with the theme, and customizable download limits.',
    'A fájl nem található':
        'File not found',
    'A fájl nem található ezen az útvonalon.':
        "The file can't be found at this path.",
    'Eredeti link':
        'Original link',
    'FOLYAMATBAN':
        'IN PROGRESS',
    'Fájl':
        'File',
    'Hozzáadva. Most {active} fut, {waiting} vár. Az Előzmények oldalon látod az állapotukat.':
        'Added. Running: {active}, waiting: {waiting}. You can follow them on the History page.',
    'KORÁBBAN':
        'EARLIER',
    'Kattints a kártyákra a kijelöléshez':
        'Click the cards to select them',
    'Kijelölés':
        'Select',
    'LETÖLTVE':
        'DOWNLOADED',
    'LETÖLTVE · {x}':
        'DOWNLOADED · {x}',
    'MA':
        'TODAY',
    'Mappa':
        'Folder',
    'Mind kijelölése':
        'Select all',
    'TEGNAP':
        'YESTERDAY',
    'Továbbiak ({n} még)':
        'Show more ({n} left)',
    'Törlés ({n})':
        'Delete ({n})',
    '{a} letöltés fut':
        '{a} downloading',
    '{a} letöltés fut, {w} vár':
        '{a} downloading, {w} waiting',
    '{n} videó kijelölve':
        '{n} selected',
    '{n} videó letöltve':
        '{n} videos downloaded',
    '▶  Lejátszás':
        '▶  Play',
    '✓  Letöltve':
        '✓  Downloaded',
    'Jelszóval elrejtheted az Előzmények oldalt (a futó letöltésekkel együtt) és a korábbi letöltési útvonalak listáját a kíváncsi szemek elől. Az app indítása után és {n} perc tétlenség után újra kéri a jelszót.':
        'With a password you can hide the History page (running downloads included) and the list of previous download folders from prying eyes. It asks for the password again after the app starts and after {n} minutes of inactivity.',
    'Indítás után és {n} perc tétlenség után újra jelszót kér.':
        'Asks for the password after the app starts and after {n} minutes of inactivity.',
    'Finomhangolások és megújult Előzmények oldal: a futó letöltések és a kész videók egy helyen.':
        'Fine-tuning and a redesigned History page: running downloads and finished videos in one place.',
    '●  Új':
        '●  New',
    'Hibák javítása':
        'Bug fixes',
    'Feltöltve: {x}':
        'Uploaded: {x}',
    'Hossz: {x}':
        'Length: {x}',
    'Fájlméret':
        'File size',
    'Bugfixek, előzmények oldal finomhangolása.':
        'Bug fixes, History page fine-tuning.',
    'Ablak átméretezéssel kapcsolatos hibák javítása':
        'Fixes for resizing the window',
    'Narancs':
        'Orange',
    'Piros':
        'Red',
    'Lila':
        'Purple',
    'Hibajavítások, az első nyilvános kiadás.':
        'Bug fixes, the first public release.',
}


DE = {
    'Bugfixek, finomhangolások':
        'Fehlerbehebungen und Feinschliff',
    'ÁLTALÁNOS':
        'ALLGEMEIN',
    'LETÖLTÉS':
        'DOWNLOADS',
    'LEJÁTSZÁS':
        'WIEDERGABE',
    'ELŐZMÉNYEK':
        'VERLAUF',
    'KARBANTARTÁS':
        'WARTUNG',
    'A letöltések végén az app egy kis értesítést mutat a sarokban, és hangjelzést ad. Ezeket külön kapcsolhatod, és azt is beállíthatod, hogyan jelenjen meg az értesítés.':
        'Wenn Downloads fertig sind, zeigt die App eine kleine Mitteilung in der Ecke und spielt einen Ton. Beides lässt sich einzeln schalten, und du kannst wählen, wie die Mitteilung erscheint.',
    'Videó- és zeneletöltő Macre, Windowsra és Linuxra. Bemásolod a linket, a többit az app intézi.':
        'Video- und Musik-Downloader für Mac, Windows und Linux. Link einfügen, den Rest erledigt die App.',
    'Letöltés YouTube-ról és több száz más oldalról, akár 4K-ban és HDR-ben':
        'Downloads von YouTube und Hunderten anderer Seiten, bis 4K und HDR',
    'Zene mentése mp3-ba, választható minőségben':
        'Musik als MP3 speichern, in wählbarer Qualität',
    'Lejátszási listák és teljes csatornák letöltése, a kívánt videók kiválasztásával':
        'Playlists und ganze Kanäle laden, mit Auswahl der gewünschten Videos',
    'Élő adások felvétele, akár az adás elejétől':
        'Livestreams aufnehmen, auch ab Streambeginn',
    'Egy videónak csak a kiválasztott része is letölthető':
        'Auch nur einen ausgewählten Teil eines Videos laden',
    'Szponzorált részek kivágása YouTube videókból (SponsorBlock)':
        'Sponsorenteile aus YouTube-Videos herausschneiden (SponsorBlock)',
    'Borítókép, cím és fejezetek a letöltött fájlokban':
        'Coverbild, Titel und Kapitel in den geladenen Dateien',
    'Egyszerre több letöltés, várakozási sorral':
        'Mehrere Downloads gleichzeitig, mit Warteschlange',
    'Kereshető, rendezhető előzmények, jelszavas védelemmel':
        'Durchsuch- und sortierbarer Verlauf mit Passwortschutz',
    'Figyelmeztetés a már letöltött linkekre':
        'Hinweis bei bereits geladenen Links',
    'Kíméletes letöltés NAS-ra':
        'Schonendes Laden auf ein NAS',
    'Gyors keresés egy billentyűparanccsal':
        'Schnellsuche per Tastenkürzel',
    'Négy téma, sötét és világos módban':
        'Vier Designs, im dunklen und hellen Modus',
    'Magyar, angol és német nyelv':
        'Ungarisch, Englisch und Deutsch',
    'Beépített yt-dlp frissítés':
        'Eingebaute yt-dlp-Updates',
    'Új Névjegy: rövid bemutatás és a funkciók listája':
        'Neues Info-Fenster: kurze Vorstellung und Liste der Funktionen',
    'Adatok beégetése a fájlba':
        'Daten in die Datei schreiben',
    'A letöltött fájlba belekerül a borítókép, a cím, az előadó vagy a feltöltő, videónál a fejezetek is. Így a zenelejátszók és a médiaszerverek (például Plex, Jellyfin) szépen megjelenítik.':
        'Die geladene Datei erhält Coverbild, Titel, Interpret oder Uploader, bei Videos auch die Kapitel. So zeigen Musikplayer und Medienserver (etwa Plex oder Jellyfin) sie schön an.',
    'SponsorBlock':
        'SponsorBlock',
    'A SponsorBlock a nézők által jelölt részeket ismeri YouTube videókban, például a szponzorált részeket vagy a bevezetőket. Ha egy videóban vannak ilyenek, a letöltő oldalon egy pipával kérheted, hogy az app kivágja vagy fejezetként jelölje őket. Itt állíthatod be, mi történjen, és mely részekkel. Áttűnéssel a vágás helyén egy rövid elsötétülés és felirat jelzi, hogy kimaradt valami. Ez lassabb, mert az egész videót újra kell kódolni.':
        'SponsorBlock kennt die von Zuschauern markierten Abschnitte in YouTube-Videos, etwa Sponsorenteile oder Intros. Hat ein Video solche, kannst du sie auf der Download-Seite per Häkchen herausschneiden oder als Kapitel markieren lassen. Hier legst du fest, was passiert und mit welchen Abschnitten. Mit Überblendung zeigen eine kurze Abblende und eine Einblendung, dass etwas herausgeschnitten wurde. Das dauert länger, weil das ganze Video neu kodiert wird.',
    '{n} mp':
        '{n} s',
    'Jelölt részek kivágása':
        'Markierte Teile herausschneiden',
    'Jelölt részek fejezetként':
        'Markierte Teile als Kapitel',
    '{n} rész, összesen {total}: {cats}':
        'Abschnitte: {n}, insgesamt {total}: {cats}',
    'Szponzor':
        'Sponsor',
    'Saját reklám':
        'Eigenwerbung',
    'Feliratkozás, like kérése':
        'Abo- und Like-Aufrufe',
    'Bevezető':
        'Intro',
    'Zárás, stáblista':
        'Outro, Abspann',
    'Előzetes, összefoglaló':
        'Vorschau, Rückblick',
    'Mellékszál, töltelék':
        'Abschweifung, Füllmaterial',
    'Nem zenei rész klipben':
        'Nicht-Musik-Teil',
    'Fejezetként jelölés':
        'Als Kapitel markieren',
    'Borítókép, cím és előadó kerül a letöltött fájlokba, videónál a fejezetek is (Beállítások)':
        'Coverbild, Titel und Interpret werden in die Dateien geschrieben, bei Videos auch die Kapitel (Einstellungen)',
    'SponsorBlock: YouTube videókban a szponzorált részeket és hasonlókat kivághatod vagy fejezetként jelölheted':
        'SponsorBlock: Sponsorenteile und Ähnliches in YouTube-Videos herausschneiden oder als Kapitel markieren',
    'Linkeket az ablakba húzva is elindíthatod a letöltést':
        'Downloads lassen sich auch starten, indem du Links ins Fenster ziehst',
    'Ha új yt-dlp érhető el, a letöltő oldalon piros sáv jelzi':
        'Ist ein neues yt-dlp verfügbar, zeigt das ein roter Balken auf der Download-Seite',
    'Az FB-R téma megszűnt, helyette a VD-R lett beállítva':
        'Das Design FB-R wurde entfernt, stattdessen ist VD-R eingestellt',
    '⚠  Új yt-dlp frissítés érhető el, telepítsd a Beállításokban.':
        '⚠  Ein neues yt-dlp-Update ist verfügbar, installiere es in den Einstellungen.',
    'Várd meg, amíg az előző videó adatai megérkeznek, utána húzd be újra a linket.':
        'Warte, bis die Daten des vorherigen Videos da sind, und ziehe den Link dann erneut hinein.',
    'A felvétel mentése...':
        'Aufnahme wird gespeichert...',
    'Élő adás':
        'Livestream',
    'A felvétel az adás elejétől indul, a már lement részt is letölti (a YouTube az adás első néhány óráját őrzi meg). Ez lassabb, mint az indítástól induló felvétel.':
        'Die Aufnahme beginnt am Anfang des Streams und lädt auch den bereits gesendeten Teil (YouTube speichert die ersten Stunden eines Streams). Das ist langsamer als eine Aufnahme ab jetzt.',
    'A felvétel az indítástól tart, amíg az adás véget nem ér, vagy amíg le nem állítod.':
        'Die Aufnahme läuft ab dem Start, bis der Stream endet oder du sie stoppst.',
    '■  Leállítás és mentés':
        '■  Stoppen und speichern',
    'Felvétel az adás elejétől':
        'Ab Streambeginn aufnehmen',
    'Az élő felvételt előbb állítsd le a Leállítás és mentés gombbal, különben elveszik.':
        'Stoppe die Liveaufnahme zuerst mit „Stoppen und speichern“, sonst geht sie verloren.',
    '●  Felvétel indítása':
        '●  Aufnahme starten',
    'Típus':
        'Typ',
    'Élő adás, most is megy':
        'Livestream, läuft gerade',
    'a felvétel hosszától függ':
        'hängt von der Aufnahmelänge ab',
    'Kész: {x} felvétel':
        'Fertig: {x} aufgenommen',
    'az adás elejétől':
        'ab Streambeginn',
    'ÉLŐ':
        'LIVE',
    'ma':
        'heute',
    'Válassz felbontást, majd nyomd meg a Felvétel indítása gombot.':
        'Wähle eine Auflösung und klicke dann auf „Aufnahme starten“.',
    '● Felvétel: {elapsed}':
        '● Aufnahme: {elapsed}',
    'Az élő adás még nem kezdődött el. Próbáld újra, amikor elindul.':
        'Der Livestream hat noch nicht begonnen. Versuche es erneut, wenn er startet.',
    'Elindult':
        'Gestartet',
    'Élő adások felvétele: az indítástól vagy YouTube-on az adás elejétől, a Leállítás és mentés gombbal bármikor megállítható':
        'Livestreams aufnehmen: ab jetzt oder auf YouTube ab Streambeginn; mit „Stoppen und speichern“ jederzeit beenden',
    'Ctrl+K':
        'Strg+K',
    'Az app angolul és németül is elérhető. Alapból a rendszer nyelvén indul, a Beállításokban átállítható':
        'Die App gibt es jetzt auch auf Englisch und Deutsch. Sie startet in der Systemsprache, umstellen kannst du das in den Einstellungen',
    'Telepítés Macen: brew install mpv':
        'Installation auf dem Mac: brew install mpv',
    'Telepítés Windowson: töltsd le az mpv.exe-t (mpv.io), és tedd az app mellé.':
        'Installation unter Windows: Lade mpv.exe herunter (mpv.io) und lege sie neben die App.',
    'Telepítés: sudo apt install mpv':
        'Installation: sudo apt install mpv',
    'Telepítés Macen: brew install ffmpeg':
        'Installation auf dem Mac: brew install ffmpeg',
    'Telepítés Windowson: winget install ffmpeg, vagy tedd az ffmpeg.exe és az ffprobe.exe fájlt az app mellé.':
        'Installation unter Windows: winget install ffmpeg, oder lege ffmpeg.exe und ffprobe.exe neben die App.',
    'Telepítés Linuxon: sudo apt install ffmpeg (vagy a saját csomagkezelőddel).':
        'Installation unter Linux: sudo apt install ffmpeg (oder mit deinem Paketmanager).',
    'A letöltött yt-dlp ({new_ver}) nem indult el, ezért a beépített verziót használom.':
        'Das heruntergeladene yt-dlp ({new_ver}) ließ sich nicht starten, daher wird die eingebaute Version verwendet.',
    'ismeretlen':
        'unbekannt',
    'Nincs':
        'Keine',
    'Csak audio (mp3)':
        'Nur Audio (mp3)',
    'Legjobb elérhető':
        'Beste verfügbare',
    'Korlátlan':
        'Unbegrenzt',
    "A Safari sütijeihez az appnak Teljes lemezhozzáférés kell (Rendszerbeállítások → Adatvédelem és biztonság). Egyszerűbb, ha az Beállítások fülön a 'Nincs' opciót választod.":
        'Für Safari-Cookies braucht die App Festplattenvollzugriff (Systemeinstellungen → Datenschutz & Sicherheit). Einfacher ist es, in den Einstellungen „Keine“ zu wählen.',
    'Elfogyott a hely a lemezen. Szabadíts fel helyet, vagy válassz másik mappát.':
        'Der Speicher ist voll. Gib etwas Platz frei oder wähle einen anderen Ordner.',
    'Nincs jogosultságom a kiválasztott mappába írni. Válassz másik mappát.':
        'In den gewählten Ordner kann nicht geschrieben werden. Wähle einen anderen Ordner.',
    'Az ffmpeg hiányzik vagy nem működik. ':
        'ffmpeg fehlt oder funktioniert nicht. ',
    'Ezt a linket az yt-dlp nem ismeri fel. Ellenőrizd, hogy a videó oldalának a linkjét másoltad-e be.':
        'yt-dlp erkennt diesen Link nicht. Prüfe, ob du den Link der Videoseite kopiert hast.',
    'Ez a felbontás ehhez a videóhoz nem érhető el. Kérd le újra a videó adatait, és válassz másikat.':
        'Diese Auflösung ist für dieses Video nicht verfügbar. Rufe die Videodaten erneut ab und wähle eine andere.',
    'Az oldal túl sok kérést kapott tőlünk (429). Várj pár percet, utána próbáld újra.':
        'Die Seite hat zu viele Anfragen von uns erhalten (429). Warte ein paar Minuten und versuche es dann erneut.',
    'Az oldal 410-es hibát adott: a videó megszűnt, vagy az oldal nem szolgálja ki az appot. Ha más videóval is ez van, nézd meg a Beállítások fülön, van-e yt-dlp frissítés.':
        'Die Seite meldet Fehler 410: Das Video existiert nicht mehr oder die Seite bedient die App nicht. Wenn das auch bei anderen Videos passiert, sieh in den Einstellungen nach einem yt-dlp-Update.',
    'Az oldal elutasította a kérést (403). Lehet, hogy az oldal védelme blokkolt, vagy elavult az yt-dlp: nézd meg a Beállítások fülön, van-e frissítés.':
        'Die Seite hat die Anfrage abgelehnt (403). Vielleicht hat ihr Schutz blockiert, oder yt-dlp ist veraltet: Sieh in den Einstellungen nach einem Update.',
    'A videó nem található: lehet, hogy törölték, vagy privát lett.':
        'Video nicht gefunden: Es wurde vielleicht gelöscht oder auf privat gestellt.',
    'A videó megtekintéséhez bejelentkezés kell. A Beállítások fülön kiválaszthatod a böngészőt, amelyből az app átveszi a sütiket.':
        'Für dieses Video musst du angemeldet sein. In den Einstellungen kannst du einen Browser wählen, aus dem die App die Cookies übernimmt.',
    'Az oldal szervere hibázik. Próbáld meg később.':
        'Der Server der Seite hat ein Problem. Versuche es später noch einmal.',
    'Nem érem el az oldalt. Ellenőrizd az internetkapcsolatot; ha az működik, lehet, hogy az oldal éppen nem válaszol.':
        'Die Seite ist nicht erreichbar. Prüfe die Internetverbindung; wenn sie funktioniert, antwortet die Seite gerade vielleicht nicht.',
    'Ismeretlen hiba történt.':
        'Ein unbekannter Fehler ist aufgetreten.',
    " A Beállítások fülön a sütik a(z) {cookie_browser} böngészőből jönnek; próbáld meg a 'Nincs' opcióval.":
        ' Die Cookies kommen derzeit aus {cookie_browser} (Einstellungen); versuche es mit „Keine“.',
    '{text}\n\nRészletek: {detail}':
        '{text}\n\nDetails: {detail}',
    'A PyPI nem ad letölthető csomagot ehhez a verzióhoz.':
        'PyPI bietet für diese Version kein herunterladbares Paket an.',
    'A letöltött fájl ellenőrző összege nem egyezik a PyPI-n megadottal, ezért nem telepítem.':
        'Die Prüfsumme der heruntergeladenen Datei stimmt nicht mit PyPI überein, daher wird sie nicht installiert.',
    'Érvénytelen verziószám.':
        'Ungültige Versionsnummer.',
    'Ez a verzió már használatban van.':
        'Diese Version wird bereits verwendet.',
    'A csomag nem tartalmazza az yt-dlp fájljait.':
        'Das Paket enthält keine yt-dlp-Dateien.',
    'Gyanús fájlútvonal a csomagban.':
        'Verdächtiger Dateipfad im Paket.',
    'A csomag verziója nem egyezik a várttal.':
        'Die Paketversion entspricht nicht der erwarteten.',
    'Névtelen videó':
        'Unbenanntes Video',
    'Angol':
        'Englisch',
    'Francia':
        'Französisch',
    'Magyar':
        'Ungarisch',
    'Német':
        'Deutsch',
    'Spanyol':
        'Spanisch',
    'Cseh':
        'Tschechisch',
    'Holland':
        'Niederländisch',
    'Lengyel':
        'Polnisch',
    'Olasz':
        'Italienisch',
    'Portugál':
        'Portugiesisch',
    'Horvát':
        'Kroatisch',
    'Orosz':
        'Russisch',
    'Román':
        'Rumänisch',
    'Szlovák':
        'Slowakisch',
    'Ukrán':
        'Ukrainisch',
    'Dán':
        'Dänisch',
    'Finn':
        'Finnisch',
    'Norvég':
        'Norwegisch',
    'Svéd':
        'Schwedisch',
    'Szerb':
        'Serbisch',
    'Török':
        'Türkisch',
    'Arab':
        'Arabisch',
    'Görög':
        'Griechisch',
    'Hindi':
        'Hindi',
    'Japán':
        'Japanisch',
    'Koreai':
        'Koreanisch',
    'Kínai':
        'Chinesisch',
    '{label} (automatikus)':
        '{label} (automatisch)',
    '{label} (automatikus fordítás)':
        '{label} (automatisch übersetzt)',
    'Linuxon egyetlen fájl az egész app: kicsomagolás után dupla kattintással indul, telepítés nélkül. A lejátszó és az ffmpeg is benne van':
        'Unter Linux ist die ganze App eine einzige Datei: entpacken und per Doppelklick starten, ohne Installation. Player und ffmpeg sind enthalten',
    'Egy videónak elég csak egy részét letölteni: add meg, honnan meddig':
        'Du kannst auch nur einen Teil eines Videos laden: Gib Anfang und Ende an',
    'Ha a videónak van felirata, azt is letöltheted. A felirat a videó mellé kerül, a lejátszó magától betölti':
        'Hat ein Video Untertitel, kannst du sie mitladen. Sie landen neben dem Video und der Player lädt sie automatisch',
    'Az app új neve Vid-Ripper. A beállításaid és az előzményeid megmaradtak':
        'Die App heißt jetzt Vid-Ripper. Deine Einstellungen und der Verlauf sind erhalten geblieben',
    'Több téma közül választhatsz, mindegyik lehet sötét, világos vagy a rendszerhez igazodó':
        'Mehrere Designs zur Auswahl, jeweils dunkel, hell oder passend zum System',
    'Átláthatóbb Beállítások: a magyarázatok az i ikon mögött vannak':
        'Übersichtlichere Einstellungen: Erklärungen findest du hinter dem i-Symbol',
    'Letöltés után kis értesítés jelenik meg a sarokban, kattintásra megmutatja a videót az Előzményekben':
        'Nach einem Download erscheint eine kleine Mitteilung in der Ecke; ein Klick zeigt das Video im Verlauf',
    'Gyors keresés: Cmd+K (Windowson és Linuxon Ctrl+K), oldalak, beállítások és előzmények egy helyen':
        'Schnellsuche: Cmd+K (unter Windows und Linux Strg+K), Seiten, Einstellungen und Verlauf an einem Ort',
    'Új felület oldalsávval, a letöltő tetején a Videó kiválasztása és az Aktív letöltések':
        'Neue Oberfläche mit Seitenleiste, oben im Downloader „Video auswählen“ und „Aktive Downloads“',
    'Az elkészült letöltések a listában maradnak, amíg el nem távolítod őket':
        'Fertige Downloads bleiben in der Liste, bis du sie entfernst',
    'Az Előzményekben egyszerre több videót is kijelölhetsz és törölhetsz':
        'Im Verlauf kannst du mehrere Videos gleichzeitig auswählen und löschen',
    'Windowson a program mappájában csak az indítófájl látszik':
        'Unter Windows ist im Programmordner nur die Startdatei zu sehen',
    'Új lejátszó (mpv): akadás nélkül játszik le nagy felbontásban és teljes képernyőn is':
        'Neuer Player (mpv): ruckelfreie Wiedergabe auch in hoher Auflösung und im Vollbild',
    'A régi beépített lejátszó a Beállításokban továbbra is választható':
        'Der alte eingebaute Player kann in den Einstellungen weiterhin gewählt werden',
    'HDR letöltés, ha a videónak van HDR változata':
        'HDR-Download, wenn das Video eine HDR-Version hat',
    'Az app Macen, Windowson és Linuxon is fut':
        'Die App läuft auf Mac, Windows und Linux',
    'Beépített lejátszó a letöltött videókhoz és mp3-akhoz, teljes képernyővel és kis ablakos móddal':
        'Eingebauter Player für geladene Videos und MP3s, mit Vollbild und kleinem Fenstermodus',
    'NAS-ra is kíméletesen tölt le: a félkész fájlok a gépen készülnek, a célmappába csak a kész videó kerül':
        'Schonend für NAS-Laufwerke: Unfertige Dateien entstehen auf dem Computer, nur das fertige Video kommt in den Zielordner',
    'Az Előzmények kereshető, rendezhető és szűrhető, a már letöltött linkre az app figyelmeztet':
        'Der Verlauf ist durchsuch-, sortier- und filterbar, und die App warnt bei bereits geladenen Links',
    'Az Előzmények jelszóval zárolható':
        'Der Verlauf kann mit einem Passwort gesperrt werden',
    'Egyszerre több letöltés, lejátszási listák és csatornák letöltése, mp3 mentés':
        'Mehrere Downloads gleichzeitig, Playlists und Kanäle laden, als MP3 speichern',
    'Előzmények':
        'Verlauf',
    'ffmpeg (kompatibilitás)':
        'ffmpeg (Kompatibilität)',
    'mpv (ajánlott)':
        'mpv (empfohlen)',
    'Dátum (újabb elöl)':
        'Datum (neueste zuerst)',
    'Név (A-tól Z-ig)':
        'Name (A bis Z)',
    'Méret (nagyobb elöl)':
        'Größe (größte zuerst)',
    'Csak mp3 (hang)':
        'Nur MP3 (Audio)',
    'Csak videó':
        'Nur Video',
    'Minden':
        'Alle',
    'Várakozik':
        'Wartet',
    'Link megnyitása':
        'Link wird geöffnet',
    'Formátumok beolvasása':
        'Formate werden gelesen',
    'Oldal letöltése':
        'Seite wird geladen',
    'Bélyegkép letöltése':
        'Vorschaubild wird geladen',
    'Adatok lekérése':
        'Daten werden abgerufen',
    'Kivágás':
        'Ausschneiden',
    'Másolás':
        'Kopieren',
    'Beillesztés':
        'Einfügen',
    'Összes kijelölése':
        'Alles auswählen',
    'Beúszás':
        'Einschieben',
    'Áttűnés':
        'Überblenden',
    '↑↓ választás   Enter: megnyitás   Esc: bezárás':
        '↑↓ auswählen   Enter: öffnen   Esc: schließen',
    'Letöltő':
        'Downloader',
    'Videó kiválasztása':
        'Video auswählen',
    'Aktív letöltések':
        'Aktive Downloads',
    'Oldal':
        'Seite',
    'Beállítások':
        'Einstellungen',
    'Link beillesztése a vágólapról':
        'Link aus der Zwischenablage einfügen',
    'Művelet':
        'Aktion',
    'Újdonságok ebben a verzióban':
        'Neu in dieser Version',
    'Téma':
        'Design',
    'Téma: {label}':
        'Design: {label}',
    'Megjelenés: Sötét':
        'Erscheinungsbild: Dunkel',
    'Megjelenés: Világos':
        'Erscheinungsbild: Hell',
    'Előzmény':
        'Verlauf',
    '  Nincs találat':
        '  Keine Treffer',
    'Figyelem':
        'Hinweis',
    'Hiba':
        'Fehler',
    'Letöltés kész':
        'Download fertig',
    '{n_entries} videót találtam':
        '{n_entries} Videos gefunden',
    ' (az első {playlist_max}-ra korlátoztam)':
        ' (auf die ersten {playlist_max} begrenzt)',
    '. Pipáld ki, amit le szeretnél tölteni.':
        '. Hake an, was du herunterladen möchtest.',
    'Mind':
        'Alle',
    'Egyik sem':
        'Keine',
    'Minőség':
        'Qualität',
    'Sorba állítás':
        'Einreihen',
    'Mégse':
        'Abbrechen',
    '{n} kijelölve':
        '{n} ausgewählt',
    '{app} névjegye':
        'Über {app}',
    'Alkalmazás verziója':
        'App-Version',
    'yt-dlp verziója':
        'yt-dlp-Version',
    'Újdonságok':
        'Neuigkeiten',
    'Jelenlegi verzió: v.{app_version}':
        'Aktuelle Version: v.{app_version}',
    'Korábbi, 1.0 előtti verziók':
        'Frühere Versionen vor 1.0',
    '   jelenlegi':
        '   aktuell',
    'A hang nem elérhető':
        'Ton nicht verfügbar',
    '  (normál)':
        '  (normal)',
    '{x}{x2} mp':
        '{x}{x2} s',
    'Az mpv lejátszó nem indult el rendesen (hibakód: {code}).\nHa a fájl más programban lejátszható, nézd meg, hogy az mpv teljes és friss-e.\n':
        'Der mpv-Player ist nicht richtig gestartet (Fehlercode: {code}).\nWenn sich die Datei in anderen Programmen abspielen lässt, prüfe, ob mpv vollständig und aktuell ist.\n',
    'Windowson ehhez a videókártya friss illesztőprogramja is kell.':
        'Unter Windows wird dafür auch ein aktueller Grafikkartentreiber benötigt.',
    'Igen':
        'Ja',
    'Nem':
        'Nein',
    'Az előzmények zárolva vannak':
        'Der Verlauf ist gesperrt',
    'Add meg a jelszót a megtekintésükhöz.':
        'Gib das Passwort ein, um ihn anzusehen.',
    'Feloldás':
        'Entsperren',
    'Elfelejtett jelszó':
        'Passwort vergessen',
    'Túl sok hibás próba. Próbáld újra {wait} mp múlva.':
        'Zu viele Fehlversuche. Versuche es in {wait} s erneut.',
    'Hibás jelszó. {lock_wait_seconds} mp várakozás következik.':
        'Falsches Passwort. Bitte {lock_wait_seconds} s warten.',
    'Hibás jelszó.':
        'Falsches Passwort.',
    'A jelszó visszaállításával az összes előzmény és a hozzájuk tartozó bélyegképek véglegesen törlődnek, és a jelszavas védelem kikapcsol.\n\nFolytatod?':
        'Beim Zurücksetzen des Passworts werden der gesamte Verlauf und die Vorschaubilder endgültig gelöscht, und der Passwortschutz wird ausgeschaltet.\n\nFortfahren?',
    'Törlés és visszaállítás':
        'Löschen und zurücksetzen',
    'A jelszó legalább {lock_min_len} karakter legyen.':
        'Das Passwort muss mindestens {lock_min_len} Zeichen lang sein.',
    'A két jelszó nem egyezik.':
        'Die beiden Passwörter stimmen nicht überein.',
    'Jelszó beállítása':
        'Passwort festlegen',
    'Ezzel zárolhatod az előzményeket. Ha elfelejted, csak az előzmények törlésével lehet visszaállítani.':
        'Damit sperrst du den Verlauf. Wenn du das Passwort vergisst, lässt es sich nur durch Löschen des Verlaufs zurücksetzen.',
    'Beállítás':
        'Festlegen',
    'Jelszó újra':
        'Passwort wiederholen',
    'Új jelszó':
        'Neues Passwort',
    'Az új jelszó legalább {lock_min_len} karakter legyen.':
        'Das neue Passwort muss mindestens {lock_min_len} Zeichen lang sein.',
    'A két új jelszó nem egyezik.':
        'Die beiden neuen Passwörter stimmen nicht überein.',
    'Jelszó módosítása':
        'Passwort ändern',
    'Jelenlegi jelszó':
        'Aktuelles Passwort',
    'Módosítás':
        'Ändern',
    'Új jelszó újra':
        'Neues Passwort wiederholen',
    'Védelem kikapcsolása':
        'Schutz ausschalten',
    'A jelszó megadása után az előzmények újra jelszó nélkül elérhetők.':
        'Nach Eingabe des Passworts ist der Verlauf wieder ohne Passwort zugänglich.',
    'Jelszó':
        'Passwort',
    'Kikapcsolás':
        'Ausschalten',
    'Előzmények védelme':
        'Verlaufsschutz',
    'Nincs bekapcsolva':
        'Nicht eingeschaltet',
    'Jelszó beállítása…':
        'Passwort festlegen…',
    'Be van kapcsolva':
        'Eingeschaltet',
    'Zárolás most':
        'Jetzt sperren',
    'Jelszó módosítása…':
        'Passwort ändern…',
    'Kikapcsolás…':
        'Ausschalten…',
    'Nézet':
        'Ansicht',
    'Keresés':
        'Suchen',
    'Szöveg törlése':
        'Text löschen',
    'Feltöltő, cím, dátum vagy weboldal neve (több szó is lehet).':
        'Uploader, Titel, Datum oder Name der Website (auch mehrere Wörter).',
    'Összes előzmény törlése':
        'Gesamten Verlauf löschen',
    'Még nincs letöltés':
        'Noch keine Downloads',
    'Az elkészült letöltéseid itt jelennek meg.':
        'Deine fertigen Downloads erscheinen hier.',
    'Lejátszás (alap)':
        'Abspielen (Standard)',
    'Letöltve':
        'Heruntergeladen',
    'Méret':
        'Größe',
    '{n__hist_view} találat ({n_history} bejegyzésből)':
        '{n__hist_view} Treffer (von {n_history} Einträgen)',
    'Az előzmények ki vannak kapcsolva':
        'Der Verlauf ist ausgeschaltet',
    'a {extra} legrégebbi bejegyzés':
        'die {extra} ältesten Einträge',
    'az összes bejegyzés':
        'alle Einträge',
    'Előzmények méretének csökkentése':
        'Verlauf verkleinern',
    'A kisebb méret miatt {what} törlődik az előzményekből.\n\nA letöltött fájlok a lemezen megmaradnak.':
        'Wegen der kleineren Größe werden {what} aus dem Verlauf entfernt.\n\nDie geladenen Dateien bleiben auf dem Datenträger.',
    'Törlés':
        'Löschen',
    'Nincs találat':
        'Keine Treffer',
    'Próbálj másik kifejezést vagy szűrést.':
        'Versuche einen anderen Suchbegriff oder Filter.',
    'Próbálj másik kifejezést.':
        'Versuche einen anderen Suchbegriff.',
    'A Beállításokban bekapcsolhatod.':
        'Du kannst ihn in den Einstellungen einschalten.',
    'Rendezés':
        'Sortieren',
    'Szűrés típus szerint':
        'Nach Typ filtern',
    'A fájl már nem található, ezért a mappáját nyitottam meg.\n\n{x}':
        'Die Datei existiert nicht mehr, daher wurde ihr Ordner geöffnet.\n\n{x}',
    'Nem találom a fájlt és a mappáját sem ezen az útvonalon:\n\n{x}':
        'Weder die Datei noch ihr Ordner wurden unter diesem Pfad gefunden:\n\n{x}',
    'A fájl már nem található ezen az útvonalon:\n\n{x}':
        'Die Datei existiert unter diesem Pfad nicht mehr:\n\n{x}',
    'Lejátszás ({name})':
        'Abspielen ({name})',
    'Nem sikerült megnyitni a fájlt az alapértelmezett programmal.':
        'Die Datei konnte nicht mit dem Standardprogramm geöffnet werden.',
    'A beépített lejátszóhoz ffmpeg kell, de nincs telepítve.\n':
        'Der eingebaute Player braucht ffmpeg, es ist aber nicht installiert.\n',
    '\n\nVálthatsz az mpv lejátszóra a Beállításokban, vagy használhatod az "Alap lejátszóval" gombot.':
        '\n\nDu kannst in den Einstellungen zum mpv-Player wechseln oder die Schaltfläche „Abspielen (Standard)“ verwenden.',
    'Ezt a fájlt a beépített lejátszó nem tudja lejátszani (nincs benne kép vagy hang, vagy nem olvasható).\nPróbáld az "Alap lejátszóval" gombot.':
        'Der eingebaute Player kann diese Datei nicht abspielen (kein Bild oder Ton, oder nicht lesbar).\nVersuche die Schaltfläche „Abspielen (Standard)“.',
    'A hang lejátszásához a sounddevice csomag kell, de nem érhető el.\nTelepítés: pip3 install sounddevice\n\nAddig használhatod az "Alap lejátszóval" gombot.':
        'Für die Tonwiedergabe wird das Paket sounddevice benötigt, es ist aber nicht verfügbar.\nInstallation: pip3 install sounddevice\n\nBis dahin kannst du die Schaltfläche „Abspielen (Standard)“ verwenden.',
    'A lejátszóhoz az mpv kell, de nincs telepítve.\n':
        'Der Player braucht mpv, es ist aber nicht installiert.\n',
    '\n\nVálthatsz a beépített lejátszóra a Beállításokban, vagy használhatod az "Alap lejátszóval" gombot.':
        '\n\nDu kannst in den Einstellungen zum eingebauten Player wechseln oder die Schaltfläche „Abspielen (Standard)“ verwenden.',
    'Nem sikerült elindítani az mpv lejátszót.':
        'Der mpv-Player konnte nicht gestartet werden.',
    'Biztosan törlöd ezt a bejegyzést az előzményekből?\n\n{x}\n\nA fájl a lemezen megmarad.':
        'Diesen Eintrag aus dem Verlauf entfernen?\n\n{x}\n\nDie Datei bleibt auf dem Datenträger.',
    '\n... és még {x}':
        '\n... und {x} weitere',
    'Biztosan törlöd a kijelölt {n_indices} bejegyzést az előzményekből?\n\n{names}{more}\n\nA fájlok a lemezen megmaradnak.':
        'Die {n_indices} ausgewählten Einträge aus dem Verlauf entfernen?\n\n{names}{more}\n\nDie Dateien bleiben auf dem Datenträger.',
    'Törlés az előzményből':
        'Aus dem Verlauf entfernen',
    'Biztosan törlöd az összes előzményt ({n_history} bejegyzés)?\n\nA letöltött fájlok a lemezen megmaradnak.':
        'Den gesamten Verlauf löschen ({n_history} Einträge)?\n\nDie geladenen Dateien bleiben auf dem Datenträger.',
    'nincs mentve':
        'nicht gespeichert',
    'Animáció: {x}':
        'Animation: {x}',
    'Így jelenik meg az értesítés':
        'So sehen Mitteilungen aus',
    'Minta':
        'Vorschau',
    'Alapértelmezett (a rendszer ideiglenes mappája)':
        'Standard (temporärer Ordner des Systems)',
    '\nSzabad hely: {x}':
        '\nFreier Speicher: {x}',
    '\nA mappa most nem érhető el, addig az alapértelmezett lesz használva.':
        '\nDer Ordner ist gerade nicht erreichbar, bis dahin wird der Standard verwendet.',
    'Ideiglenes fájlok mappája':
        'Ordner für temporäre Dateien',
    'Ebbe a mappába nem lehet írni.':
        'In diesen Ordner kann nicht geschrieben werden.',
    'Nyelv, megjelenés, értesítések, letöltés, előzmények és védelem':
        'Sprache, Erscheinungsbild, Mitteilungen, Downloads, Verlauf und Schutz',
    'Nyelv':
        'Sprache',
    'Az alkalmazás nyelve. Automatikus beállításnál a rendszer nyelvét követi, ha az magyar, angol vagy német, egyébként angol. A váltás az app újraindítása után lép életbe.':
        'Die Sprache der App. „Automatisch“ folgt der Systemsprache, wenn sie Ungarisch, Englisch oder Deutsch ist, sonst Englisch. Die Änderung gilt nach einem Neustart der App.',
    'Automatikus (a rendszer nyelve)':
        'Automatisch (Systemsprache)',
    'Az alkalmazás témájának kiválasztása.':
        'Wähle das Design der App.',
    'Rendszer':
        'System',
    'Sötét':
        'Dunkel',
    'Világos':
        'Hell',
    'Értesítések':
        'Mitteilungen',
    'Értesítések a letöltések végén':
        'Mitteilung, wenn Downloads fertig sind',
    'Hangjelzés a letöltések végén':
        'Ton, wenn Downloads fertig sind',
    'Be':
        'Ein',
    'Ki':
        'Aus',
    'Értesítések animációja':
        'Animation',
    'Ideiglenes fájlok helye':
        'Ort der temporären Dateien',
    'Az alkalmazás letöltés közben ideiglenes fájlokkal dolgozik. Ez néha gondot jelenthet, ha közvetlenül NAS gépre töltesz le, például a NAS logja megtelik a letöltött videók bejegyzéseivel. Ennél a beállításnál kijelölhetsz egy mappát, ahova az ideiglenes fájlok kerülnek, így a célmappába csak a kész videó lesz átmásolva. Az ideiglenes fájlok automatikusan törlődnek a videó sikeres letöltése és megszakítás után.':
        'Beim Herunterladen arbeitet die App mit temporären Dateien. Das kann stören, wenn du direkt auf ein NAS lädst, zum Beispiel füllt sich dessen Protokoll mit Einträgen zu den Downloads. Hier kannst du einen Ordner für die temporären Dateien festlegen, sodass nur das fertige Video in den Zielordner kopiert wird. Temporäre Dateien werden nach einem erfolgreichen Download oder einem Abbruch automatisch gelöscht.',
    'Célmappában':
        'Im Zielordner',
    'Ideiglenes mappában':
        'In einem temporären Ordner',
    'Mappa…':
        'Ordner…',
    'Alap':
        'Standard',
    'Előzmények mérete':
        'Größe des Verlaufs',
    'Itt az előzmények listában szereplő bejegyzések mennyiségét állíthatod be. Ha a lista megtelt, az utolsó bejegyzés automatikusan eltűnik a listából. Ha nagyobb értékről kisebbre állítod, szintén eltűnnek a régebbi bejegyzések.':
        'Lege fest, wie viele Einträge der Verlauf behält. Ist die Liste voll, verschwindet der älteste Eintrag automatisch. Wenn du den Wert verkleinerst, werden ältere Einträge ebenfalls entfernt.',
    'Beépített lejátszó':
        'Eingebauter Player',
    'Az mpv egy modernebb lejátszóval indítja a letöltött videókat. Támogatja a HDR formátumokat, 4K és 60 fps videók esetén is megfelelő teljesítményt nyújt, és több beállítási lehetősége van (jobb klikk a videón). Az ffmpeg egy egyszerűbb beépített lejátszó, kevesebb funkcióval és kevésbé jó teljesítménnyel, főleg régebbi gépekhez ajánlott.':
        'mpv öffnet geladene Videos in einem moderneren Player. Er unterstützt HDR, läuft auch bei 4K- und 60-fps-Videos flüssig und bietet mehr Optionen (Rechtsklick auf das Video). ffmpeg ist ein einfacher eingebauter Player mit weniger Funktionen und geringerer Leistung, vor allem für ältere Computer.',
    'Böngésző sütik használata':
        'Browser-Cookies verwenden',
    'Ezt alapból hagyd a „Nincs” lehetőségen. Csak akkor válts, ha egy oldal bejelentkezést vagy sütit kér a tartalmak megjelenítéséhez.':
        'Lass das standardmäßig auf „Keine“. Ändere es nur, wenn eine Seite eine Anmeldung oder Cookies verlangt, um Inhalte anzuzeigen.',
    'yt-dlp frissítése':
        'yt-dlp aktualisieren',
    'Ahhoz, hogy a letöltő megfelelően működjön, időnként frissíteni szükséges a yt-dlp plugint.':
        'Damit der Downloader weiter funktioniert, muss yt-dlp ab und zu aktualisiert werden.',
    'Telepített verzió: {ytdlp_version}':
        'Installierte Version: {ytdlp_version}',
    'Frissítés keresése':
        'Nach Updates suchen',
    'Frissítés letöltése':
        'Update herunterladen',
    'Visszamenőleges verziótörténet az utókor számára.':
        'Die komplette Versionsgeschichte für die Nachwelt.',
    'Verziótörténet':
        'Versionsverlauf',
    'Névjegy':
        'Über',
    '(letöltve, újraindítás után lép életbe)':
        '(geladen, gilt nach dem Neustart)',
    '(frissítés érhető el)':
        '(Update verfügbar)',
    'Frissítés keresése...':
        'Suche nach Updates...',
    'Nem sikerült megnézni az új verziót. Van internet?':
        'Konnte nicht nach einer neuen Version suchen. Bist du online?',
    'Az yt-dlp naprakész.':
        'yt-dlp ist aktuell.',
    'Az új verzió már le van töltve, indítsd újra az appot, hogy életbe lépjen.':
        'Die neue Version ist bereits geladen. Starte die App neu, damit sie aktiv wird.',
    'Új verzió érhető el: {latest_ytdlp}':
        'Neue Version verfügbar: {latest_ytdlp}',
    'Letöltés indul...':
        'Download startet...',
    'Letöltés...':
        'Wird geladen...',
    'Letöltés: {pct}%':
        'Wird geladen: {pct}%',
    'Ellenőrzés és telepítés...':
        'Prüfen und installieren...',
    'A frissítés nem sikerült.':
        'Das Update ist fehlgeschlagen.',
    'Az yt-dlp frissítése nem sikerült.\n\n':
        'Die Aktualisierung von yt-dlp ist fehlgeschlagen.\n\n',
    'Kész: a(z) {version} verzió letöltve. Indítsd újra az appot, hogy életbe lépjen.':
        'Fertig: Version {version} geladen. Starte die App neu, damit sie aktiv wird.',
    'Másold be a videó linkjét, vagy több linket soronként.':
        'Füge einen Videolink ein, oder mehrere Links, einen pro Zeile.',
    'Videó linkje':
        'Videolink',
    'Videó adatai':
        'Videodaten',
    'Felbontás':
        'Auflösung',
    'Előbb kérd le a videó adatait.':
        'Rufe zuerst die Videodaten ab.',
    'letöltés HDR minőségben':
        'in HDR-Qualität laden',
    'Hangminőség':
        'Audioqualität',
    'Letöltendő rész':
        'Zu ladender Teil',
    'Teljes videó':
        'Ganzes Video',
    'Kijelölt rész':
        'Ausgewählter Teil',
    'Kezdete':
        'Anfang',
    'Vége':
        'Ende',
    'Feliratok letöltése':
        'Untertitel laden',
    'Letöltési mappa':
        'Download-Ordner',
    'Tallózás…':
        'Durchsuchen…',
    'Megszakítás':
        'Abbrechen',
    '↓  Letöltés':
        '↓  Herunterladen',
    'Mentés ezen a néven':
        'Speichern als',
    'Válassz felbontást, majd nyomd meg a Letöltés gombot.':
        'Wähle eine Auflösung und klicke dann auf „Herunterladen“.',
    'Az időpontot így add meg: 1:30 vagy 1:02:30.':
        'Gib die Zeit so ein: 1:30 oder 1:02:30.',
    'A vége legyen később, mint a kezdete.':
        'Das Ende muss nach dem Anfang liegen.',
    'A videó csak {x} hosszú.':
        'Das Video ist nur {x} lang.',
    '{x} hosszú rész':
        'Teil mit {x} Länge',
    'Csak hang':
        'Nur Audio',
    'Más ▾':
        'Mehr ▾',
    'Feltöltő':
        'Uploader',
    'Hossz':
        'Länge',
    '{x}-tól {x2}-ig':
        '{x} bis {x2}',
    'Becsült méret':
        'Geschätzte Größe',
    'Mentés ezen a néven: {name}\nVálassz felbontást, majd nyomd meg a Letöltés gombot.':
        'Speichern als: {name}\nWähle eine Auflösung und klicke dann auf „Herunterladen“.',
    'Ezt már letöltötted':
        'Bereits heruntergeladen',
    'Ezt a linket már letöltötted ({when}):\n\n{x}\n\nLetöltöd még egyszer?':
        'Diesen Link hast du schon heruntergeladen ({when}):\n\n{x}\n\nNoch einmal herunterladen?',
    'Letöltöm újra':
        'Erneut herunterladen',
    'Mégsem':
        'Abbrechen',
    'A kiválasztott mappa nem létezik.':
        'Der gewählte Ordner existiert nicht.',
    'Ezeket már letöltötted':
        'Bereits heruntergeladen',
    'Igen, újra is':
        'Ja, die auch',
    'Kihagyom őket':
        'Überspringen',
    '{n_dups} linket korábban már letöltöttél (a {n_links} közül).\n\nLetöltöd ezeket is újra?':
        'Bereits früher geladene Links: {n_dups} von {n_links}.\n\nDiese auch erneut herunterladen?',
    'Minden link már le volt töltve.':
        'Alle Links wurden bereits heruntergeladen.',
    '{n_entries} link beillesztve.':
        'Eingefügte Links: {n_entries}.',
    'Beillesztett linkek':
        'Eingefügte Links',
    'A linkek letöltését elvetted.':
        'Du hast das Herunterladen der Links verworfen.',
    'Előbb másold be a videó linkjét.':
        'Füge zuerst den Videolink ein.',
    'Videó keresése az oldalon':
        'Video auf der Seite wird gesucht',
    'Indul':
        'Startet',
    'Videó adatainak lekérése: {x}%  ({fetch_stage}, {secs} mp)':
        'Videodaten werden abgerufen: {x}%  ({fetch_stage}, {secs} s)',
    'Nem találtam elérhető felbontást ehhez a linkhez.':
        'Für diesen Link wurde keine verfügbare Auflösung gefunden.',
    'Nem találtam letölthető videót ezen a linken.':
        'Unter diesem Link wurde kein ladbares Video gefunden.',
    'Lejátszási lista: {n_entries} videó.':
        'Playlist: {n_entries} Videos.',
    'Lejátszási lista':
        'Playlist',
    'A lejátszási lista letöltését elvetted.':
        'Du hast das Herunterladen der Playlist verworfen.',
    'Az mp3 készítéséhez ffmpeg kell, de nincs telepítve.\n':
        'Für MP3s wird ffmpeg benötigt, es ist aber nicht installiert.\n',
    '{added} videót tettem a sorba, a többi már szerepelt a listában, vagy betelt a sor.':
        'Eingereihte Videos: {added}. Die übrigen waren schon in der Liste, oder die Warteschlange ist voll.',
    'Adatok lekérése...':
        'Daten werden abgerufen...',
    'Nem sikerült lekérni a videó adatait.':
        'Die Videodaten konnten nicht abgerufen werden.',
    'A videó adatainak lekérése nem sikerült.':
        'Das Abrufen der Videodaten ist fehlgeschlagen.',
    'Újrapróbálkozás':
        'Erneut versuchen',
    '{headline}\n\n{text}\n\nÚjrapróbáljam?':
        '{headline}\n\n{text}\n\nErneut versuchen?',
    'lassú vagy megszakadt az internet':
        'das Internet ist langsam oder unterbrochen',
    'az oldal nem válaszol':
        'die Seite antwortet nicht',
    'elavult az yt-dlp (a Beállítások fülön van frissítés keresés)':
        'yt-dlp ist veraltet (Update-Suche in den Einstellungen)',
    'a(z) {x} sütijeinek beolvasása várhat egy rendszerablakra (például jelszókérésre)':
        'das Lesen der Cookies von {x} wartet vielleicht auf ein Systemfenster (zum Beispiel eine Passwortabfrage)',
    'Az adatlekérés már több mint {fetch_stall_seconds:g} másodperce tart, valami akadozik.\n\nLehetséges okok:\n':
        'Das Abrufen der Daten dauert schon über {fetch_stall_seconds:g} Sekunden, etwas hakt.\n\nMögliche Ursachen:\n',
    '\n\nMegszakítsam, és újrapróbáljam?':
        '\n\nAbbrechen und erneut versuchen?',
    'A lekérés elakadt':
        'Der Abruf hängt',
    'Az adatok lekérését megszakítottam.':
        'Das Abrufen der Daten wurde abgebrochen.',
    'A link megváltozott, kérd le újra a videó adatait.':
        'Der Link hat sich geändert, rufe die Videodaten erneut ab.',
    'Legfeljebb {max_jobs} letöltés lehet a listában. Várd meg, amíg néhány elkészül.':
        'Die Liste fasst höchstens {max_jobs} Downloads. Warte, bis einige fertig sind.',
    'Ez a videó ebben a minőségben már szerepel a letöltések között.':
        'Dieses Video ist in dieser Qualität schon bei den Downloads.',
    'Az ffmpeg nincs telepítve, ezért nem biztos, hogy mp4 lesz belőle.\n':
        'ffmpeg ist nicht installiert, daher wird es eventuell keine MP4.\n',
    'Indul...':
        'Startet...',
    'még {x} mp':
        'noch {x} s',
    'mp3 átalakítás':
        'Umwandlung in MP3',
    'mp4 összefűzés':
        'MP4 wird zusammengefügt',
    'Feldolgozás ({what})...':
        'Verarbeitung ({what})...',
    'Kész, de a felirat nem jött le':
        'Fertig, aber die Untertitel kamen nicht mit',
    'Kész':
        'Fertig',
    'Megszakítva':
        'Abgebrochen',
    'Nem sikerült a letöltés':
        'Download fehlgeschlagen',
    'Legfeljebb {max_jobs} letöltés lehet a sorban. Várd meg, amíg néhány elkészül.':
        'Die Warteschlange fasst höchstens {max_jobs} Downloads. Warte, bis einige fertig sind.',
    '{name}\n\nMappa: {folder}':
        '{name}\n\nOrdner: {folder}',
    'Kész, a hangfájl a kiválasztott mappába került.':
        'Fertig, die Audiodatei liegt im gewählten Ordner.',
    'Kész, a videó a kiválasztott mappába került.':
        'Fertig, das Video liegt im gewählten Ordner.',
    '\n… és még {x}':
        '\n… und {x} weitere',
    'Mind a(z) {n_ok} letöltés elkészült.\n\n{names}':
        'Alle Downloads fertig ({n_ok}).\n\n{names}',
    '\n\n{failed} letöltés nem sikerült.':
        '\n\nFehlgeschlagene Downloads: {failed}.',
    'Kész, {n_ok} letöltés elkészült.':
        'Fertig, abgeschlossene Downloads: {n_ok}.',
    'Kész a letöltés':
        'Download fertig',
    '{n_ok} letöltés elkészült':
        'Fertige Downloads: {n_ok}',
    'és még {x} videó':
        'und {x} weitere Videos',
    ', {failed} nem sikerült':
        ', fehlgeschlagen: {failed}',
    'Megszakítás...':
        'Wird abgebrochen...',
    'Készek eltávolítása':
        'Fertige entfernen',
    'Egyszerre legfeljebb {max_parallel} letöltés fut, a többi sorban vár.':
        'Bis zu {max_parallel} Downloads laufen gleichzeitig, der Rest wartet.',
    'Újrapróbálás':
        'Erneut versuchen',
    'Eltávolítás':
        'Entfernen',
    'néhány oldal nem fog működni, mert a curl_cffi csomag hiányzik':
        'einige Seiten funktionieren nicht, weil das Paket curl_cffi fehlt',
    'a bélyegképek nem látszanak, mert a pillow csomag hiányzik':
        'Vorschaubilder fehlen, weil das Paket pillow fehlt',
    '\nFigyelem: ':
        '\nHinweis: ',
    'Az új nyelv az app újraindítása után lép életbe.':
        'Die neue Sprache gilt nach einem Neustart der App.',
    'Később':
        'Später',
    'Újraindítás most':
        'Jetzt neu starten',
    'Kilépés':
        'Beenden',
    'Még {n_running} letöltés fut vagy vár. Ha kilépsz, ezek megszakadnak.\n\nBiztosan kilépsz?':
        'Noch laufende oder wartende Downloads: {n_running}. Beim Beenden werden sie abgebrochen.\n\nTrotzdem beenden?',
    'KÖNYVTÁR':
        'BIBLIOTHEK',
    '♥  Ko-fi támogatás':
        '♥  Ko-fi-Spende',
    '●  Újdonságok ebben a verzióban':
        '●  Neu in dieser Version',
    'január':
        'Januar',
    'február':
        'Februar',
    'március':
        'März',
    'április':
        'April',
    'május':
        'Mai',
    'június':
        'Juni',
    'július':
        'Juli',
    'augusztus':
        'August',
    'szeptember':
        'September',
    'október':
        'Oktober',
    'november':
        'November',
    'december':
        'Dezember',
    "Az Újdonságok ablak mindig előre nyílik, és simább lett a görgetés.": "Das Fenster „Neuigkeiten“ öffnet sich jetzt immer im Vordergrund, und das Scrollen ist flüssiger.",
    'Kivágás áttűnéssel':
        'Mit Überblendung',
    'Kivágott szponzor tartalom':
        'Gesponserter Inhalt entfernt',
    'Kivágott rész: {x}':
        'Entfernt: {x}',
    'Kivágott rész':
        'Teil entfernt',
    'Áttűnések készítése: {pct}%':
        'Überblendungen: {pct}%',
    'SponsorBlock: kivágás áttűnéssel is, így a vágás helyén egy rövid elsötétülés és felirat jelzi, hogy kimaradt valami.':
        'SponsorBlock: Ausschneiden jetzt auch mit Überblendung, eine kurze Abblende und eine Einblendung zeigen, wo etwas entfernt wurde.',
    'Kijelölt rész: {pct}%  ({done} / {total})':
        'Ausgewählter Teil: {pct}%  ({done} / {total})',
    'Kijelölt rész előkészítése... {secs} mp':
        'Ausgewählter Teil wird vorbereitet... {secs} s',
    'Kijelölt rész letöltése: gyorsabb, látszik a haladás, és a megszakítás is működik.':
        'Ausgewählten Teil laden: schneller, mit Fortschrittsanzeige, und Abbrechen funktioniert.',
    'Kilépéskor nem jön hibaablak Windowson.':
        'Beim Beenden unter Windows erscheint kein Fehlerfenster mehr.',
    'Kész, áttűnés nélkül (sima vágás)':
        'Fertig, ohne Überblendung (einfacher Schnitt)',
    'SponsorBlock hibajavítások':
        'SponsorBlock-Fehlerbehebungen',
    'Hibajavítások és dupla kattintásos műveletek hozzáadása':
        'Fehlerbehebungen und neue Doppelklick-Aktionen',
    'Sebességkorlát: {x} MB/s':
        'Tempolimit: {x} MB/s',
    'Sebességkorlát: ki':
        'Tempolimit: aus',
    'Sebességkorlát':
        'Tempolimit',
    'Ha bekapcsolod, a letöltések együtt legfeljebb ennyi sebességgel töltenek, így a többi gép és alkalmazás is kényelmesen használhatja az internetet. Futó letöltésre is azonnal hat. Gyorsan ki- és bekapcsolhatod az Előzmények oldalon is.':
        'Wenn aktiv, laden alle Downloads zusammen höchstens mit dieser Geschwindigkeit, damit andere Geräte und Apps das Internet weiter bequem nutzen können. Es wirkt sofort, auch bei laufenden Downloads. Du kannst es auch auf der Seite „Verlauf“ schnell ein- und ausschalten.',
    'Egyéni':
        'Eigene',
    'Egyéni…':
        'Eigener Wert…',
    'Egyéni érték:':
        'Eigener Wert:',
    'letöltés':
        'Downloads',
    '{a} és {b} MB/s közötti számot adj meg.':
        'Gib eine Zahl zwischen {a} und {b} MB/s ein.',
    '1 és {b} közötti egész számot adj meg.':
        'Gib eine ganze Zahl zwischen 1 und {b} ein.',
    'Egyszerre futó letöltések':
        'Gleichzeitige Downloads',
    'Minden letöltés egyszerre fut, nincs várakozó sor.':
        'Alle Downloads laufen gleichzeitig, nichts wartet in der Warteschlange.',
    'Ennyi letöltés fut egyszerre, a többi sorban vár, és akkor indul, amikor egy elkészül. Több egyszerre futó letöltés nem mindig gyorsabb, mert osztoznak az interneten. Korlátlannál minden letöltés azonnal indul.':
        'So viele Downloads laufen gleichzeitig, der Rest wartet und startet, sobald einer fertig ist. Mehr gleichzeitige Downloads sind nicht immer schneller, weil sie sich die Internetverbindung teilen. Bei „Unbegrenzt“ startet jeder Download sofort.',
    'Finomhangolások, az app ikonjának téma szerinti változtatása és letöltési limitek testreszabhatósága.':
        'Feinschliff, ein App-Symbol passend zum Design und anpassbare Download-Limits.',
    'A fájl nem található':
        'Datei nicht gefunden',
    'A fájl nem található ezen az útvonalon.':
        'Die Datei ist unter diesem Pfad nicht zu finden.',
    'Eredeti link':
        'Originallink',
    'FOLYAMATBAN':
        'LÄUFT',
    'Fájl':
        'Datei',
    'Hozzáadva. Most {active} fut, {waiting} vár. Az Előzmények oldalon látod az állapotukat.':
        'Hinzugefügt. Laufend: {active}, wartend: {waiting}. Den Stand siehst du auf der Seite „Verlauf“.',
    'KORÁBBAN':
        'FRÜHER',
    'Kattints a kártyákra a kijelöléshez':
        'Klicke auf die Karten, um sie auszuwählen',
    'Kijelölés':
        'Auswählen',
    'LETÖLTVE':
        'GELADEN',
    'LETÖLTVE · {x}':
        'GELADEN · {x}',
    'MA':
        'HEUTE',
    'Mappa':
        'Ordner',
    'Mind kijelölése':
        'Alle auswählen',
    'TEGNAP':
        'GESTERN',
    'Továbbiak ({n} még)':
        'Mehr anzeigen (noch {n})',
    'Törlés ({n})':
        'Löschen ({n})',
    '{a} letöltés fut':
        '{a} laufen',
    '{a} letöltés fut, {w} vár':
        '{a} laufen, {w} warten',
    '{n} videó kijelölve':
        '{n} ausgewählt',
    '{n} videó letöltve':
        '{n} Videos geladen',
    '▶  Lejátszás':
        '▶  Abspielen',
    '✓  Letöltve':
        '✓  Geladen',
    'Jelszóval elrejtheted az Előzmények oldalt (a futó letöltésekkel együtt) és a korábbi letöltési útvonalak listáját a kíváncsi szemek elől. Az app indítása után és {n} perc tétlenség után újra kéri a jelszót.':
        'Mit einem Passwort kannst du die Seite „Verlauf“ (samt laufender Downloads) und die Liste früherer Download-Ordner vor neugierigen Blicken verbergen. Nach dem Start der App und nach {n} Minuten Inaktivität fragt sie erneut nach dem Passwort.',
    'Indítás után és {n} perc tétlenség után újra jelszót kér.':
        'Fragt nach dem Start und nach {n} Minuten Inaktivität erneut nach dem Passwort.',
    'Finomhangolások és megújult Előzmények oldal: a futó letöltések és a kész videók egy helyen.':
        'Feinschliff und eine neu gestaltete Verlaufsseite: laufende Downloads und fertige Videos an einem Ort.',
    '●  Új':
        '●  Neu',
    'Hibák javítása':
        'Fehlerbehebungen',
    'Feltöltve: {x}':
        'Hochgeladen: {x}',
    'Hossz: {x}':
        'Länge: {x}',
    'Fájlméret':
        'Dateigröße',
    'Bugfixek, előzmények oldal finomhangolása.':
        'Fehlerbehebungen, Feinschliff der Verlaufsseite.',
    'Ablak átméretezéssel kapcsolatos hibák javítása':
        'Fehlerbehebungen beim Ändern der Fenstergröße',
    'Narancs':
        'Orange',
    'Piros':
        'Rot',
    'Lila':
        'Lila',
    'Hibajavítások, az első nyilvános kiadás.':
        'Fehlerbehebungen, die erste öffentliche Version.',
}
