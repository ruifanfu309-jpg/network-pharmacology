# -*- coding: utf-8 -*-
"""
网络药理学 v2 - 网络图静态 PNG + 自包含 HTML
用 networkx + matplotlib 生成静态网络图 (方案A)
同时重新生成内联 ECharts 的 HTML (方案B)
"""
import csv, json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
DATA = BASE / "01_数据"
REPORT = BASE / "03_报告"

def main():
    # 读取交集数据
    with open(DATA / "step6_intersections.csv", encoding="utf-8-sig") as f:
        inter = list(csv.DictReader(f))

    # 构建网络
    import networkx as nx
    G = nx.Graph()
    for r in inter:
        G.add_edge(r["compound"], r["gene"], weight=float(r["probability"]))
    print(f"图: {G.number_of_nodes()} 节点, {G.number_of_edges()} 连线")

    # 分类节点
    comps = [n for n in G.nodes if n not in set(r["gene"] for r in inter)]
    genes = [n for n in G.nodes if n in set(r["gene"] for r in inter)]
    degree = dict(G.degree())

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(18, 14), dpi=150)
    pos = nx.spring_layout(G, k=1.6, iterations=80, seed=42)

    # 画边
    edges = list(G.edges())
    weights = [G[u][v]["weight"] * 2 for u, v in edges]
    nx.draw_networkx_edges(G, pos, ax=ax, edgelist=edges, width=weights,
                           edge_color="#8b9bb4", alpha=0.5)

    # 画成分节点（紫）
    comp_nodes = [n for n in comps if n in G]
    sizes_c = [degree[n] * 220 + 300 for n in comp_nodes]
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=comp_nodes, node_size=sizes_c,
                           node_color="#8b5cf6", alpha=0.9, node_shape="o")

    # 画靶点节点（绿，核心黄色）
    core_genes = [g for g in genes if degree[g] >= 3]
    other_genes = [g for g in genes if degree[g] < 3]
    sizes_g = [degree[g] * 320 + 500 for g in genes]
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=core_genes,
                           node_size=[degree[g] * 320 + 500 for g in core_genes],
                           node_color="#fbbf24", alpha=0.95, node_shape="o")
    nx.draw_networkx_nodes(G, pos, ax=ax, nodelist=other_genes,
                           node_size=[degree[g] * 320 + 500 for g in other_genes],
                           node_color="#34d399", alpha=0.9, node_shape="o")

    # 标签
    nx.draw_networkx_labels(G, pos, ax=ax,
                            labels={n: n for n in comp_nodes},
                            font_size=7, font_color="#c4b5fd")
    nx.draw_networkx_labels(G, pos, ax=ax,
                            labels={g: g for g in genes},
                            font_size=9, font_color="#0f172a", font_weight="bold")

    # 图例
    legend = [
        mpatches.Patch(color="#8b5cf6", label="活性成分"),
        mpatches.Patch(color="#34d399", label="抗氧化靶点"),
        mpatches.Patch(color="#fbbf24", label=f"核心靶点(度≥3, n={len(core_genes)})"),
    ]
    ax.legend(handles=legend, loc="upper left", fontsize=11, framealpha=0.8,
              facecolor="#0f172a", edgecolor="#334155", labelcolor="#e2e8f0")
    ax.set_title(f"成分-靶点关联网络图 ({G.number_of_nodes()} 节点 / {G.number_of_edges()} 连线)",
                 fontsize=16, color="#e2e8f0", pad=14)
    ax.set_facecolor("#0a0f1a")
    fig.patch.set_facecolor("#0a0f1a")
    ax.axis("off")

    REPORT.mkdir(parents=True, exist_ok=True)
    png = REPORT / "成分靶点网络图.png"
    fig.savefig(png, bbox_inches="tight", facecolor="#0a0f1a")
    print(f"✅ 静态图已生成: {png} ({png.stat().st_size//1024}KB)")
    plt.close(fig)

    # 保存网络数据供 HTML 用
    nodes, links, node_ids = [], set(), []
    for r in inter:
        cid, gid = "C:" + r["compound"], "G:" + r["gene"]
        if cid not in node_ids:
            node_ids.add(cid)
            nodes.append({"name": r["compound"], "id": cid, "category": 0})
        if gid not in node_ids:
            node_ids.add(gid)
            nodes.append({"name": r["gene"], "id": gid, "category": 1})
        links.append({"source": cid, "target": gid})
    for n in nodes:
        n["degree"] = degree[n["name"]]
        if n["category"] == 1:
            n["core"] = degree[n["name"]] >= 3
    (DATA / "step6_network_v2.json").write_text(
        json.dumps({"nodes": nodes, "links": links}, ensure_ascii=False), encoding="utf-8")
    print("网络数据已保存")

if __name__ == "__main__":
    main()
