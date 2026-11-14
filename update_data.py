#!/usr/bin/env python3
"""Holt Spielpläne und Ergebnisse von bosselergebnis.info und schreibt sie als
daten.json neben die App (index.html).

- Welche Ligen: alle Spielpläne, die auf der Kreisseite (KREISE) gelistet sind.
- Schonend: Komplette Spielpläne höchstens alle FULL_EVERY_DAYS Tage, sonst nur
  die Spieltage der letzten RESULT_WINDOW_DAYS Tage (dort ändern sich Ergebnisse).
- Komplett neu laden:  python scripts/update_data.py --full
Benötigt nur Python 3 (3.9+), keine zusätzlichen Pakete.
"""
import datetime
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

SEASON = "2026-2027"
KREISE = ["ese"]             # Kreis VIII Esens. Weitere Kreise z. B. "aur", "nor", "wtm", "fri"
FULL_EVERY_DAYS = 7          # kompletter Abruf aller Spieltage höchstens so oft
RESULT_WINDOW_DAYS = 21      # Spieltage in diesem Zeitraum werden bei jedem Lauf neu geholt
PAUSE = 0.4                  # Sekunden zwischen zwei Abrufen

SITE = "https://bosselergebnis.info"
API = SITE + "/ajax/ergebnis/"
HEADERS = {"User-Agent": "Bossel-Tracker Vereinsapp (Spielplan- und Ergebnisabruf, wenige Male pro Woche)"}
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "daten.json")
TZ = ZoneInfo("Europe/Berlin")
ROMAN = {"i": "I", "ii": "II", "iii": "III", "iv": "IV", "v": "V"}


class NoDay(Exception):
    pass


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    time.sleep(PAUSE)
    return text


def fetch_json(url):
    text = fetch(url)
    try:
        return json.loads(text)
    except ValueError:
        raise NoDay(url)


def schoet_len(group, klasse):
    if group == "M":
        return 150
    if group == "F":
        return 100
    if klasse == "A":
        return 150 if group == "JM" else 100
    if klasse == "E":
        return 75
    if klasse == "F":
        return 50
    return 100


def classify(slug):
    """'m_i_kreisliga' -> ('M', 'I'), 'w_e_kreisliga' -> ('JW', 'E')"""
    m = re.match(r"([mw])_([a-z]+)_", slug)
    if not m:
        return None, None
    sex, cl = m.group(1), m.group(2)
    if cl in ROMAN:
        return ("M" if sex == "m" else "F"), ROMAN[cl]
    if len(cl) == 1 and cl in "abcdef":
        return ("JM" if sex == "m" else "JW"), cl.upper()
    return None, None


def discover():
    leagues = {}
    for kreis in KREISE:
        page = fetch(f"{SITE}/{SEASON}/{kreis}")
        kreis_name = (re.findall(r"Spielpläne für Vereine aus dem ([^<]+)", page) or [kreis])[0].strip()
        for href, title, org in re.findall(
                r'<a class="ui card" href="(https://bosselergebnis\.info/' + re.escape(SEASON) + r'/[a-z]+/liga/[^"]+)"\s*>.*?'
                r'<div class="header">(.*?)</div>.*?<span class="category">(.*?)</span>', page, re.S):
            href = href.split("?")[0]
            if href not in leagues:
                leagues[href] = {"url": href, "title": html.unescape(title).strip(), "org": html.unescape(org).strip(), "kreis": kreis_name}
    return list(leagues.values())


def parse_erg(text):
    t = (text or "").strip()
    sign = -1 if t.startswith("-") else 1
    s, m = (t.lstrip("+-").split(",") + ["0"])[:2]
    return sign, int(s or 0), int(m or 0)


def iso(datum):
    d, m, y = datum.split(".")
    return f"{y}-{m}-{d}"


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
    return {
        "id": "imp-" + str(g["paarungsid"]), "imp": 1, "st": int(g["nummer"]), "date": iso(g["datum"]),
        "group": plan["group"], "klasse": plan["klasse"], "len": plan["len"], "plan": plan["id"],
        "teams": {"L": g["heim"], "R": g["gast"]}, "res": res, "rows": rows, "note": g.get("bemerkung") or "",
    }


def get_day(be_id, n, last=None):
    """Spieltag n: 'vorheriger von n+1', beim letzten Spieltag 'nächster von n-1'."""
    if last is not None and n == last and n > 1:
        return fetch_json(f"{API}showNextSpieltag?spielplan={be_id}&nummer={n - 1}")
    return fetch_json(f"{API}showPreviousSpieltag?spielplan={be_id}&nummer={n + 1}")


