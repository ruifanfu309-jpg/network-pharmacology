# -*- coding: utf-8 -*-
"""
Network pharmacology Step 2: RDKit Lipinski (类药性) screening.
Reads pubchem_smiles.json (from step1_pubchem.py), writes 类药性筛选结果.csv (utf-8-sig, Excel-safe).

Requires: uv pip install rdkit pandas
"""
import json, csv
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Crippen

BASE = Path(__file__).parent
IN_JSON = BASE / "pubchem_smiles.json"
OUT_CSV = BASE / "类药性筛选结果.csv"


def lipinski(mol):
    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    rotb = Descriptors.NumRotatableBonds(mol)
    tpsa = Descriptors.TPSA(mol)
    violations = sum([
        mw > 500, logp > 5, hbd > 5, hba > 10, rotb > 10,
    ])
    return {"MW": round(mw, 2), "LogP": round(logp, 2), "HBD": hbd, "HBA": hba,
            "RotB": rotb, "TPSA": round(tpsa, 1), "Violations": violations}


def main():
    with open(IN_JSON, encoding="utf-8") as f:
        results = json.load(f)

    rows, found = [], 0
    for r in results:
        name, smiles = r.get("name", ""), r.get("smiles", "")
        base = {"VAR": r.get("VAR", ""), "ID": r.get("ID", ""), "Metabolite": name, "SMILES": smiles}
        if not smiles:
            rows.append({**base, "查库状态": "未找到", "MW": "", "LogP": "", "HBD": "", "HBA": "",
                         "RotB": "", "TPSA": "", "Violations": "", "筛选结果": "✗ 无结构"})
            continue
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            rows.append({**base, "查库状态": "SMILES解析失败", "MW": "", "LogP": "", "HBD": "", "HBA": "",
                         "RotB": "", "TPSA": "", "Violations": "", "筛选结果": "✗ 解析失败"})
            continue
        found += 1
        p = lipinski(mol)
        # violations <= 1 -> candidate; >= 2 -> large glycoside/lipid (keep flagged, may act as prodrug)
        status = "✓ 候选活性成分" if p["Violations"] <= 1 else "△ 分子量大(糖苷/脂质)"
        rows.append({**base, "查库状态": "OK", **p, "筛选结果": status})

    fields = ["VAR", "ID", "Metabolite", "SMILES", "查库状态", "MW", "LogP", "HBD", "HBA",
              "RotB", "TPSA", "Violations", "筛选结果"]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    ok = sum(1 for r in rows if r["筛选结果"] == "✓ 候选活性成分")
    warn = sum(1 for r in rows if "△" in r["筛选结果"])
    print(f"总计 {len(rows)} | 查库成功 {found} | 候选 {ok} | 糖苷/脂质 {warn} | 无结构 {len(rows)-ok-warn}")
    print(f"结果 -> {OUT_CSV}")


if __name__ == "__main__":
    main()
