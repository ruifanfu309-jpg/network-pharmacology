# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 第1步: PubChem 批量查询结构 (138 个全查)
改进: 逗号修正名重试 + 进度保存(断点续跑)
"""
import csv, json, time, urllib.request, urllib.parse, re
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"
CSV_FILE = DATA / "代谢物列表.csv"
OUT = DATA / "step1_structures.json"

def get(url, retries=2):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            if i == retries - 1:
                return None
            time.sleep(1.5)

def clean_name(name):
    """去引号变体, 但保留逗号(逗号是化学名一部分)"""
    n = name.replace("''", "").replace('"', "")
    return n.strip()

def query_pubchem(name):
    """PubChem 名称查询 → SMILES"""
    q = urllib.parse.quote(name)
    r = get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/property/CanonicalSMILES/TXT")
    if r and not r.startswith("<!") and r.strip() and "Status" not in r[:50]:
        return r.strip().split("\n")[0]
    return None

def main():
    with open(CSV_FILE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"共 {len(rows)} 个代谢物")

    # 断点续跑
    done = {}
    if OUT.exists():
        done = {r["VAR"]: r for r in json.loads(OUT.read_text(encoding="utf-8"))}

    results = []
    for i, row in enumerate(rows, 1):
        var = row["VAR编号"]
        if var in done:
            results.append(done[var])
            continue
        name = row["Metabolite"].strip()
        entry = {"VAR": var, "ID": row["ID"], "name": name, "smiles": None, "source": None}

        # 1. 原名
        smi = query_pubchem(name)
        # 2. 清理名(去引号)
        if not smi:
            cn = clean_name(name)
            if cn != name:
                smi = query_pubchem(cn)
                entry["source"] = "PubChem-clean"
        if smi:
            entry["smiles"] = smi
            entry["source"] = entry["source"] or "PubChem"

        results.append(entry)
        if i % 10 == 0:
            OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {i}/{len(rows)} ... 命中 {sum(1 for r in results if r['smiles'])}")
        time.sleep(0.3)

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    found = sum(1 for r in results if r["smiles"])
    print(f"\n✅ 完成: {found}/{len(rows)} 查到结构")
    missing = [r for r in results if not r["smiles"]]
    if missing:
        print("未查到:")
        for r in missing:
            print(f"  {r['VAR']} {r['name'][:45]}")

if __name__ == "__main__":
    main()
