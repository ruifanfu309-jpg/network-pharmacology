# -*- coding: utf-8 -*-
"""
TCMSP batch ADME lookup (OB/DL/BBB/Caco2/HL) — verified 2026-08.
Flow: candidate name -> tcmspsearch.php find MOL_ID -> molecule.php?qn=ID get ADME.
Input : 类药性筛选结果.csv (columns: VAR, Metabolite, SMILES, ..., 筛选结果)
Output: tcmsp_adme.csv
NOTE : parameter for detail page is qn=<molecule_ID> (NOT molID).
       token must be re-grabbed from tcmsp.php before each batch run.
"""
import csv, json, re, time, urllib.request, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent
CSV_FILE = BASE / "类药性筛选结果.csv"
OUT_CSV = BASE / "tcmsp_adme.csv"

def http_get(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            time.sleep(1.5)
    return ""

def get_token():
    html = http_get("https://tcmsp-e.com/tcmsp.php")
    m = re.search(r'name="token" value="([a-f0-9]{32})"', html)
    return m.group(1) if m else None

def search_molecule(token, name):
    q = urllib.parse.quote(name)
    html = http_get(f"https://tcmsp-e.com/tcmspsearch.php?qs=molecule_name&q={q}&token={token}")
    m = re.search(r'data:\s*\[(.*?)\]\s*,\s*pageSize', html, re.DOTALL)
    if not m:
        return []
    hits = []
    for mm in re.finditer(r'\{"MOL_ID":"(MOL\d+)","molecule_ID":"(\d+)","molecule_synonyms":"([^"]+)"\}', m.group(1)):
        hits.append((mm.group(1), mm.group(2), mm.group(3)))
    seen, uniq = set(), []
    for h in hits:
        if h[1] not in seen:
            seen.add(h[1]); uniq.append(h)
    return uniq

def get_adme(mol_id_num):
    html = http_get(f"https://tcmsp-e.com/molecule.php?qn={mol_id_num}")
    m = re.search(r'\{[^{}]*"ob"\s*:\s*"[^"]+"[^{}]*\}', html)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return {"OB": float(d.get("ob", 0)), "DL": float(d.get("dl", 0)),
                "MW": float(d.get("mw", 0)), "AlogP": float(d.get("alogp", 0)),
                "TPSA": float(d.get("tpsa", 0)), "Hdon": int(d.get("hdon", 0)),
                "Hacc": int(d.get("hacc", 0)), "BBB": float(d.get("bbb", 0)),
                "Caco2": float(d.get("caco2", 0)), "HL": float(d.get("halflife", 0)),
                "FASA": float(d.get("FASA", 0))}
    except (ValueError, TypeError):
        return None

def main():
    with open(CSV_FILE, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    cands = [r for r in rows if r["筛选结果"] == "✓ 候选活性成分"]
    print(f"候选成分: {len(cands)}")
    token = get_token()
    print(f"Token: {(token or 'FAIL')[:12]}...")
    results = []
    for i, r in enumerate(cands):
        name = r["Metabolite"]
        entry = {"VAR": r["VAR"], "name": name, "MOL_ID": "", "synonym": "",
                 "OB": "", "DL": "", "MW": "", "AlogP": "", "TPSA": "",
                 "Hdon": "", "Hacc": "", "BBB": "", "Caco2": "", "HL": "", "FASA": ""}
        qname = re.split(r"[,;]", name)[0].strip()
        hits = search_molecule(token, qname)
        if hits:
            best = next((h for h in hits if h[2].lower() == name.lower()), hits[0])
            entry["MOL_ID"], num_id, entry["synonym"] = best
            adme = get_adme(num_id)
            if adme:
                entry.update(adme)
        results.append(entry)
        print(f"  {i+1:2d}/{len(cands)} {'✓' if entry['OB'] != '' else '—'} {name[:38]:40s} MOL={entry['MOL_ID'] or '-':11s} OB={entry['OB']}")
        time.sleep(0.4)
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader(); w.writerows(results)
    found = sum(1 for r in results if r["OB"] != "")
    both = sum(1 for r in results if r["OB"] != "" and r["DL"] != "" and float(r["OB"]) >= 30 and float(r["DL"]) >= 0.18)
    print(f"\nTCMSP done: {found}/{len(cands)} found, OB>=30 & DL>=0.18: {both}")
    print(f"Output: {OUT_CSV}")

if __name__ == "__main__":
    main()
