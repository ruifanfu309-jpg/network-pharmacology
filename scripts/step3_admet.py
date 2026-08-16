# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 第3步: ADMET-AI 批量计算 (吸收/代谢/毒性)
输入: 01_数据/step2_lipinski.csv (候选成分)
输出: 01_数据/step3_admet.csv
"""
import csv, json, time
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"

def main():
    from admet_ai import ADMETModel

    # 读取候选成分 SMILES
    with open(DATA / "step2_lipinski.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    cands = [r for r in rows if "✓" in r.get("筛选结果", "")]
    print(f"候选成分: {len(cands)} 个")

    # 加载模型（首次加载权重）
    print("加载 ADMET-AI 模型...")
    model = ADMETModel()

    smiles_list = [c["SMILES"] for c in cands]
    names = [c["Metabolite"] for c in cands]
    vars_ = [c["VAR"] for c in cands]

    # 批量预测
    print("批量预测中...")
    preds = model.predict(smiles_list)

    # 选取关键 ADMET 列（ADMET-AI v2 实际列名）
    key_cols = [
        "CYP1A2_Veith", "CYP2C9_Veith", "CYP2D6_Veith", "CYP3A4_Veith", "CYP2C19_Veith",
        "CYP2C9_Substrate_CarbonMangels", "CYP2D6_Substrate_CarbonMangels", "CYP3A4_Substrate_CarbonMangels",
        "Bioavailability_Ma", "Caco2_Wang", "BBB_Martins", "Pgp_inhibitor",
        "Clearance_Hepatocyte_AZ", "hERG", "AMES", "Carcinogens_Lagunin",
        "LD50_rats", "skin_sensitization", "Solubility_aq_log_mol_L",
        "GI_absorption",
    ]
    avail = [c for c in key_cols if c in preds.columns]
    print(f"可用列: {len(avail)} 个")

    out_rows = []
    for i, (name, var) in enumerate(zip(names, vars_)):
        row = {"VAR": var, "Metabolite": name}
        for col in avail:
            v = preds.iloc[i][col]
            if isinstance(v, float):
                row[col] = f"{v:.4f}" if abs(v) < 100 else f"{v:.1f}"
            else:
                row[col] = str(v)
        out_rows.append(row)

    # 保存
    out = DATA / "step3_admet.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"✅ ADMET 计算完成: {len(out_rows)} 个成分, {len(avail)} 项参数")
    print(f"   输出: {out}")

if __name__ == "__main__":
    main()