def fetch_all_days(be_id):
    days = {}
    n = 1
    while n < 60:
        try:
            games = get_day(be_id, n)
        except NoDay:
            if n == 1:
                break
            # n ist der letzte Spieltag
            try:
                games = fetch_json(f"{API}showNextSpieltag?spielplan={be_id}&nummer={n - 1}")
                if games and int(games[0]["nummer"]) == n:
                    days[n] = games
            except NoDay:
                pass
            break
        if not games or int(games[0]["nummer"]) != n:
            break
        days[n] = games
        n += 1
    return days


def plan_from_days(meta, be_id, days):
    group, klasse = meta["group"], meta["klasse"]
    plan = {
        "id": "be" + str(be_id), "beId": be_id, "slug": meta["slug"], "url": meta["url"],
        "title": meta["title"], "label": meta["title"], "org": meta["org"],
        "sub": "Saison " + SEASON.replace("-", "/") + " · " + meta["org"],
        "group": group, "klasse": klasse, "len": schoet_len(group, klasse),
        "vier": "(4er)" in meta["title"] or "4er" in meta["title"], "days": [],
    }
    for n in sorted(days):
        games = days[n]
        plan["days"].append({"n": n, "d": iso(games[0]["datum"]), "g": [[g["heim"], g["gast"]] for g in games]})
    return plan


def main():
    full = "--full" in sys.argv
    now = datetime.datetime.now(TZ)
    today = now.date()
    try:
        old = json.load(open(OUT, encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    old_plans = {p["url"]: p for p in old.get("plans", [])}
    old_records = {r["id"]: r for r in old.get("records", [])}
    last_full = old.get("vollabruf")
    need_full = full or not old_plans or not last_full or (today - datetime.date.fromisoformat(last_full)).days >= FULL_EVERY_DAYS

    leagues = discover()
    print(f"{len(leagues)} Ligen gefunden ({'kompletter Abruf' if need_full else 'nur aktuelle Spieltage'})")
    plans, records, errors = [], dict(old_records), 0
    for lg in leagues:
        slug = lg["url"].rsplit("/", 1)[1]
        group, klasse = classify(slug)
        if not group:
            print(f"  übersprungen (Klasse unbekannt): {lg['title']}")
            continue
        meta = dict(lg, slug=slug, group=group, klasse=klasse)
        prev = old_plans.get(lg["url"])
        try:
            if need_full or not prev:
                page = fetch(lg["url"])
                ids = re.findall(r'"id":(\d+),"datum"', page)
                if not ids:
                    print(f"  keine Spielplan-Nummer: {lg['title']}")
                    continue
                be_id = int(ids[0])
                days = fetch_all_days(be_id)
                if not days:
                    print(f"  keine Spieltage: {lg['title']}")
                    continue
                plan = plan_from_days(meta, be_id, days)
                for games in days.values():
                    for g in games:
                        if "Spielfrei" in (g.get("heim"), g.get("gast")) or not g.get("ergebnis") or g["ergebnis"] == "---":
                            continue
                        records["imp-" + str(g["paarungsid"])] = to_record(plan, g)
            else:
                plan = dict(prev, title=meta["title"], label=meta["title"], org=meta["org"])
                last = plan["days"][-1]["n"] if plan["days"] else None
                for d in plan["days"]:
                    dd = datetime.date.fromisoformat(d["d"])
                    if dd > today or (today - dd).days > RESULT_WINDOW_DAYS:
                        continue
                    games = get_day(plan["beId"], d["n"], last)
                    for g in games:
                        if "Spielfrei" in (g.get("heim"), g.get("gast")) or not g.get("ergebnis") or g["ergebnis"] == "---":
                            continue
                        records["imp-" + str(g["paarungsid"])] = to_record(plan, g)
            plans.append(plan)
            print(f"  {plan['title']}: {len(plan['days'])} Spieltage")
        except Exception as exc:
            errors += 1
            print(f"  Fehler bei {lg['title']}: {exc}", file=sys.stderr)
            if prev:
                plans.append(prev)

    if not plans:
        print("Keine Spielpläne erhalten, daten.json bleibt unverändert.", file=sys.stderr)
        sys.exit(1)
    plan_ids = {p["id"] for p in plans}
    recs = sorted((r for r in records.values() if r.get("plan") in plan_ids), key=lambda r: (r["plan"], r["st"], r["id"]))
    body = json.dumps({"plans": plans, "records": recs}, ensure_ascii=False, sort_keys=True)
    version = hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]
    if old.get("version") == version and not need_full:
        print(f"Keine Änderungen ({len(plans)} Spielpläne, {len(recs)} Ergebnisse).")
        return
    data = {
        "version": version, "stand": now.strftime("%d.%m.%Y"), "abgerufen": now.isoformat(timespec="minutes"),
        "saison": SEASON, "kreise": KREISE,
        "vollabruf": today.isoformat() if need_full else last_full,
        "plans": plans, "records": recs,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"daten.json geschrieben: {len(plans)} Spielpläne, {len(recs)} Ergebnisse, Version {version}" + (f", {errors} Fehler" if errors else ""))


if __name__ == "__main__":
    main()
