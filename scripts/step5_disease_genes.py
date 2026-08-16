# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 第5步: 抗氧化疾病靶点获取 (UniProt GO 注释)
GO: 氧化应激响应/抗氧化活性/过氧化物酶/SOD/GPX
输出: 01_数据/step5_antioxidant_genes.csv
"""
import csv, json, time, urllib.request, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"

GO_TERMS = [
    ("GO:0006979", "氧化应激响应"),
    ("GO:0016209", "抗氧化活性"),
    ("GO:0045454", "细胞氧化还原稳态"),
    ("GO:0004601", "过氧化物酶活性"),
    ("GO:0004784", "超氧化物歧化酶活性"),
    ("GO:0004602", "谷胱甘肽过氧化物酶活性"),
]

def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=40) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"ERR:{e}"

def fetch_go_genes(go_id):
    url = (f"https://rest.uniprot.org/uniprotkb/stream?query=({go_id})+AND+organism_id:9606"
           f"+AND+reviewed:true&format=tsv&fields=accession,gene_primary,protein_name")
    r = get(url)
    if r.startswith("ERR"):
        return None
    genes = []
    lines = r.strip().split("\n")
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) >= 2 and parts[1]:
            genes.append(parts[1].strip())
    return genes

def main():
    all_genes = set()
    rows = []
    for go_id, label in GO_TERMS:
        genes = fetch_go_genes(go_id)
        if genes is None:
            print(f"  ❌ {go_id} {label}: 查询失败")
            continue
        all_genes.update(genes)
        print(f"  ✅ {go_id} {label}: {len(genes)} 个基因")
        for g in genes:
            rows.append({"go_id": go_id, "label": label, "gene": g})
        time.sleep(1)

    # 去重
    seen = set()
    uniq = []
    for r in rows:
        if r["gene"] not in seen:
            seen.add(r["gene"])
            uniq.append(r)

    out = DATA / "step5_antioxidant_genes.csv"
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["go_id", "label", "gene"])
        w.writeheader()
        w.writerows(uniq)
    print(f"\n✅ 去重后 {len(uniq)} 个抗氧化基因 → {out.name}")

if __name__ == "__main__":
    main()
