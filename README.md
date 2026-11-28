# Boßel-Tracker mit automatischen Ergebnissen

Die App (`index.html`) läuft über GitHub Pages unter einer eigenen Adresse.
Ein Zeitplan holt sonntagabends und montags alle Spielpläne aus Kreis VIII Esens samt Ergebnissen
von bosselergebnis.info und legt sie als `daten.json` neben die App. Die App lädt diese Datei beim Öffnen.

## Inhalt

| Datei | Zweck |
|---|---|
| `index.html` | die App |
| `daten.json` | Spielpläne und Ergebnisse, wird automatisch erneuert |
| `scripts/update_data.py` | holt Spielpläne und Ergebnisse und schreibt `daten.json` |
| `ergebnisse.json`, `scripts/update_results.py` | ältere Fassung, wird nicht mehr gebraucht und kann gelöscht werden |
| `.github/workflows/update-results.yml` | Zeitplan und Veröffentlichung |

## Einrichten (einmalig, etwa 30 Minuten)

### Phase 1: privat testen

1. Auf github.com oben rechts **+ › New repository**: Name `bossel-tracker`, **Private**, README aus, kein .gitignore, keine Lizenz, **Create repository**.
2. **uploading an existing file** wählen und `index.html`, `ergebnisse.json` und `README.md` hochladen, **Commit changes**.
3. Das Skript anlegen: **Add file › Create new file**, als Namen `scripts/update_results.py` eintippen
   (der Schrägstrich legt den Ordner an), den Inhalt hineinkopieren, **Commit changes**.
4. Den Zeitplan genauso anlegen: **Add file › Create new file**, Name `.github/workflows/update-results.yml`,
   Inhalt hineinkopieren, **Commit changes**.
   (Der Ordner `.github` ist auf vielen Rechnern unsichtbar und wird beim Hochladen gern vergessen, deshalb dieser Weg.)
5. **Settings › Actions › General**: ganz unten bei **Workflow permissions** „**Read and write permissions**“ wählen, **Save**.
6. **Actions** öffnen, links **Ergebnisse aktualisieren**, rechts **Run workflow**.
   Der Teil „ergebnisse“ wird grün, „seite“ wird übersprungen, solange das Repository privat ist.
   Gab es neue Ergebnisse, erscheint im Code ein Eintrag „Ergebnisse aktualisiert“ an `ergebnisse.json`.

Hinweis: Eine Webseite (GitHub Pages) gibt es im kostenlosen Tarif nur für öffentliche Repositories.
In Phase 1 testest du deshalb den automatischen Abruf, die App selbst kannst du weiter über den Claude-Link nutzen.

### Phase 2: veröffentlichen und teilen

1. **Settings › General**, ganz unten **Change repository visibility › Change to public**.
2. **Settings › Pages**: bei **Source** „**Deploy from a branch**“ wählen, Branch **main**, Ordner **/ (root)**, **Save**.
3. Eine Datei `.nojekyll` anlegen (Add file › Create new file, Inhalt egal). GitHub veröffentlicht die Seite nach jeder Änderung selbst („pages build and deployment“ unter Actions).
4. Die App ist unter `https://DEIN-NAME.github.io/bossel-tracker/` erreichbar. Diesen Link kannst du weitergeben.

## Im Alltag

Der Zeitplan steht in `.github/workflows/update-results.yml` (Zeiten in UTC, also Winterzeit +1, Sommerzeit +2 Stunden):

| Wann | Was |
|---|---|
| Samstag und Sonntag, ca. 11 bis 21 Uhr, alle 30 Minuten | Schnellmodus: nur die Spieltage dieses Wochenendes |
| Montag früh und Montag nachmittags | Spieltage der letzten drei Wochen, für spät eingetragene Ergebnisse |
| Mittwoch nachts | alle Spielpläne komplett, falls sich Termine geändert haben |

- Die Seite wird nur neu veröffentlicht, wenn sich wirklich etwas geändert hat: GitHub veröffentlicht jede Änderung am Branch main automatisch.
- GitHub startet geplante Läufe manchmal mit einigen Minuten Verspätung.
- Sofort aktualisieren: **Actions › Ergebnisse aktualisieren › Run workflow**.
- Die App zeigt auf der Startseite „Stand“ mit Datum und Uhrzeit des letzten Abrufs. Sie lädt neue Daten beim Öffnen,
  wenn sie wieder in den Vordergrund kommt und alle 10 Minuten, solange sie offen ist.
- Ohne Internet nutzt die App die zuletzt geladenen Daten.

## Neue App-Version einspielen

`index.html` im Repository öffnen, **Stift-Symbol › …** bzw. einfach die neue Datei per
**Add file › Upload files** mit gleichem Namen hochladen. Die Seite wird danach automatisch neu veröffentlicht.

## Neue Saison oder weitere Kreise

In `scripts/update_data.py` oben `SEASON` (z. B. `"2027-2028"`) bzw. `KREISE` anpassen,
z. B. `["ese", "wtm"]` für Esens und Wittmund. Das Skript findet die Ligen selbst.
Komplette Spielpläne holt es höchstens einmal pro Woche, sonst nur die letzten Spieltage.

## Hinweis

Bitte frag beim Betreiber von bosselergebnis.info kurz nach, ob der automatische Abruf in Ordnung ist.
Das Skript holt die kompletten Spielpläne höchstens einmal pro Woche (rund 800 Abrufe), sonst nur die Spieltage der letzten drei Wochen (rund 150 Abrufe), jeweils mit einer kleinen Pause dazwischen.

## Rechtliches

© 2026 Till Zaydowicz. Alle Rechte vorbehalten.

Die Nutzung der App über ihre Webadresse ist ausdrücklich erlaubt. Kopieren, Verändern, Weitergeben
oder Weiterentwickeln des Programmcodes, der Skripte und des Designs ist ohne schriftliche Zustimmung
nicht gestattet. Siehe `LICENSE`.

Spielpläne und Ergebnisse stammen von bosselergebnis.info. Die Vereinswappen sind Eigentum der jeweiligen Vereine.
