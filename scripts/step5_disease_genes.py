# -*- coding: utf-8 -*-
"""
Network pharmacology - Step 5: disease-target gene retrieval (UniProt GO terms)
疾病靶点获取（UniProt GO 注释）——通用版，任意疾病方向可配置

Usage (用法):
    # 抗氧化 (default example)
    python step5_disease_genes.py

    # 抗炎 (anti-inflammatory)
    python step5_disease_genes.py --label anti_inflammatory \
        --go "GO:0006954,GO:0002526,GO:0070098" \
        --output step5_anti_inflammatory_genes.csv

    # 降糖 (hypoglycemic)
    python step5_disease_genes.py --label hypoglycemic \
        --go "GO:0032868,GO:0042593,GO:0006006" \
        --output step5_hypoglycemic_genes.csv

Output: CSV with columns go_id,label,gene (deduplicated)
"""
import csv, time, argparse, urllib.request, urllib.parse
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"

# Default example: antioxidant (see SKILL.md "Disease direction" for the full 17-term list)
DEFAULT_GO = [
    ("GO:0006979", "response to oxidative stress"),
    ("GO:0016209", "antioxidant activity"),
    ("GO:0045454", "cell redox homeostasis"),
    ("GO:0004601", "peroxidase activity"),
    ("GO:0004784", "superoxide dismutase activity"),
    ("GO:0004602", "glutathione peroxidase activity"),
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
    ap = argparse.ArgumentParser(description="Disease-target genes from UniProt GO annotations")
    ap.add_argument("--label", default="antioxidant", help="disease direction label, e.g. antioxidant / anti_inflammatory")
    ap.add_argument("--go", default="", help="comma-separated GO terms, e.g. 'GO:0006954,GO:0002526'. Empty = default antioxidant list")
    ap.add_argument("--output", default="", help="output CSV filename")
    args = ap.parse_args()

    if args.go:
        go_terms = [(g.strip(), g.strip()) for g in args.go.split(",") if g.strip()]
    else:
        go_terms = DEFAULT_GO

    out_name = args.output or f"step5_{args.label}_genes.csv"
    out = DATA / out_name

    all_genes = set()
    rows = []
    for go_id, label in go_terms:
        genes = fetch_go_genes(go_id)
        if genes is None:
            print(f"  [FAIL] {go_id}: query error")
            continue
        all_genes.update(genes)
        print(f"  [OK] {go_id} {label}: {len(genes)} genes")
        for g in genes:
            rows.append({"go_id": go_id, "label": label, "gene": g})
        time.sleep(1)

    seen = set()
    uniq = []
    for r in rows:
        if r["gene"] not in seen:
            seen.add(r["gene"])
            uniq.append(r)

    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["go_id", "label", "gene"])
        w.writeheader()
        w.writerows(uniq)
    print(f"\n[OK] {len(uniq)} disease genes ({args.label}) -> {out.name}")

if __name__ == "__main__":
    main()
