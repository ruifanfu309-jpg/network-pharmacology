# 网药小白入门教程 (Beginner tutorial bank, 2026-08)

Teaching content for the user (石河子大学食品学院, network-pharmacology beginner). All numbers are REAL from the user's own 138-metabolite antioxidant project — reuse them when teaching; the user loves "拿我们的真实数据".

## What 网络药理学 is (the 5-minute opener)

- 传统方法: one ingredient → one disease, one trial at a time.
- 网药: "成分 ↔ 靶点 ↔ 疾病" network mined from databases + computers, drawn as a graph.
- Analogy that lands: 汤里所有食材 vs 身体零件的"社交圈" — 查谁跟抗氧化圈的人熟.
- Core logic, one sentence: 成分 → 预测靶点 → 与疾病靶点取交集 → 网络图 + 富集验证.

## The 8-step pipeline in 大白话 (with this user's real numbers)

| # | Step | Tool | Plain meaning | User's numbers |
|---|------|------|---------------|----------------|
| ① | 成分收集 | LC-MS / TCMSP | 把食材捞出来 | 138 代谢物 |
| ② | 结构+类药性 | PubChem + RDKit | 食材过安检 | 126 SMILES → 72 候选 |
| ③ | ADME | TCMSP | 好不好消化 | 7 个 OB≥30% |
| ④ | 靶点预测 | STP | 食材碰哪些零件 | 124 成分 / 1781 条 |
| ⑤ | 疾病靶点 | GeneCards + UniProt GO | 抗氧化圈都有谁 | 416 基因 |
| ⑥ | 取交集 | Venny/Python | 两圈对比 | 189 条 / 46 基因 / 98 成分 |
| ⑦ | 网络图 | ECharts/Cytoscape | 画关系图 | 144 节点 |
| ⑧ | 富集+验证 | g:Profiler | 共同职业是啥 | GO:BP 氧化应激 p=1.41e-38 |

## The 12 TCMSP ADME parameters (plain-language table)

| Param | Full name | 白话 | Standard |
|-------|-----------|------|----------|
| MW | 分子量 | 分子多重 | ≤500 |
| AlogP | 脂水分配 | 油腻度 | ≤5 |
| TPSA | 拓扑极性表面积 | 亲水面积 | 20–130 Å² |
| Hdon | 氢键供体数 | 魔术贴钩子 | ≤5 |
| Hacc | 氢键受体数 | 魔术贴毛面 | ≤10 |
| OB(%) | 口服生物利用度 | 吃了吸收多少 | ≥30% ⭐ |
| Caco-2 | 肠细胞通透性 | 肠道保安放不放行 | >0.4 |
| BBB | 血脑屏障 | 大脑门卫放不放行 | >0.3 |
| DL | 类药性 | 长得像不像药 | ≥0.18 ⭐ |
| HL | 半衰期 | 药效持续多久 | 视情况 |
| RBN | 可旋转键数 | 分子关节数 | ≤10 |
| FASA- | 亲水面分数 | 表面带电占比 | 进阶 |

## Key-concept analogies that work

- **NFE2L2 = Nrf2 = 消防总指挥** (KEAP1=保安关着他; 氧化应激=火灾 → KEAP1 松手 → Nrf2 进核 → 喊 SOD/CAT/GPX/NQO1/HO-1 灭火队员出动). Pathway name: KEAP1/Nrf2/ARE.
- **`@` in SMILES = 手性/左右手**: `@` 一种朝向, `@@` 镜像; 无标记=未指定. 案例: 沙利度胺 (一个构型治孕吐, 镜像致畸). Both @-and-plain SMILES work in STP.
- **DL = 看脸打分**: Tanimoto 相似度 vs 652 known drugs. DL 高 ≠ 活性强 — 没食子酸 DL=0.045 但抗氧化强. OB+DL 双标准互补 (龙胆苦苷 OB=23% 低但 DL=0.39 达标; 没食子酸反着).
- **GeneCards 搜 keyword = 图书馆查书**: matches any gene whose annotation text mentions the word; take top 20–50 by relevance score.
- **138 代谢物是什么**: LC-MS (UHPLC-Q-TOF-MS/MS) metabolomics output of the user's 发酵样品. VAR00008=software auto-ID; neg_/pos_=ion mode. Classes: 黄酮糖苷 ~30%, 酚酸 ~15%, 脂质 ~10%, 糖/肽/杂类 rest.

## Hands-on practice exercise (Gentiopicroside → NFE2L2)

Give the user THIS walkthrough; real data below so we can verify their result.

1. **PubChem SMILES**: open `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/Gentiopicroside/property/CanonicalSMILES/TXT` → `C=C[C@H]1[C@@H](OC=C2C1=CCOC2=O)O[C@H]3[C@@H]([C@H]([C@@H]([C@H](O3)CO)O)O)O` (the `@` is fine).
2. **TCMSP** (skip, already known: OB=23.0% DL=0.39) or tcmsp-e.com search `Gentiopicroside`.
3. **STP**: swisstargetprediction.ch → paste SMILES → Homo sapiens → Predict targets. Real targets (12): STAT3, PTPN1, BACE1, PRKCA, HSP90AA1, EPAS1, NFE2L2, TRPM7, BCL2L1, IL2, ADORA3, PRKCQ.
4. **GeneCards**: genecards.org → search `antioxidant` → top 20: ATOX1(296.4), PRDX3(169.4), PRDX5(143.4), PRDX4(139.1), PRDX2(128.0), PRDX6(127.3), PRDX1(117.8), NFE2L2(114.6), KEAP1(108.7), CAT(89.2), SELENOP(89.1), PON2(88.1), HP(81.1), GSR(80.5), SOD3(80.0), PRXL2A(78.1), NFE2L1(76.1), TP53(73.7), ATM(72.5), TP53INP1(72.3).
5. **Venny** (bioinfogp.cnb.csic.es/tools/venny/): **List1 = STP targets, List2 = disease genes** (one per line, uppercase gene symbols, no commas/spaces). Intersection = **NFE2L2** 🎉.
6. **STRING**: string-db.org → "Multiple proteins by names / identifiers" → paste 15–20 hub genes (NOT 50 — 15–30 keeps the graph readable; use ALL 46 only for enrichment) → Homo sapiens → Search → Continue → Exports (PNG/SVG).
7. **g:Profiler**: paste all intersection genes → GO:BP + KEGG → Run query → top hit should be oxidative stress.

Paper tip: 材料与方法 write-up → "采用 UHPLC-Q-TOF-MS/MS 对样品进行代谢组学分析，共鉴定出 138 个差异代谢物（VIP>1, p<0.05）"; 讨论 highlight "通过 KEAP1/Nrf2/ARE 信号通路发挥抗氧化作用".

## Beginner FAQ (answers already validated in-session)

- **SMILES 栏在哪?** PubChem compound page → right column → **Computed Properties** → expand → SMILES/Canonical SMILES. Faster: REST URL trick above.
- **为什么有 @?** stereochemistry (see analogy above).
- **DL 怎么这么有意思?** it's a similarity score vs known drugs; low DL ≠ inactive (没食子酸 0.045 still antioxidant).
- **NFE2L2 是什么?** Nrf2, antioxidant master switch; hub of the project's story.
- **antioxidant 怎么来的?** user's own research theme; GeneCards keyword search.
- **List1 和 2 填什么?** List1=STP 成分靶点名单, List2=疾病基因名单; 每行一个, 全大写.
- **string-db.org 怎么用?** Search tab → paste genes → Homo sapiens → Search → Continue → Exports.
- **50 个吗?** STRING 15–30; enrichment all 46.
