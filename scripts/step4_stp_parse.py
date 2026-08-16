# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 恢复 STP 靶点预测结果（从浏览器缓存解析）
输出: 01_数据/step4_stp_predictions.csv
"""
import re, csv, json, os, sys
from pathlib import Path

# 浏览器 workspace 路径：优先命令行参数，其次环境变量，最后默认值
WS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ.get("BH_AGENT_WORKSPACE", r"C:\path\to\browser-use\workspace"))
BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"

# 名称映射（safe 名 → 原名）
def safe_name(name):
    return "".join(c for c in name if c.isalnum() or c in "_- ").replace(" ", "_")[:40]

# 从 step1_structures.json 拿真实名字映射
structs = json.loads((DATA / "step1_structures.json").read_text(encoding="utf-8"))
safe_to_real = {safe_name(s["name"]): s["name"] for s in structs}
# 补充核心映射（旧的核心 20 个）
core_map = {
    "5-Hydroxyferulic_Acid": "5-Hydroxyferulic Acid", "Syringic_Acid": "Syringic Acid",
    "Axillarin": "Axillarin", "Rheic_Acid": "Rheic Acid", "Methyl_Gallate": "Methyl Gallate",
    "Protocatechuic_Acid": "Protocatechuic Acid", "Vanillylmandelic_Acid": "Vanillylmandelic Acid",
    "Wedelolactone": "Wedelolactone", "Daidzin": "Daidzin", "Gentiopicroside": "Gentiopicroside",
    "Cosmosiin": "Cosmosiin", "Ascorbic_Acid": "Ascorbic Acid",
    "Kaempferol_7-Arabinoside": "Kaempferol 7-Arabinoside", "Isovanillic_Acid": "Isovanillic Acid",
    "7-Hydroxycoumarine": "7-Hydroxycoumarine", "Bellidifolin": "Bellidifolin",
    "Hydroquinone": "Hydroquinone", "Shikimic_Acid_3-Phosphate": "Shikimic Acid 3-Phosphate",
}
safe_to_real.update(core_map)
safe_to_real["Gallic_Acid"] = "Gallic Acid"
safe_to_real["Inermin"] = "Inermin"

TARGET_RE = re.compile(r'(.+?)\t([A-Z][A-Z0-9\-]*)\t([OPQ][0-9][A-Z0-9]{4}|[A-NR][0-9][A-Z0-9]{3}[0-9]|[A-Z0-9]{6})\t(CHEMBL\d+)\t(.+?)\t([\d.]+)')

def parse_file(fname):
    p = WS / fname
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")
    out = []
    blocks = re.split(r'@@@@@\s+([A-Za-z0-9_\-]+)\s+@@@@@', text)
    for i in range(1, len(blocks), 2):
        raw = blocks[i].strip()
        real = safe_to_real.get(raw, raw)
        body = blocks[i+1]
        if "Target Classes" not in body:
            continue
        for m in TARGET_RE.finditer(body):
            tname, common, uniprot, chembl, tclass, prob = m.groups()
            out.append({"compound": real, "common": common.strip(), "uniprot": uniprot,
                        "chembl": chembl, "class": tclass.strip(), "probability": float(prob),
                        "target_name": tname.strip()[:60]})
    return out

all_rows = []
all_rows += parse_file("stp_all_results4.txt")
for fn in ["stp_batch2_results.txt", "stp_batch3_results.txt", "stp_batch4_results.txt"]:
    all_rows += parse_file(fn)
for fn, disp in [("stp_syringic.txt", "Syringic Acid"), ("stp_gallic_full.txt", "Gallic Acid")]:
    text = (WS / fn).read_text(encoding="utf-8")
    for m in TARGET_RE.finditer(text):
        tname, common, uniprot, chembl, tclass, prob = m.groups()
        all_rows.append({"compound": disp, "common": common.strip(), "uniprot": uniprot,
                         "chembl": chembl, "class": tclass.strip(), "probability": float(prob),
                         "target_name": tname.strip()[:60]})

# 去重
seen = set()
uniq = []
for r in all_rows:
    key = (r["compound"], r["uniprot"])
    if key in seen:
        continue
    seen.add(key)
    uniq.append(r)

from collections import Counter
comp_cnt = Counter(r["compound"] for r in uniq)
print(f"恢复: {len(uniq)} 条关联, {len(comp_cnt)} 个化合物")

# 保存
out = DATA / "step4_stp_predictions.csv"
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["compound", "target_name", "common", "uniprot", "chembl", "class", "probability"])
    w.writeheader()
    w.writerows(uniq)
print(f"✅ 已保存: {out}")

# 对比 130 个有结构的，找出缺的
have = set(comp_cnt.keys())
all_names = set(s["name"] for s in structs if s.get("smiles"))
missing = all_names - have
print(f"\n有结构但无 STP 结果: {len(missing)} 个")
for m in sorted(missing):
    print(f"  {m[:50]}")
