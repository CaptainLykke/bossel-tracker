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
2. **Settings › Pages**: bei **Source** „**GitHub Actions**“ auswählen.
3. **Actions › Ergebnisse aktualisieren › Run workflow**. Jetzt laufen beide Teile, „seite“ zeigt am Ende den Link.
4. Die App ist unter `https://DEIN-NAME.github.io/bossel-tracker/` erreichbar. Diesen Link kannst du weitergeben.

## Im Alltag

- Ergebnisse werden **sonntags um 20 Uhr** (Sommerzeit 21 Uhr) und **montags nachmittags** geholt.
  Die Zeiten stehen in `update-results.yml` in den `cron`-Zeilen (in UTC).
- Sofort aktualisieren: **Actions › Ergebnisse aktualisieren › Run workflow**.
- Die App zeigt auf der Startseite „Stand“ mit dem Datum des letzten Abrufs.
- Ohne Internet oder ohne `ergebnisse.json` nutzt die App die eingebauten Ergebnisse.

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
