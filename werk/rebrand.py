#!/usr/bin/env python3
"""Macht aus dem Originalprogramm die Werk-Ausgabe (Name, Logos, Links).

Läuft im Build direkt nach dem Auschecken und verändert nur den Arbeitsordner;
im Repository selbst bleibt der Originalcode unangetastet. So lässt sich der
Fork jederzeit mit dem Original abgleichen, ohne Konflikte.

Jede Ersetzung muss mindestens einmal treffen. Trifft eine nicht mehr, hat sich
das Original an dieser Stelle geändert: das Skript bricht ab und nennt die Stelle,
statt still ein halb umbenanntes Programm zu bauen.

Aufruf:  python3 werk/rebrand.py            (im Wurzelordner des Repositories)
         python3 werk/rebrand.py --check    (nur prüfen, nichts schreiben)
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WERK = ROOT / "werk"
CFG = json.loads((WERK / "werk.json").read_text(encoding="utf-8"))
CHECK = "--check" in sys.argv

NAME, ORIGINAL, SUITE = CFG["name"], CFG["original"], CFG["suite"]
GITHUB, UPSTREAM = CFG["github"], CFG["upstream"]
OWNER = GITHUB.split("/")[0]
ICON, APP_ID = CFG["icon_base"], CFG["app_id"]
ORIGINAL_LC = ORIGINAL.lower()

# Ordner mit Quelltext und Paketierung. Lizenztexte und Urheberhinweise bleiben, wie sie sind.
TEXT_DIRS = ["crates", "apps", "xtask", "packaging"]
KEEP = ("LICENSE", "LICENCE", "NOTICE", "ATTRIBUTION", "OFL")

problems: list[str] = []


def read(path: pathlib.Path) -> str:
    """Liest UTF-8, ohne Zeilenenden umzuwandeln (wichtig beim Build unter Windows)."""
    return path.read_bytes().decode("utf-8")


def text_files():
    for d in TEXT_DIRS:
        for p in sorted((ROOT / d).rglob("*")):
            if not p.is_file() or p.name.upper().startswith(KEEP) or "target" in p.parts:
                continue
            try:
                yield p, read(p)
            except (UnicodeDecodeError, OSError):
                continue  # Binärdatei


def write(path: pathlib.Path, text: str):
    if not CHECK:
        path.write_bytes(text.encode("utf-8"))


def replace_everywhere(pairs, what):
    """Ersetzt Textstellen in allen Quelldateien; jedes Paar muss irgendwo treffen."""
    hits = {old: 0 for old, _ in pairs}
    for path, text in text_files():
        new = text
        for old, repl in pairs:
            n = new.count(old)
            if n:
                hits[old] += n
                new = new.replace(old, repl)
        if new != text:
            write(path, new)
    for old, n in hits.items():
        print(f"  {n:5d} × {old!r}")
        if n == 0:
            problems.append(f"{what}: {old!r} kommt im Original nicht mehr vor")


def replace_in(rel, old, new, what):
    path = ROOT / rel
    text = read(path) if path.is_file() else ""
    if old not in text:
        problems.append(f"{what}: Stelle in {rel} nicht gefunden")
        return
    write(path, text.replace(old, new))
    print(f"  {rel}: {what}")


# Sätze, die auf ArtCraft-Angebote (Discord, Website) verweisen, mit ihrem Ersatz.
# Englisch ist die Ausgangssprache des Programms; Deutsch wird unten nachgetragen.
PHRASES = [
    ("Join the ArtCraft Discord", "Help and feedback", "Hilfe und Feedback"),
    ("Join our Discord", "Report a problem", "Problem melden"),
    ("Join the ArtCraft community", "Questions or problems?", "Fragen oder Probleme?"),
    (
        "Get help, share feedback and follow development on Discord.",
        "Report a problem or follow development on GitHub.",
        "Melde ein Problem oder verfolge die Entwicklung auf GitHub.",
    ),
    ("ArtCraft website", f"{SUITE} on GitHub", f"{SUITE} auf GitHub"),
]


def fix_catalogs():
    """Übersetzungstabellen: Zeilen der ersetzten Sätze entfernen, Deutsch neu eintragen."""
    old_sources = {old for old, _, _ in PHRASES}
    i18n = sorted(ROOT.glob("crates/*/src/i18n/*.tsv"))
    if not i18n:
        problems.append("Übersetzungen: keine .tsv-Dateien gefunden")
    for path in i18n:
        lines = read(path).split("\n")
        kept = []
        for line in lines:
            cols = line.rstrip("\r").split("\t")
            if len(cols) >= 3 and not line.startswith("#") and cols[1] in old_sources:
                continue
            kept.append(line)
        if path.name == "de.tsv":
            have = {l.split("\t")[1] for l in kept if l.count("\t") >= 2 and not l.startswith("#")}
            eol = "\r" if kept and kept[0].endswith("\r") else ""
            while kept and kept[-1].strip() == "":
                kept.pop()
            for _, new, german in PHRASES:
                if new not in have:
                    kept.append(f"\t{new}\t{german}{eol}")
            kept.append("")
        write(path, "\n".join(kept))
    print(f"  {len(i18n)} Übersetzungstabellen bereinigt")


def copy(src_rel, dst_rel):
    src, dst = WERK / "icons" / src_rel, ROOT / dst_rel
    if not src.is_file():
        problems.append(f"Icons: {src_rel} fehlt in werk/icons")
        return
    if not dst.is_file():
        problems.append(f"Icons: Ziel {dst_rel} gibt es im Original nicht mehr")
        return
    if not CHECK:
        shutil.copyfile(src, dst)


def main():
    print(f"{ORIGINAL} → {NAME}{'  (nur Prüfung)' if CHECK else ''}")

    print("Übersetzungen:")
    fix_catalogs()

    print("Name und Verweise:")
    replace_everywhere(
        [(old, new) for old, new, _ in PHRASES]
        + [
            ("https://discord.gg/artcraft", f"https://github.com/{GITHUB}/issues"),
            (f"https://getartcraft.com/apps/{ORIGINAL_LC}", f"https://github.com/{GITHUB}/releases"),
            ("https://getartcraft.com", f"https://github.com/{OWNER}"),
            # Auch die eingebaute Update-Prüfung schaut danach in den eigenen Releases nach.
            (f"github.com/repos/{UPSTREAM}/", f"github.com/repos/{GITHUB}/"),
            (f"https://github.com/{UPSTREAM}", f"https://github.com/{GITHUB}"),
            ('alt_text("ArtCraft")', f'alt_text("{SUITE}")'),
            (ORIGINAL, NAME),
        ],
        "Ersetzung",
    )

    print("Einzelstellen:")
    # Knopf oben rechts in der Titelleiste (zwei Stellen: Breite messen und zeichnen).
    chrome = "crates/ui-egui/src/chrome.rs"
    replace_in(chrome, '"messages-square", "Discord"', '"messages-square", "Hilfe"', "Hilfe-Knopf")
    replace_in(chrome, 'layout_no_wrap("Discord".into()', 'layout_no_wrap("Hilfe".into()', "Breite des Hilfe-Knopfs")
    replace_in(f"apps/{ORIGINAL_LC}-cli/src/main.rs", '"Discord: {}', '"Hilfe: {}', "Hilfe-Zeile der Kommandozeile")
    # Herkunft bleibt im Über-Dialog sichtbar: das verlangt der Anstand und hilft bei Fehlersuche.
    replace_in(
        "crates/ui-egui/src/dialogs.rs",
        '"Rendering: hayro',
        f'"Based on {ORIGINAL} by the ArtCraft team · Rendering: hayro',
        "Herkunftshinweis im Über-Dialog",
    )

    print("Icons und Marke:")
    icon_dir = "assets/app-icon"
    copy("icon.svg", f"{icon_dir}/{ICON}.svg")
    copy("icon-small.svg", f"{icon_dir}/{ICON}-small.svg")
    copy("icon-1024.png", f"{icon_dir}/{ICON}-1024.png")
    copy("icon.ico", f"{icon_dir}/{ICON}.ico")
    copy("icon.svg", f"{icon_dir}/hicolor/scalable/apps/{APP_ID}.svg")
    for n in (16, 24, 32, 48, 64, 128, 256, 512):
        copy(f"hicolor/{n}x{n}.png", f"{icon_dir}/hicolor/{n}x{n}/apps/{APP_ID}.png")
    # Das Programm bettet die Marke der Suite aus docs/brand ein; dort steht danach die eigene.
    copy("mark.svg", "docs/brand/artcraft-mark.svg")
    copy("logo.svg", "docs/brand/artcraft-logo.svg")
    copy("logo-white.svg", "docs/brand/artcraft-logo-white.svg")
    print("  Icons ersetzt")

    notice = ROOT / "NOTICE"
    addition = (
        f"\n\n{NAME}\n"
        f"{NAME} is a modified version of {ORIGINAL} (https://github.com/{UPSTREAM}), renamed and\n"
        f"repackaged by {OWNER} (https://github.com/{GITHUB}). It is not made, sponsored or endorsed by\n"
        f"the ArtCraft Team. The original copyright notice and licenses above continue to apply.\n"
    )
    if notice.is_file():
        text = read(notice)
        if addition.strip() not in text.replace("\r", ""):
            write(notice, text.rstrip("\n") + addition)
        print("  NOTICE ergänzt")
    else:
        problems.append("NOTICE fehlt im Original")

    if problems:
        print("\nABBRUCH, das Original hat sich geändert:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)
    print("Fertig.")


main()
