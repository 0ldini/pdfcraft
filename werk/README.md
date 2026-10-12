# Werk-Ausgabe: Blattwerk

Dieser Ordner macht aus dem Originalprogramm PdfCraft die eigene Ausgabe **Blattwerk**.
Der Originalcode im Repository bleibt unverändert; die Umbenennung passiert erst beim Bauen.

## Was hier liegt

| Datei | Zweck |
|---|---|
| `werk.json` | Name der Ausgabe, GitHub-Adresse des Forks |
| `rebrand.py` | ersetzt Name, Logos und Links im Arbeitsordner |
| `icons/` | App-Icon in allen Grössen und die Werkbank-Marke |
| `../.github/workflows/werk-release.yml` | baut Windows, Linux und Browser und veröffentlicht ein Release |

## Neue Version herausgeben

1. Auf GitHub im Fork **Sync fork** klicken (holt die Neuerungen des Originals).
2. Reiter **Actions** → **Werk-Release** → **Run workflow**.
3. Nach dem Build erscheint das Release; der Werkbank-Launcher bietet es als Update an.

Bricht `rebrand.py` mit «das Original hat sich geändert» ab, nennt es die Stelle, die im
Original anders geworden ist. Dann muss die passende Ersetzung im Skript angepasst werden.

## Was sich gegenüber dem Original ändert

- Anzeigename PdfCraft → Blattwerk, eigenes App-Icon.
- ArtCraft-Logo, Discord-Knopf und Links zu getartcraft.com sind ersetzt (Markenbedingungen
  in `docs/brand/LICENSE-brand.txt`); Hilfe-Links führen zu diesem Fork.
- Der Über-Dialog nennt weiterhin die Herkunft; Lizenzen und `NOTICE` bleiben erhalten.
- Programmdatei (`pdfcraft`) und interne Kennungen bleiben gleich, damit Updates des
  Originals ohne Konflikte übernommen werden können.

## Lizenz

Wie das Original: MIT oder Apache-2.0. Blattwerk ist kein Produkt des ArtCraft-Teams.
