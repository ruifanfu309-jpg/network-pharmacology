# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 第6步: 交集分析 + 网络图数据 + 完整报告
输入: step4_stp_predictions.csv + step5_antioxidant_genes.csv + step5b_genecards
输出: step6_intersections.csv + step6_network.json + 03_报告/网络药理学完整报告.html
"""
import csv, json, html
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"
REPORT = BASE / "03_报告"

def read_csv(fname):
    with open(DATA / fname, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def esc(s):
    return html.escape(str(s or ""))

def main():
    stp = read_csv("step4_stp_full.csv")
    go = read_csv("step5_antioxidant_genes.csv")
    gc = []  # 方案A: 纯净版只用 GO 注释（不含 GeneCards 文本挖掘基因）
    lip = read_csv("step2_lipinski.csv")
    admet = read_csv("step3_admet.csv")

    go_genes = set(r["gene"].upper() for r in go)
    gc_genes = {}
    all_anti = go_genes
    print(f"抗氧化基因: GO={len(go_genes)} → {len(all_anti)}（纯净版，无 GeneCards）")

    inter = []
    for r in stp:
        gene = r["common"].upper().strip()
        if gene in all_anti:
            src = []
            if gene in go_genes: src.append("GO")
            if gene in gc_genes: src.append("GeneCards")
            inter.append({
                "compound": r["compound"], "gene": gene, "uniprot": r["uniprot"],
                "target_name": r["target_name"], "probability": r["probability"],
                "source": "+".join(src), "gc_score": gc_genes.get(gene, "")
            })

    best = {}
    for x in inter:
        key = (x["compound"], x["gene"])
        p = float(x["probability"])
        if key not in best or p > float(best[key]["probability"]):
            best[key] = x
    inter = sorted(best.values(), key=lambda x: -float(x["probability"]))

    genes_hit = set(x["gene"] for x in inter)
    comps_hit = set(x["compound"] for x in inter)
    print(f"交集: {len(inter)} 条, {len(genes_hit)} 基因, {len(comps_hit)} 成分")

    with open(DATA / "step6_intersections.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["compound", "gene", "uniprot", "target_name", "probability", "source", "gc_score"])
        w.writeheader()
        w.writerows(inter)

    nodes, node_ids, links = [], set(), []
    for x in inter:
        cid, gid = "C:" + x["compound"], "G:" + x["gene"]
        if cid not in node_ids:
            node_ids.add(cid)
            nodes.append({"name": x["compound"], "id": cid, "category": 0})
        if gid not in node_ids:
            node_ids.add(gid)
            nodes.append({"name": x["gene"], "id": gid, "category": 1})
        links.append({"source": cid, "target": gid, "value": round(float(x["probability"]), 2)})

    degree = defaultdict(int)
    for l in links:
        degree[l["source"]] += 1
        degree[l["target"]] += 1
    for n in nodes:
        d = degree[n["id"]]
        n["degree"] = d
        if n["category"] == 1:
            n["core"] = d >= 3
            n["symbolSize"] = 32 if d >= 3 else 18
        else:
            n["symbolSize"] = 14

    (DATA / "step6_network.json").write_text(
        json.dumps({"nodes": nodes, "links": links}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"网络图: {len(nodes)} 节点, {len(links)} 连线")

    gene_rank = sorted([(n["name"], n["degree"]) for n in nodes if n["category"] == 1], key=lambda x: -x[1])
    print("核心靶点 Top 10:")
    for g, d in gene_rank[:10]:
        print(f"  {g:10s} {d} 成分")

    # ===== 构建 HTML（占位符方式避免 f-string 冲突）=====
    # 富集表
    go_bp = read_csv("step9_enrichment_go.csv")
    kegg = read_csv("step9_enrichment_kegg.csv")
    go_rows = ""
    for r in go_bp[:12]:
        go_rows += f"<tr><td>{esc(r['term_name'][:58])}</td><td class='n' style='color:#34d399'>{esc(r['p_value'])}</td><td class='n'>{esc(r['intersection_size'])}</td></tr>"
    kegg_rows = ""
    for r in kegg[:10]:
        kegg_rows += f"<tr><td>{esc(r['term_name'][:58])}</td><td class='n' style='color:#34d399'>{esc(r['p_value'])}</td><td class='n'>{esc(r['intersection_size'])}</td></tr>"

    # 排行表
    ranking = read_csv("step7_ranking.csv")
    rank_rows = ""
    for r in ranking[:20]:
        medal = {"1": "🥇", "2": "🥈", "3": "🥉"}.get(r["排名"], "")
        rank_rows += f"<tr><td style='text-align:center'>{medal}{r['排名']}</td><td>{esc(r['Metabolite'])}</td><td class='n'>{r['抗氧化靶点数']}</td><td class='n'>{r['最高概率']}</td><td class='n'>{r['生物利用度']}</td><td class='n' style='color:#fbbf24'>{r['综合评分']}</td></tr>"

    inter_rows = ""
    for x in sorted(inter, key=lambda r: -float(r["probability"]))[:80]:
        inter_rows += "<tr><td>" + esc(x["compound"]) + "</td><td style='color:#34d399;font-weight:700'>" + esc(x["gene"]) + "</td><td>" + esc(x["uniprot"]) + "</td><td class='n'>" + f"{float(x['probability']):.2f}" + "</td><td>" + esc(x["source"]) + "</td></tr>"

    gene_rows = ""
    for i, (g, d) in enumerate(gene_rank[:20], 1):
        comps_for_g = [x["compound"] for x in inter if x["gene"] == g][:3]
        gc_score = next((x["gc_score"] for x in inter if x["gene"] == g and x.get("gc_score")), "")
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, "")
        gene_rows += "<tr><td style='text-align:center'>" + medal + str(i) + "</td><td style='font-weight:700;color:#a78bfa'>" + g + "</td><td class='n' style='color:#fbbf24'>" + str(d) + "</td><td class='l'>" + esc("、".join(comps_for_g)) + "</td><td class='n'>" + esc(gc_score) + "</td></tr>"

    admet_map = {r["Metabolite"]: r for r in admet}
    admet_rows = ""
    for r in sorted(inter, key=lambda x: -float(x["probability"]))[:30]:
        a = admet_map.get(r["compound"], {})
        bio, ames, carc = a.get("Bioavailability_Ma", ""), a.get("AMES", ""), a.get("Carcinogens_Lagunin", "")
        bio_html = "<span style='color:#34d399;font-weight:700'>" + bio + "</span>" if bio and float(bio) > 0.5 else bio
        ames_html = "<span style='color:#34d399'>" + ames + "</span>" if ames and float(ames) < 0.5 else ames
        admet_rows += "<tr><td>" + esc(r["compound"]) + "</td><td class='n'>" + bio_html + "</td><td class='n'>" + ames_html + "</td><td class='n'>" + carc + "</td><td style='color:#34d399;font-weight:700'>" + esc(r["gene"]) + "</td><td class='n'>" + f"{float(r['probability']):.2f}" + "</td></tr>"

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    links_json = json.dumps(links, ensure_ascii=False)

    n_cand = sum(1 for r in lip if "✓" in r.get("筛选结果", ""))

    # 读模板
    tpl = (BASE / "02_脚本" / "report_template.html").read_text(encoding="utf-8")
    doc = tpl
    for key, val in {
        "__N_CAND__": str(n_cand),
        "__N_ANTI__": str(len(all_anti)),
        "__N_COMP_HIT__": str(len(comps_hit)),
        "__N_GENE_HIT__": str(len(genes_hit)),
        "__N_NODES__": str(len(nodes)),
        "__N_LINKS__": str(len(links)),
        "__GENE_ROWS__": gene_rows,
        "__ADMET_ROWS__": admet_rows,
        "__INTER_ROWS__": inter_rows,
        "__GO_ROWS__": go_rows,
        "__KEGG_ROWS__": kegg_rows,
        "__RANK_ROWS__": rank_rows,
        "__NODES_JSON__": nodes_json,
        "__LINKS_JSON__": links_json,
    }.items():
        doc = doc.replace(key, val)

    REPORT.mkdir(parents=True, exist_ok=True)
    out = REPORT / "网络药理学完整报告.html"
    out.write_text(doc, encoding="utf-8")
    print(f"✅ 报告已生成: {out}")

    # 自动内联 echarts（若本地文件存在）
    ech_file = REPORT / "echarts.min.js"
    if ech_file.exists():
        ech = ech_file.read_text(encoding="utf-8")
        doc2 = doc.replace('<script src="echarts.min.js"></script>', "<script>" + ech + "</script>")
        out.write_text(doc2, encoding="utf-8")
        print(f"✅ ECharts 已内联, 最终大小 {len(doc2)//1024}KB")
    else:
        print("⚠️ echarts.min.js 不存在，报告引用外部相对路径")

if __name__ == "__main__":
    main()
