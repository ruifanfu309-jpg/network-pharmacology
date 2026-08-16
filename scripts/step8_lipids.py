# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 第8步(修): 手动构建 5 个脂质 SMILES (完整手写版)
"""
from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"

# 完整手写脂质 SMILES（甘油骨架 + 脂肪酸酰基 + 头基）
# 格式: sn1-C(=O)OCH2-CH(OC(=O)-sn2)-CH2-head
LIPIDS = [
    # PE(18:1(9Z)/18:2(9Z,12Z)): 1-油酰-2-亚油酰-sn-甘油-3-磷酸乙醇胺
    ("VAR00168", "Pe(18:1/18:2)",
     "CCCCCCCC/C=C/CCCCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/C/C=C/CCCCC)COP(=O)(O)OCCN"),
    # PA(18:0/18:2): 1-硬脂酰-2-亚油酰-sn-甘油-3-磷酸
    ("VAR00512", "Pa(18:0/18:2)",
     "CCCCCCCCCCCCCCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/C/C=C/CCCCC)COP(=O)(O)O"),
    # Gpetn(18:3/18:3): 半乳糖基-1,2-二亚麻酰甘油
    ("VAR00343", "Gpetn(18:3/18:3)",
     "CCC/C=C/C/C=C/C/C=C/CCCCCCCC(=O)OC[C@H](COC(=O)CCCCCC/C=C/C/C=C/C/C=C/CCC)OC1C(C(C(C(O1)CO)O)O)O"),
    # Gpetn(22:4/14:1): 半乳糖基-1-二十二碳四烯酰-2-肉豆蔻烯酰甘油
    ("VAR00586", "Gpetn(22:4/14:1)",
     "CCCCC/C=C/C/C=C/C/C=C/C/C=C/CCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/CCCCC)OC1C(C(C(C(O1)CO)O)O)O"),
    # DGDG(18:2/18:2): 双半乳糖-1,2-二亚油酰甘油
    ("VAR00132", "Dgdg(18:2/18:2)",
     "CCCCC/C=C/C/C=C/CCCCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/C/C=C/CCCCC)OC1C(OC(CO)C(C1O)O)OC2C(C(C(C(O2)CO)O)O)O"),
]

results = []
for var, name, smi in LIPIDS:
    mol = Chem.MolFromSmiles(smi)
    if mol:
        mw = Descriptors.MolWt(mol)
        logp = Crippen.MolLogP(mol)
        results.append({"VAR": var, "name": name, "smiles": smi, "MW": round(mw, 2), "LogP": round(logp, 2), "valid": True})
        print(f"✅ {name}: MW={mw:.1f} LogP={logp:.1f}")
    else:
        results.append({"VAR": var, "name": name, "smiles": smi, "MW": "", "LogP": "", "valid": False})
        print(f"❌ {name}: 解析失败!")

out = DATA / "step8_lipids.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n✅ 已保存: {out}")
