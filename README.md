# Partylichter

Stimmungslichter für den Beamer – für Unterricht, Schulfeste und Partys.

**App öffnen:** https://thmsupt.github.io/partylichter/

## Was die App kann

- 7 Szenen: Farbverlauf, Sternenhimmel, Discokugel, Scheinwerfer, Farb-Puls, Wellen, Lagerfeuer
- 3 Modi: Takt (tippen oder BPM einstellen), Mikrofon, Automatik
- Freeze mit Stopp-Schild und automatischer **Licht-Stopptanz** mit Gong
- Bedienung über Tasten, Präsentations-Klicker oder eine Leiste, die sich ausblendet
- Installierbar als App und offline nutzbar

## Sicherheit

Kein Stroboskop. Lichtwechsel sind fest auf höchstens 3 pro Sekunde begrenzt, Helligkeit ändert sich nur weich, Szenenwechsel werden überblendet. Alle Szenen werden automatisch gegen die Blitz-Grenzwerte der WCAG 2.3.1 geprüft (`tests/flashcheck.py`).

## Datenschutz

Keine Datenübertragung, keine Cookies, kein Tracking. Das Mikrofon wird nur lokal ausgewertet. Einstellungen bleiben im Browser des jeweiligen Geräts.

## Tasten

| Taste | Funktion |
|---|---|
| 1–7, ← → | Szene wählen |
| 8, F, B, . | Freeze |
| Leertaste | Takt tippen |
| ↑ ↓ | Tempo ±1 (Shift ±5) |
| T / M / A | Takt / Mikrofon / Automatik |
| S | Licht-Stopptanz an/aus |
| V | Vollbild |
| H | Hilfe |

## Neue Version veröffentlichen

Nach Änderungen an `index.html` in `sw.js` die Zeile `VERSION` hochzählen, damit installierte Apps das Update laden.
