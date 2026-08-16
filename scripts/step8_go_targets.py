# -*- coding: utf-8 -*-
"""
UniProt GO-term batch query — disease-target gene sets for network pharmacology.
Queries ALL reviewed human genes annotated to antioxidant GO terms and writes
a CSV (gene, uniprot, protein, GO terms). Verified query syntax 2026-08.

Usage (uv venv python):
    python step8_go_targets.py > step8_output.txt 2>&1
"""
import time, urllib.request, csv
from pathlib import Path

BASE = Path(__file__).parent
OUT_CSV = BASE / "抗氧化靶点_GO.csv"

# Antioxidant-related GO terms (rename / extend per disease)
GO_TERMS = {
    "GO:0006979": "氧化应激响应",
    "GO:0016209": "抗氧化活性",
    "GO:0045454": "细胞氧化还原稳态",
    "GO:0004601": "过氧化物酶活性",
    "GO:0004784": "超氧化物歧化酶活性",
    "GO:0004602": "谷胱甘肽过氧化物酶活性",
}

def fetch_go_genes(go_id):
    """CRITICAL syntax: (GO:xxxxxxx) BARE — NOT go:GO:... nor go_id:GO:... (both HTTP 400)."""
    url = (f"https://rest.uniprot.org/uniprotkb/stream?query=(GO:{go_id.split(':')[1]})"
           f"+AND+organism_id:9606+AND+reviewed:true&format=tsv"
           f"&fields=accession,gene_primary,protein_name,organism_name")
    # NOTE: query=(GO:0006979) — the GO prefix itself is required, just no extra field name.
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            lines = resp.read().decode("utf-8", errors="ignore").strip().split("\n")
            genes = {}
            for line in lines[1:]:
                parts = line.split("\t")
                if len(parts) >= 3 and parts[1]:
                    gene = parts[1].split()[0]
                    genes[gene] = {"uniprot": parts[0], "gene": gene, "protein": parts[2][:50]}
            return genes
    except Exception as e:
        print(f"    {go_id} query failed: {e}")
        return {}

def main():
    all_genes = {}
    for go_id, desc in GO_TERMS.items():
        genes = fetch_go_genes(go_id)
        print(f"  {go_id} {desc}: {len(genes)} genes")
        for g, info in genes.items():
            if g not in all_genes:
                all_genes[g] = info
                all_genes[g]["GO"] = [go_id]
            else:
                all_genes[g]["GO"].append(go_id)
        time.sleep(1)

    print(f"\n✅ deduped: {len(all_genes)} antioxidant genes")
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["gene", "uniprot", "protein", "GO_terms"])
        for g, info in sorted(all_genes.items()):
            w.writerow([g, info["uniprot"], info["protein"], ";".join(info["GO"])])
    print(f"result: {OUT_CSV}")

if __name__ == "__main__":
    main()
