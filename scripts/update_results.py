#!/usr/bin/env python3
"""Holt die Ergebnisse der eingetragenen Spielpläne von bosselergebnis.info
und schreibt sie als ergebnisse.json neben die App (index.html).

Läuft automatisch über GitHub Actions (.github/workflows/update-results.yml),
kann aber auch von Hand gestartet werden:  python scripts/update_results.py
Benötigt nur Python 3, keine zusätzlichen Pakete.
"""
import datetime
import hashlib
import json
import os
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

# Spielpläne auf bosselergebnis.info. Für eine neue Saison oder weitere Klassen
# hier die Spielplan-ID, Klasse, Schoet-Länge und Anzahl der Spieltage anpassen.
PLANS = [
    {"id": 914, "group": "M", "klasse": "I", "len": 150, "days": 18},   # Kreisliga Männer I, Kreis VIII Esens
    {"id": 957, "group": "JM", "klasse": "F", "len": 50, "days": 14},   # 1. Kreisliga männl. Jugend F, Staffel II
]

BASE = "https://bosselergebnis.info/ajax/ergebnis/"
HEADERS = {"User-Agent": "Bossel-Tracker Vereinsapp (Ergebnisabruf, wenige Male pro Woche)"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ergebnisse.json")


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def day_games(plan_id, n, total):
    # Die Seite liefert Spieltag n über "vorheriger von n+1" bzw. beim letzten Spieltag über "nächster von n-1".
    if n < total:
        return get_json(f"{BASE}showPreviousSpieltag?spielplan={plan_id}&nummer={n + 1}")
    return get_json(f"{BASE}showNextSpieltag?spielplan={plan_id}&nummer={n - 1}")


def parse_erg(text):
    """'-7,095' -> (-1, 7, 95): Vorzeichen aus Sicht der Heimmannschaft, Schoet, Meter."""
    t = (text or "").strip()
    sign = -1 if t.startswith("-") else 1
    t = t.lstrip("+-")
    s, m = (t.split(",") + ["0"])[:2]
    return sign, int(s or 0), int(m or 0)


def to_record(plan, g):
    rows = []
    for gr in g.get("gruppenergebnisse") or []:
        e = gr.get("ergebnis")
        if not e or e == "---":
            continue
        sign, s, m = parse_erg(e)
        kind = "G" if "gummi" in (gr.get("name") or "").lower() else "H"
        rows.append({"k": kind, "w": "L" if sign > 0 else "R", "s": s, "m": m})
    res = {"L": {"s": 0, "m": 0}, "R": {"s": 0, "m": 0}}
    for r in rows:
        res[r["w"]]["s"] += r["s"]
        res[r["w"]]["m"] += r["m"]
    if not rows:
        sign, s, m = parse_erg(g.get("ergebnis"))
        res["L" if sign > 0 else "R"] = {"s": s, "m": m}
    d, mth, y = g["datum"].split(".")
    return {
        "id": "imp-" + str(g["paarungsid"]), "imp": 1, "st": int(g["nummer"]),
        "date": f"{y}-{mth}-{d}", "group": plan["group"], "klasse": plan["klasse"], "len": plan["len"],
        "teams": {"L": g["heim"], "R": g["gast"]}, "res": res, "rows": rows,
        "note": g.get("bemerkung") or "",
    }


def main():
    records, failures = [], 0
    for plan in PLANS:
        for n in range(1, plan["days"] + 1):
            try:
                games = day_games(plan["id"], n, plan["days"])
            except Exception as exc:  # Netzwerkfehler oder unerwartete Antwort
                failures += 1
                print(f"Spielplan {plan['id']}, Spieltag {n}: Fehler {exc}", file=sys.stderr)
                continue
            for g in games:
                if g.get("heim") == "Spielfrei" or g.get("gast") == "Spielfrei":
                    continue
                if not g.get("ergebnis") or g["ergebnis"] == "---":
                    continue
                records.append(to_record(plan, g))
            time.sleep(0.5)  # die Seite schonen
    if not records:
        print("Keine Ergebnisse erhalten, ergebnisse.json bleibt unverändert.", file=sys.stderr)
        sys.exit(1)
    records.sort(key=lambda r: (r["group"], r["klasse"], r["st"], r["id"]))
    body = json.dumps(records, ensure_ascii=False, sort_keys=True)
    version = hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]
    try:
        old = json.load(open(OUT, encoding="utf-8"))
        if old.get("version") == version:
            print(f"Keine neuen Ergebnisse ({len(records)} Spiele).")
            return
    except (OSError, ValueError):
        pass
    now = datetime.datetime.now(ZoneInfo("Europe/Berlin"))
    data = {"version": version, "stand": now.strftime("%d.%m.%Y"), "abgerufen": now.isoformat(timespec="minutes"), "records": records}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"ergebnisse.json geschrieben: {len(records)} Spiele, Version {version}" + (f", {failures} Abruffehler" if failures else ""))


if __name__ == "__main__":
    main()
