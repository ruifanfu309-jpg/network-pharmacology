# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 第2步: RDKit 类药性计算 (Lipinski五规则)
输入: 01_数据/step1_structures.json
输出: 01_数据/step2_lipinski.csv
"""
import csv, json
from pathlib import Path
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"
IN = DATA / "step1_structures.json"
OUT = DATA / "step2_lipinski.csv"

def main():
    structs = json.loads(IN.read_text(encoding="utf-8"))
    rows = []
    n_ok = 0
    for s in structs:
        entry = {
            "VAR": s["VAR"], "Metabolite": s["name"], "SMILES": s.get("smiles", ""),
            "查库状态": "OK" if s.get("smiles") else "未找到",
            "MW": "", "LogP": "", "HBD": "", "HBA": "", "RotB": "", "TPSA": "",
            "Violations": "", "筛选结果": "✗ 无结构" if not s.get("smiles") else ""
        }
        if s.get("smiles"):
            mol = Chem.MolFromSmiles(s["smiles"])
            if mol:
                n_ok += 1
                mw = Descriptors.MolWt(mol)
                logp = Crippen.MolLogP(mol)
                hbd = Descriptors.NumHDonors(mol)
                hba = Descriptors.NumHAcceptors(mol)
                rotb = Descriptors.NumRotatableBonds(mol)
                tpsa = Descriptors.TPSA(mol)
                viol = sum([mw > 500, logp > 5, hbd > 5, hba > 10, rotb > 10])
                entry.update({
                    "MW": f"{mw:.2f}", "LogP": f"{logp:.2f}", "HBD": hbd, "HBA": hba,
                    "RotB": rotb, "TPSA": f"{tpsa:.1f}", "Violations": viol,
                    "筛选结果": "✓ 候选活性成分" if viol <= 1 else "△ 分子量大(糖苷/脂质)"
                })
            else:
                entry["筛选结果"] = "✗ SMILES解析失败"
        rows.append(entry)

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    cand = sum(1 for r in rows if "✓" in r["筛选结果"])
    big = sum(1 for r in rows if "△" in r["筛选结果"])
    miss = sum(1 for r in rows if "✗" in r["筛选结果"])
    print(f"✅ 类药性计算完成: 结构OK {n_ok}")
    print(f"   候选 {cand} | 大分子 {big} | 无结构 {miss}")
    print(f"   输出: {OUT}")

if __name__ == "__main__":
    main()
