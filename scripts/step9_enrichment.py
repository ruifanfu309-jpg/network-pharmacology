# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 第9步: GO/KEGG 富集分析 (g:Profiler API)
输入: step6_intersections_v2.csv (78 基因)
输出: step9_enrichment_go.csv + step9_enrichment_kegg.csv
"""
import csv, json, os, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"

def main():
    # 78 个交集基因
    with open(DATA / "step6_intersections_v2.csv", encoding="utf-8-sig") as f:
        inter = list(csv.DictReader(f))
    genes = sorted(set(r["gene"] for r in inter))
    print(f"交集基因: {len(genes)} 个")

    # g:Profiler API（走代理）
    payload = json.dumps({"organism": "hsapiens", "query": genes,
                          "sources": ["GO:BP", "KEGG"], "user_threshold": 0.05}).encode()
    req = urllib.request.Request("https://biit.cs.ut.ee/gprofiler/api/gost/profile/",
                                 data=payload, headers={"Content-Type": "application/json"})
    proxy = urllib.request.ProxyHandler({"http": os.environ.get("HTTPS_PROXY", "http://127.0.0.1:7993"),
                                          "https": os.environ.get("HTTPS_PROXY", "http://127.0.0.1:7993")})
    opener = urllib.request.build_opener(proxy)
    resp = opener.open(req, timeout=90)
    d = json.loads(resp.read().decode())
    results = d.get("result", [])
    print(f"富集结果: {len(results)} 条")

    def flat_genes(intersections):
        out = []
        for x in intersections:
            if isinstance(x, list):
                out.append(x[0] if x else "")
            else:
                out.append(str(x))
        return out

    def dump(rows, fname):
        with open(DATA / fname, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["source", "term_id", "term_name", "p_value", "term_size", "intersection_size", "genes"])
            for r in rows:
                g = flat_genes(r.get("intersections", []))
                w.writerow([r["source"], r["native"], r["name"], f"{r['p_value']:.3e}",
                            r.get("term_size", ""), len(g), ",".join(g)])

    go_bp = [r for r in results if r["source"] == "GO:BP"][:20]
    kegg = [r for r in results if r["source"] == "KEGG"][:20]
    dump(go_bp, "step9_enrichment_go.csv")
    dump(kegg, "step9_enrichment_kegg.csv")

    print("\n=== GO:BP Top 10 ===")
    for r in go_bp[:10]:
        g = flat_genes(r.get("intersections", []))
        print(f"  p={r['p_value']:.2e} | {r['name'][:50]:52s} | {len(g)}基因")
    print("\n=== KEGG Top 10 ===")
    for r in kegg[:10]:
        g = flat_genes(r.get("intersections", []))
        print(f"  p={r['p_value']:.2e} | {r['name'][:50]:52s} | {len(g)}基因")

if __name__ == "__main__":
    main()
