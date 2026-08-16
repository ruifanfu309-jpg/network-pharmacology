# -*- coding: utf-8 -*-
"""
Network pharmacology Step 1: batch PubChem name -> SMILES lookup.
Reads 代谢物列表.csv (columns: 序号,VAR编号,ID,Metabolite), writes pubchem_smiles.json.

KEY: PubChem PUG REST JSON returns the key `ConnectivitySMILES`, NOT `CanonicalSMILES`.
Using CanonicalSMILES silently returns empty smiles (0% hit rate). Do not change it back.

Run with uv-managed venv python (NOT Hermes bundled venv):
    "/c/Users/<user>/AppData/Local/hermes/hermes-agent/.venv/Scripts/python.exe" step1_pubchem.py
"""
import csv, json, time, urllib.request, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent
CSV_FILE = BASE / "代谢物列表.csv"
OUT_JSON = BASE / "pubchem_smiles.json"


def clean_name(name: str) -> str:
    """Clean compound name to improve PubChem matching.
    Do NOT split on commas -- commas are part of chemical names
    (e.g. 'Glycerol 1,3-Dihexadecanoate'). Splitting yields a silently WRONG structure."""
    n = name.strip()
    n = n.replace("''", "").replace('"', "")  # strip double primes/quotes; keep single-quote primes (2'-Hydroxy is legal)
    return n.strip()


def query_pubchem(name: str, retries: int = 3) -> dict:
    candidates = [name, clean_name(name)]
    for cand in candidates:
        q = urllib.parse.quote(cand)
        url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/"
               f"property/ConnectivitySMILES,MolecularFormula,MolecularWeight/JSON")
        for _ in range(retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode())
                    props = data["PropertyTable"]["Properties"][0]
                    return {"name": name, "cid": props.get("CID"),
                            "smiles": props.get("ConnectivitySMILES", ""),
                            "formula": props.get("MolecularFormula", ""),
                            "mw": props.get("MolecularWeight", "")}
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    break  # try next candidate name
                time.sleep(2)
            except Exception:
                time.sleep(2)
    return {"name": name, "error": "not_found"}


def main():
    with open(CSV_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"共 {len(rows)} 个代谢物")

    results = []
    for i, row in enumerate(rows):
        name = row["Metabolite"].strip()
        res = query_pubchem(name)
        res["VAR"] = row["VAR编号"]
        res["ID"] = row["ID"]
        results.append(res)
        if (i + 1) % 10 == 0:
            print(f"  已查询 {i+1}/{len(rows)}")
        time.sleep(0.3)  # rate limit

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if r.get("smiles"))
    print(f"\nPubChem 查询完成: {ok}/{len(rows)} 查到结构 -> {OUT_JSON}")
    print(f"未找到 {len(rows)-ok} 个（脂质缩写/谷胱甘肽结合物/含特殊字符名属预期缺失）")


if __name__ == "__main__":
    main()
