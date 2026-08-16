# -*- coding: utf-8 -*-
"""
Network pharmacology Step 4: gene symbol -> canonical UniProt ID mapping.
Reads a gene list text file (one gene per line, `#` comments allowed), writes CSV.

KEY: query MUST include `reviewed:true` or you get random isoforms (A0A... accessions)
instead of canonical Swiss-Prot entries. Strip everything after `#` (inline Chinese
comments otherwise become garbage gene-name tokens).
"""
import json, time, urllib.request, urllib.parse, csv
from pathlib import Path

BASE = Path(__file__).parent
TXT_FILE = BASE / "抗氧化靶点列表.txt"   # user-provided gene list
OUT_CSV = BASE / "抗氧化靶点_UniProt.csv"


def read_genes(path: Path):
    genes = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.split("#")[0].strip()  # strip inline comments
            if not line:
                continue
            for g in line.replace("/", " ").split():
                if g.isascii() and g.isalpha() and len(g) <= 12:
                    genes.append(g.upper())
    return sorted(set(genes))


def map_gene(gene):
    url = (f"https://rest.uniprot.org/uniprotkb/search?"
           f"query=gene_exact:{gene}+AND+organism_id:9606+AND+reviewed:true"
           f"&format=json&fields=accession,id,protein_name,gene_names&size=1")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode())
            results = d.get("results", [])
            if results:
                r = results[0]
                return {"gene": gene, "uniprot": r.get("primaryAccession", ""),
                        "entry": r.get("uniProtkbId", ""),
                        "protein": (r.get("proteinDescription", {}).get("recommendedName", {})
                                     .get("fullName", {}).get("value", ""))[:60]}
    except Exception:
        pass
    return {"gene": gene, "uniprot": "", "entry": "", "protein": ""}


def main():
    genes = read_genes(TXT_FILE)
    print(f"共 {len(genes)} 个基因")
    results = []
    for i, g in enumerate(genes):
        res = map_gene(g)
        results.append(res)
        print(f"  {'✓' if res['uniprot'] else '✗'} {g:8s} -> {res['uniprot'] or '未找到'}")
        time.sleep(0.2)
        if (i + 1) % 10 == 0:
            time.sleep(1)

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["gene", "uniprot", "entry", "protein"])
        w.writeheader()
        w.writerows(results)

    found = sum(1 for r in results if r["uniprot"])
    print(f"\n完成: {found}/{len(genes)} 映射成功 -> {OUT_CSV}")


if __name__ == "__main__":
    main()
