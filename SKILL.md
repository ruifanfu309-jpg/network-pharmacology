---
name: network-pharmacology
description: "Use when screening compounds for drug-like actives (网络药理学)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [network-pharmacology, pubchem, rdkit, lipinski, tcmsp, target-prediction, antioxidant, metabolomics]
    related_skills: [academic-research-tools, academic-paper, deep-research]
---

# Network Pharmacology Screening (网络药理学·前期物质筛选)

## When to use

- User has a batch of compounds / metabolites (LC-MS output, TCM database entries, literature lists) and wants to screen for drug-like / active ingredients.
- User mentions 网络药理学, 前期物质筛选, OB/DL 筛选, 类药性, 靶点预测, 分子对接, or a target disease (e.g. 抗氧化 / antioxidant, 抗炎 / anti-inflammatory).
- Typical input: CSV with `Metabolite` names + IDs (VAR / neg_ / pos_ MS identifiers).

## Pipeline (前期筛选核心)

```
① 成分列表(CSV) → ② PubChem 批量获取SMILES → ③ RDKit 计算 Lipinski 参数
→ ④ 筛选判定 (Violations ≤ 1 → 候选活性成分) → ⑤ 靶点预测 → ⑥ 疾病靶点交集
→ ⑦ 成分-靶点网络 (HTML/Cytoscape) → ⑧ GO/KEGG 富集 + 分子对接 (可选)
```

Screening criterion mirrors TCMSP's OB/DL approach but computed locally:
- **Lipinski five rules**: MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10, RotB ≤ 10.
- Violations ≤ 1 → candidate active ingredient. Violations ≥ 2 with large MW → likely sugar conjugate / lipid (mark `大分子糖苷/脂质` separately — do NOT hard-delete; they may act as prodrugs).
- For TCMSP-style OB/DL numbers specifically, pull from TCMSP directly (OB ≥ 30%, DL ≥ 0.18).

**Composite ranking when the user asks "从好到坏排行" (good→bad ranking of all candidates):** score = `min(n_hits,10)/10*40 + max_p*30 + min(bio,1)*20 + (1-AMES)*5 + (1-carcinogens)*5` (i.e. 40% target-count capped at 10, 30% best hit probability, 20% ADMET-AI bioavailability, 10% low toxicity). Output a numbered table (排名/英文名/靶点数/最高概率/生物利用度/评分), Top-3 explanation (phenolic acids + small phenols win: absorption × target-hits), bottom-5 explanation (phosphorylated intermediates, zero-hit glycosides). Save full ranking to CSV. Phenolic acids (Syringic/Gallic) and small phenols (Hydroquinone) consistently top the antioxidant ranking; MW>500 大分子 are excluded by design.

## Ready-made scripts & references

- `scripts/step1_pubchem.py` — batch PubChem name → SMILES lookup (rate-limited, name-cleaning fallback). **Parses `ConnectivitySMILES`** (see Pitfall 1). Outputs `pubchem_smiles.json`.
- `scripts/step7_tcmsp.py` — batch TCMSP OB/DL/BBB/Caco2/HL lookup (token + `qn=` detail page; verified 2026-08), writes `tcmsp_adme.csv`. Reads `类药性筛选结果.csv`.
- `scripts/step2_lipinski.py` — RDKit descriptor computation + screening, writes `类药性筛选结果.csv` with `utf-8-sig` (Excel-safe). Reads `pubchem_smiles.json` from step1.
- `scripts/uniprot_mapping.py` — gene→canonical UniProt mapping (Step 4, `reviewed:true`), writes CSV.
- `scripts/step8_go_targets.py` — batch UniProt GO-term query (disease-target gene sets; bare `(GO:...)` syntax, verified 2026-08).
- `templates/echarts_network.html` — force-directed 成分-靶点 network graph template (fill `nodes`/`links` JSON).
- `references/pubchem-pug-api.md` — PubChem PUG REST API quirks and correct usage.
- `references/antioxidant-targets.md` — curated antioxidant / oxidative-stress gene list (Nrf2-ARE core + classic enzymes + inflammation crosstalk).
- `references/stp-browser-automation.md` — STP browser-automation recipe (JS-set-value trick, batch loop, job-URL curl shortcut, timing).
- `references/lipid-smiles-construction.md` — manual SMILES construction for MS-lipid shorthand (`Dgdg/Pe/Gpetn/Pa`) when databases fail: verified complete SMILES + MW checks + the don't-string-slice pitfall.
- `references/beginner-tutorial.md` — 小白入门教程库: 8-step 大白话 pipeline, 12-parameter ADME table, analogy bank (Nrf2消防/手性/DL看脸), Gentiopicroside→NFE2L2 hands-on exercise with real data, beginner FAQ. Use when the user asks to be taught.

Worked example (this user's data, FULL-scale 2026-08): 138 MS-metabolites → 126 PubChem hits → 72 候选 + 54 糖苷/脂质 + 12 待查 (lipids `Dgdg/Pe/Gpetn/Pa/Lpc` and glutathione conjugates are expected PubChem misses) → STP target prediction on **124 compounds** (only `Trp-Ala-Lys` tripeptide skipped — STP doesn't predict peptides) → **1781 compound-target associations** → ∩ antioxidant (GO 404 ∪ GeneCards 20 ∪ curated 16 = 416 genes) = **189 intersections / 46 genes / 98 compounds**. Hub targets: TNF(27), PTGS2/MMP2/SNCA(15), PRKCA(12), CA3/AKT1/KEAP1(7), **NFE2L2(4), NQO1, GSR, GSTP1/GSTA1/GSTO1** — Nrf2-ARE core fully represented. GO:BP top hit `response to oxidative stress` **p=1.41e-38** (46/46 genes).

**V2 full re-run (2026-08, after user deleted the folder and asked for 零缺口):** rebuilt data from conversation history → fixed 18 more comma-truncated names (including `VAR00508` `2-Hydroxy-3` → `2-Hydroxy-3,4-Dimethoxybenzoic Acid`) → **130/138 structures (94.2%)** → 74 候选 + 56 大分子 + 8 无结构 → ADMET-AI on all 74 → STP restored from browser-cache results files (124) + 6 freshly predicted = **130 compounds / 1871 associations** → antioxidant 404 GO ∪ 20 GeneCards = 406 genes → intersections deduped to best-probability-per-(compound,gene) = **159 edges / 42 genes / 78 compounds / 120-node network**. Hub targets v2: SNCA(17), MMP2/PTGS2(15), PRKCA(12), CA3(8), KEAP1(7), AKT1(7), CYP1B1/FYN/PTGS1(6). Note the dedup change (keep max probability per pair) lowers edge counts vs v1 — that is intentional and paper-safe. `Trp-Ala-Lys` stays skipped (tripeptide).

**V3 full-target re-run (2026-08, triggered by user's manual discovery):** the V2 STP capture only had the default Top-15 targets per compound. The user expanded one compound's list manually and found NQO1/PTGS2/AKT1 etc. below the Top-15 cutoff → re-captured all 74 候选 with the select-All trick (`sel.value='-1'` + change event, see stp-browser-automation.md) → **7031 associations (~95-100 targets/compound)** → intersections recomputed = **774 edges / 78 genes / 73 compounds / 151-node network**. Hub targets v3: PTGS2(62), HDAC6(50), MMP2(41), PTGS1(38), SNCA(35), CYP1B1(32), CA3(29), SRC(26), PTGES(26), PSMB5(25), PRKCA(24), FYN(23); NFE2L2(10), NQO1(7, incl. 7-Hydroxycoumarine p=0.194), G6PD(2, Wedelolactone p=1.0). **Moral: intersection/enrichment downstream of STP is only trustworthy with the FULL 100-target capture — Top-15 undercounts gene hubs by 2-4×.**

**Enrichment re-run on the full capture (2026-08, 78 intersection genes, g:Profiler via proxy):** GO:BP top = `response to oxidative stress` **p=6.65e-97** (78/78 genes), followed by cellular response to oxidative stress (7.6e-70), response to ROS (1.5e-53); KEGG top = Fluid shear stress & atherosclerosis (2.6e-12), Pathways in cancer (5.1e-12), **Chemical carcinogenesis - reactive oxygen species** (2.4e-11), TNF signaling (1.3e-9). These supersede the earlier 46-gene numbers (p=1.41e-38) as the canonical validation — expect p to collapse toward 1e-90+ as the gene set grows with full capture. Report tables: GO:BP Top-12 + KEGG Top-10 side by side in the HTML (grid2 layout), plus a 综合排行 Top-20 table (ranking CSV) integrated into the same self-contained report.

**V4 (2026-08): last-8-structures resolution → 136/138 (98.6%).** The 8 PubChem misses split as: 5 lipids (`Dgdg/Pe/Gpetn/Pa`), 1 amino-keto-acid (L-Alpha-Amino-Epsilon-Keto-Pimelate), 2 truly unrecoverable (xanthone derivative `1,5-Dihydroxy-8-Methoxycarbonyl-9-Oxoxanthene-3-Carboxylic Acid` and `Theaflagallin`). 6 of 8 were resolved by MANUAL SMILES construction (see `references/lipid-smiles-construction.md`): RDKit-validated MWs (PE 756, PA 715, DGDG 941, Gpetn 789/791, amino-keto-acid 189) confirm correctness. **Before declaring any compound unrecoverable, exhaust ALL databases** — for these 2 the full evidence trail was: PubChem (original + variant names), HMDB (curl 403, browser `unearth` returned empty), ChEBI (`advancedSearchForward.do?searchString=` → "Total Record(s): 0"), KEGG (`rest.kegg.jp/find/compound/` → 1B empty), MassBank (4KB empty), Google full-text (no compound entry), ChemSpider (404 anti-bot). Both are tea-fermentation-specific / multi-substituted rare metabolites absent from ALL general chemistry databases — a genuine coverage gap, not a lookup failure. The user accepted 136/138 ("A") after seeing the evidence; report honestly ("数据库未收录"), never fabricate. Don't propose approximate-structure substitutes unless the user asks (they explicitly rejected 近似). Note these built lipids are all MW>500 → they land in the 大分子 bucket, NOT the candidate ranking (lipids are membrane components, not antioxidant actives — don't push them through STP). LIPID MAPS front-end exact-name search 404s and SwissLipids/HMDB searches returned nothing for lipid shorthands — manual construction (glycerol backbone + fatty-acyl chains + head group as ONE complete SMILES, never string-sliced) was the only route that worked.

Run with the uv-managed venv python (NOT the Hermes bundled `venv/Scripts/python`):
```bash
"/c/Users/<user>/AppData/Local/hermes/hermes-agent/.venv/Scripts/python.exe" step1_pubchem.py
```

## Pitfalls (hard-won)

1. **PubChem JSON property key is `ConnectivitySMILES`, NOT `CanonicalSMILES`.** Using `CanonicalSMILES` silently returns empty strings while CID/formula look fine → 0% hit rate. Always parse `ConnectivitySMILES`.
2. **NEVER split chemical names on commas.** `Glycerol 1,3-Dihexadecanoate` contains commas as part of its name; splitting yields `Glycerol 1` and PubChem returns plain glycerol (MW 92) — a silently WRONG structure. Only strip commas when they delimit a parenthetical qualifier; if a name has a comma inside, query the full name first, then fall back to stripping `, ...` suffixes only for names where the comma clearly introduces a second entry.
3. **Expect ~80% first-pass PubChem hit rate.** Names with `''` (double-prime), brackets `[...]`, or salts (e.g. `... Sodium Salt`) fail name lookup. Collect misses (26/138 in first pass) into a manual-review list; use the clean-name fallback (strip quotes/primes/leading numbers) before giving up.
4. **Sugar glycosides legitimately violate Lipinski** (MW 500–800, HBD 6–12). Do not discard — bucket them separately; aglycone may be the active form.
5. **Run Python as script files in background, not `python -c` one-liners in the terminal tool** — one-liners can hang/block on approval. Write the script with `write_file`, run with `terminal(background=true)`, redirect stdout to a file (`> out.txt 2>&1`), then `read_file` the output. Background-process stdout is truncated in the log; the file redirect is mandatory for full results.
6. **uv-created venvs have NO pip.** `uv sync`/`uv venv` produces a venv without pip; `python -m pip install` fails with "No module named pip". Install packages with `uv pip install <pkg>` (auto-targets the active `.venv`).
7. RDKit import is slow (~10-30s first load) — don't assume hang; give background runs generous timeouts.
8. On this user's Windows box: `python3` is not on PATH — use `python` (3.11); MSYS paths (`/c/...`) work in terminal but `write_file`/`read_file` need native `C:/...` paths.
9. **Run multi-step batch jobs as ONE background task** (`step1.py && step2.py && step3.py` chained with `&&` inside a single `terminal(background=true, notify_on_complete=true)`, stdout redirected to a file). Separate sequential background calls get interrupted between steps (observed mid-batch), leaving a stale partial output. After completion, read the output file — don't rely on the background log (truncated).
10. **CSV fields containing commas MUST be quoted** — names like `2'',6''-Diacetylorientin`, `3,4-Dihydroxyphenylpyruvate` silently truncate to `2''` / `3` when unquoted, then PubChem returns garbage structures. When hand-writing the compound CSV, wrap every comma-containing name in double quotes; when generating via `csv.writer`, quoting is automatic — do NOT hand-concatenate CSV lines. This bug poisoned 26 "not found" results and 2 wrong candidate structures (glycerol instead of the diglyceride) before it was caught.
11. **ChEMBL `pref_name=` is FUZZY-matched** — every query in a 72-compound batch returned the same fallback molecule (CHEMBL6329) with zero targets. Even `molecule_synonym=` returns odd matches. ChEMBL known-activity coverage for MS metabolites is low anyway; treat it as optional, never as the primary target-prediction source (STP is).
12. **Downstream steps must read the FULL prediction CSV.** After expanding STP coverage (20 → 124 compounds), `step9_intersect.py` kept reading the old `stp_predictions.csv` (20-compound file) and silently returned the stale 28-edge intersection. Fix: point it at `stp_predictions_all.csv` and re-run the whole chain (`step9 → step10 → step12`) in ONE chained background task. When coverage grows, grep every script for hardcoded input filenames before re-running.
13. **Resume-cache poisoning after data fixes.** A `step1_structures.json` resume cache stores FAILED entries (name truncated, `smiles: null`). After fixing the CSV, re-running with `if var in done: reuse` silently reuses the stale null-SMILES entries — hit rate stays at the broken level (108/138). Fix: DELETE the JSON cache (or make resume skip only entries with non-null smiles) before re-running after any source-data fix. Symptom to watch for: "未查到" list still shows truncated names even though the CSV is fixed.
14. **ADMET (absorption/metabolism/toxicity) is a REQUIRED stage this user explicitly wants filled** — TCMSP OB/DL is query-table (32% coverage on MS metabolites) and the user correctly rejects "查不到就不查". The calculation-based route: SwissADME (GI absorption, bioavailability score, solubility) or **ADMET-AI** (local ML model, batch 72+ SMILES in one run: absorption + metabolism + toxicity). Install ADMET-AI with `uv pip install admet-ai` — Tsinghua mirror timed out for this package; use official PyPI behind the VPN proxy (`export HTTPS_PROXY=http://<YOUR_PROXY:PORT>  # e.g. local VPN proxy`). **GOTCHA: a global `uv.toml` with `[pip] index-url = <mirror>` OVERRIDES the HTTPS_PROXY env var — uv keeps hitting the dead mirror. Delete `%APPDATA%\uv\uv.toml` (or run without it) before installing; re-create it afterward if needed.** ~1GB deps (torch); CPU inference is fine for a few hundred compounds. Use its outputs (GI absorption, toxicity classes) as a soft filter alongside Lipinski — same logic as OB/DL: flag Low-absorption/High-toxicity compounds, don't hard-delete on a single prediction. **ADMET-AI v2 output columns DIFFER from the docs** — verify with `avail = [c for c in key_cols if c in preds.columns]` and dump `sorted(preds.columns)` once. Verified real names (2026-08): `Bioavailability_Ma` (absorption), `Caco2_Wang` (gut permeability), `BBB_Martins`, `CYP1A2_Veith`/`CYP2C9_Veith`/`CYP2D6_Veith`/`CYP3A4_Veith`/`CYP2C19_Veith` (metabolism), `CYP2C9_Substrate_CarbonMangels` etc., `Clearance_Hepatocyte_AZ`, `hERG` (cardiotox), `AMES` (mutagenicity), `Carcinogens_Lagunin` (carcinogenicity), `Pgp_inhibitor`. ~104 columns total; pick ~15. Screening rule used: Bioavailability > 0.5 green, AMES < 0.5 green.
15. **Regex block-splitting truncates compound names with commas/primes in results files.** Parsing STP batch output with `re.split(r'@@@@@\s+([A-Za-z0-9_\-]+)\s+@@@@@', text)` silently truncates block names like `2,3-Dehydrosilychristin` → `2` and `3,4-Dihydroxyphenylpyruvate` → `3` (`,`/`'` not in the char class), so name-mapping fails and those compounds stay "missing" forever despite having results. Fix: use a LOOSE split regex `re.split(r'@@@@@\s*(.+?)\s*@@@@@', text)` and match the safe-name→real-name map against the full block name. Symptom: after a successful STP run, the parse says N compounds still missing even though the result file has "Target Classes" in their blocks.
16. **HTML report with the network graph MUST be self-contained for this user (China network + preview pane).** Two independent blank-graph failures observed: (a) the ECharts jsdelivr CDN (`cdn.jsdelivr.net`) is unreachable → graph div renders empty, no visible error; (b) even after downloading `echarts.min.js` next to the HTML, the open_preview pane does NOT resolve the relative `src="echarts.min.js"` → still blank. The only approach that worked: read the downloaded `echarts.min.js` as text and inline it into the HTML, replacing `<script src="echarts.min.js"></script>` with `<script>…full ~1MB source…</script>`. Result: a ~1.06MB self-contained report that renders in the preview pane, offline, and on any machine. Verify before delivering: open the HTML in a real browser and check `document.querySelectorAll('#net canvas').length > 0` (ECharts renders to canvas). Generalize: any HTML deliverable for this user gets external JS/CSS inlined — never CDN, never relative-path.
17. **Hand-written JS inside HTML templates WILL have brace-imbalance bugs — validate before delivering.** Real failure: the ECharts tooltip line in `report_template.html` had one extra `}` (`...:'');}}},` instead of `...:'');}},`) → browser console `Uncaught SyntaxError: missing ) after argument list`, entire script dead, blank graph with NO other symptom. Fix workflow that worked: (a) extract the main script block with `re.findall(r'<script>(.*?)</script>', html, re.DOTALL)` and count braces in Python (`main.count('{') == main.count('}')`, also parens) — imbalance pinpoints the line; (b) write the script to a temp `.js` file and run `node --check <file>` for exact line numbers (node lives at `C:\Users\<user>\AppData\Local\hermes\node\node.exe` on this box; the Hermes `node` on PATH is not the same); (c) fix the TEMPLATE (not the generated HTML — the next regeneration must inherit the fix) and re-run the generator + inline step. NOTE: the browser `file://` origin warning (`Unsafe attempt to load URL file:///...`) is benign — the SyntaxError is the real issue. Also: when the user deletes the report file outright, regenerate from the template + data scripts (all in `02_脚本/`), never hand-rebuild.

## Visualization preference (this user)

When outputting results as an HTML report/diagram:
- **For 网络药理学 the deliverable is an interactive 成分-靶点关联图: ECharts force-directed graph (圆圈节点 + 线条连线), NOT a static table.** `type:'graph', layout:'force'`, categories 活性成分 (purple #8b5cf6) vs 靶点 (green #34d399), hub targets (degree ≥ 3) enlarged + amber #fbbf24, `roam:true draggable:true`, `emphasis.focus:'adjacency'`. Template: `templates/echarts_network.html` (fill nodes/links JSON from real prediction data). ⚠️ **Do NOT load echarts from the jsdelivr CDN — it is unreachable for this user in China and the graph renders blank.** Make the report self-contained: `curl -sL https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js -o echarts.min.js` (~1MB, HTTP 200 works from a proxy/terminal even when the browser pane can't), then INLINE the file contents into the HTML — see Pitfall 16. Pie/bar/funnel ECharts supplements are welcome but the network graph is the centerpiece.
- Layout must be **element-by-element non-overlapping** — clean rows/columns with generous spacing; no SVG boxes or arrows crossing each other. User rejects overlapping diagrams explicitly.
- **Building the report HTML: do NOT use an f-string with JS inside** — the JS `{ }` braces collide with f-string syntax (SyntaxError: single '}' is not allowed). Pattern that works (v2): write a `report_template.html` with `__PLACEHOLDER__` tokens (`__NODES_JSON__`, `__GENE_ROWS__`, ...), then in Python do `doc = tpl; for k,v in {...}.items(): doc = doc.replace(k, v)`. This also keeps the big HTML out of the script file.
- **Include ALL specific data** — full tables (every compound row with values), parameters, and stats. User dislikes summarized-only reports ("我要论文完整的，且加入论文中的具体数据").
- **User may ALSO ask for a plain-text table "按原来的顺序"** (original input order). Deliver a fixed-width aligned `.txt` (序号 | VAR | name | MW | LogP | Violations | 类药性 | TCMSP-OB | TCMSP-DL | STP交集靶点), one line per original row + a trailing 统计 line. Chinese headers fine in txt; write via a generator script (step13 pattern), UTF-8.
- Save outputs under `Desktop/网络药理学/` (2026-08 reorg — user deleted the old `Desktop/学术工具/网络药理学/` and rebuilt): `01_数据/` (CSVs + JSON), `02_脚本/` (step scripts), `03_报告/` (final HTML), `工具/` (installed tools). Step scripts live in `02_脚本/` and write to `01_数据/`. When the user says they deleted the project folder, recover raw data from conversation history and RE-VERIFY every comma-containing field gets quoted (see Pitfall 10) — hand-restored CSVs silently truncate names again.

## User workflow preferences (this user)

- **先讨论再行动** — propose the plan (databases, screening criteria, visualization form) and get explicit approval before executing. User may repeat this demand several times when they feel the agent is moving without discussion.
- **Model-switching strategy**: user runs light prep work (downloads, tool installs, data fixes) on `deepseek-v4-flash` to save cost, then switches to `deepseek-v4-pro` for the real analysis. REMIND the user to switch models before starting automated multi-database queries — they asked to be notified at that point.
- **Wants MANY databases** ("所有的网站都可以多弄几个") — multi-database coverage per stage: components (TCMSP + SwissADME), target prediction (STP + PharmMapper + SEA), disease targets (GeneCards + OMIM + DisGeNET), network/enrichment (STRING + Metascape + DAVID). Don't propose a minimal single-DB route when the user can afford breadth.
- **Division of labor (2026-08)**: when teaching/verifying, the user often wants to look things up HIMSELF in Edge ("我去用edge上面的网站去查") while the agent runs the batch pipelines in parallel. Give him precise click-by-click instructions (URL → what to type → what to look for) for HIS compound, and keep the automation running on your side; he reports back findings to compare.
- **Full re-run requests**: if the user says they deleted everything and wants a complete re-screen "零缺口", rebuild data from conversation history, re-verify CSV quoting, DELETE stale resume caches, and run the full chain fresh — do not assume old artifacts survive.
- **The deliverable is a WORK screening, NOT a thesis** (user: "这不是写什么论文，138是工作要找到好的筛选"). Frame every result as 分档 tiers (优秀 Top10 / 良好 / 一般 / 差 + 大分子前体 bucket + 未收录 note), lead with the actionable conclusion ("你的样品主力活性成分是酚酸类"), and offer a copyable Excel/CSV of the ranking. Skip paper-writing framing (材料与方法 etc.) unless the user asks.
- **Audit EVERY web tool for default-view truncation before trusting downstream numbers** (user's own lesson: "看其他的网址会不会也出现这样的情况"). Known traps: STP default Top-15 of 100 (fix: select All), GeneCards default 20 rows (pagination widget ignores clicks — ask user for their own top-50 list or combine GO gene sets for breadth), UniProt stream returns full sets (fine). Every time a new database enters the pipeline, check its default page size / result cap.
- browser_exec code comments must be pure ASCII — Chinese comments trigger UnicodeDecodeError in the browser-use CLI on this user's Windows box (GBK stdin).

## Teaching mode (小白 onboarding) — how to teach this user

The user is a **self-described 网药 小白** and explicitly asks to be taught ("开始入门讲解", "我是小白"). When that happens, deliver a structured beginner LESSON, not another analysis. Preferences, hard-won:

- **Hands-on practice over theory** ("我喜欢实践"): give a walkthrough of the actual websites — which URL to open, what to type into which box, what to look at, and where to take the info next (chain: PubChem → TCMSP → STP → GeneCards → Venny → STRING → g:Profiler). Use a REAL compound from their project as the exercise (Gentiopicroside / VAR00338 is the star: it hits NFE2L2).
- **Number every step** ("编号带上"): steps ①–⑧, numbered 速查卡, checkbox homework table. User explicitly requested numbered formats.
- **大白话 + analogies for every concept**: 网药=社交圈查关系, Lipinski=食材安检, OB=好消化, DL=看脸打分, NFE2L2=消防总指挥, @=左右手, GeneCards搜antioxidant=图书馆查书. These land; abstract definitions do not.
- **Teach the 12 TCMSP ADME parameters** (MW/AlogP/TPSA/Hdon/Hacc/OB/Caco-2/BBB/DL/HL/RBN/FASA-) when the user hits a TCMSP table — one-line plain-language meaning + standard + 比喻 each.
- Answer beginner FAQs immediately, with the project's real numbers (the full FAQ bank is in `references/beginner-tutorial.md`): what the 138 metabolites ARE (LC-MS metabolomics output; VAR=software auto-ID, neg_/pos_=ion mode), SMILES 栏 location (Computed Properties; or the REST URL `.../property/CanonicalSMILES/TXT` trick), what `@` means, why DL is "有意思" (Tanimoto similarity vs 652 known drugs; high DL ≠ active), NFE2L2=Nrf2 master switch, how GeneCards keyword search works, Venny List1/List2 contents, STRING steps, and how many genes to paste (15–30 for STRING, ALL for enrichment).
- Keep replies emoji-rich (user explicitly requested "多发点emoji").
- When the user asks "给我一个好的一个不好的" (a good vs a bad compound, to copy and compare himself): deliver a copyable side-by-side comparison table — one strong antioxidant candidate (e.g. Syringic Acid: OB 47.78%, CA3+SNCA hits at p=1.0, Lipinski 0 violations → 值得研究) vs one weak (e.g. Carboxydextran: large polysaccharide, no TCMSP entry, zero antioxidant-target hits → 淘汰), with the 对比逻辑 (分子大小/吸收/靶点/活性基团 → 结论) spelled out so the pattern transfers to any pair. **⚠️ Only label a compound "差的/无抗氧化命中" AFTER the FULL 100-target STP capture** — the Top-15 default view hid NQO1/PTGS2/AKT1 etc. for 7-Hydroxycoumarine, which the user found by expanding the list manually; a compound judged "0 hits" from Top-15 data will be wrong. The comparison walkthrough should teach the user to click the STP "Show All" select (see stp-browser-automation.md) and read probabilities from the FULL list.
- End lessons with a 一句总结 + optional paper-writing tip (e.g. 材料与方法: "UHPLC-Q-TOF-MS/MS 代谢组学分析，VIP>1, p<0.05").

## TCMSP API (verified 2026-08, NEW site — direct curl, no browser needed)

Site: `https://tcmsp-e.com/` (old `old.tcmsp-e.com` is dead; must use https).

```
# ① Get token from homepage (refreshes per session; re-grab before each batch run)
GET https://tcmsp-e.com/tcmsp.php
  → regex: name="token" value="([a-f0-9]{32})"

# ② Search by chemical name — GET form, NOT JS/AJAX (page's kendoGrid data is server-rendered)
GET https://tcmsp-e.com/tcmspsearch.php?qs=molecule_name&q={Name}&token={TOKEN}
  → hits embedded in JS: {"MOL_ID":"MOL000513","molecule_ID":"513","molecule_synonyms":"Gallic acid"}

# ③ Detail page — parameter is qn=<molecule_ID>, NOT molID (molID/molecule_ID variants → "Molecule" not exist)
GET https://tcmsp-e.com/molecule.php?qn=513
  → ADME embedded as JS JSON: {"ob":"31.69","dl":"0.045","mw":"170.13","alogp":"0.632",
     "tpsa":"97.99","hdon":"4","hacc":"…","bbb":"-0.54","caco2":"-0.09","halflife":"11.78","FASA":"0.41"}
```

Screening: OB ≥ 30%, DL ≥ 0.18. Expect partial coverage — many MS metabolites (glycosides, lipids) are not in TCMSP; combine with Lipinski results.

## ChEMBL API (known-activity targets, direct curl, no key)

⚠️ **2026-08: `molecule.json?smiles=` returns EMPTY results for everything, even caffeine** (tested through this user's proxy — `{"molecules": [], "total_count": 0}`). The SMILES-lookup path is unreliable in this environment; do not build a pipeline on it. **Use name lookup instead, which works:**

```
# name → activities (works, verified)
GET https://www.ebi.ac.uk/chembl/api/data/activity.json?molecule_synonym={Name}&limit=5
# each activity: target_chembl_id, target_pref_name, target_organism, pchembl_value, standard_type
```

If the SMILES path ever works again, the flow is: `molecule.json?smiles={SMILES}&limit=1` → `molecule_chembl_id` → `activity.json?molecule_chembl_id={ID}&limit=50`. Filter `target_organism` containing "Homo sapiens". Rate-limit ~0.4s/request, wrap EVERY compound in try/except (a single failure must not kill the batch), and route through the VPN proxy (urllib `ProxyHandler` for http/https `<YOUR_PROXY:PORT>`) — direct connection stalls and the process gets SIGTERM'd mid-run.

## Intersection & enrichment (STRING PPI + g:Profiler, verified 2026-08)

**Intersection logic (step9)**: STP's `common` column IS the gene symbol (e.g. CA2, TNF). Intersect `set(common names)` against the disease gene set (GO genes ∪ GeneCards ∪ curated core). Score sources per hit (`GO`/`GeneCards`/`核心`). Hub targets = degree ≥ 3 in the compound-gene network (full-scale session: TNF×27, PTGS2×15, MMP2×15, SNCA×15, PRKCA×12, KEAP1×7, AKT1×7, **NFE2L2×4**; the killer biological hit is Gentiopicroside→NFE2L2, the Nrf2 master switch, cross-confirmed by GeneCards score 114.6).

**g:Profiler enrichment — API works THROUGH the VPN proxy** (direct connect times out):
```python
POST https://biit.cs.ut.ee/gprofiler/api/gost/profile/   # proxy <YOUR_PROXY:PORT>
JSON: {"organism":"hsapiens","query":["SNCA","TNF",...],
       "sources":["GO:BP","KEGG","GO:MF","GO:CC"],"user_threshold":0.05}
# → {"result":[{source,native,name,p_value,term_size,query_size,intersections}]}
```
⚠️ `intersections` is a NESTED list `[[gene, evidence_code], ...]` — flatten with `x[0] if isinstance(x,list) else x`. The GO:BP top hit validating antioxidant work was `response to oxidative stress` (p=2.29e-14) — expect the top GO:BP terms to echo the disease theme; that's the built-in sanity check.

**STRING PPI — also through the proxy**:
```
GET https://string-db.org/api/tsv/network?identifiers=SNCA%0dTNF%0d...&species=9606&required_score=400&network_type=physical
# returns TSV (header: stringId_A stringId_B ... score ... experiments ... database)
```
Small gene sets (~14) yield few edges at score 400; lower to 150 or drop `network_type=physical` for more. Write result to `string_ppi.csv`.

**Enrichr API is DEAD (2026-08)**: `maayanlab.cloud/Enrichr/addList` POST returns HTML (not JSON), `speedrichr/api/addList` returns 500. Do not build on it; g:Profiler via proxy is the working enrichment route.

## Database reachability matrix (tested 2026-08, this user's box)

| Status | Databases |
|---|---|
| ✅ Direct curl OK | PubChem, UniProt, ChEMBL, TCMSP, SwissADME, BATMAN-TCM, ETCM, pkCSM, Metascape, Enrichr(site), KEGG, CTD, OpenTargets, PubMed, STRING(302), DisGeNET(301), TTD(302), PharmMapper(301) |
| 🔶 Proxy-only API | g:Profiler (`biit.cs.ut.ee/gprofiler/api/gost/profile/`), STRING (`string-db.org/api/`), SEA (React SPA, ~6.5s via proxy) |
| 🔶 403 anti-bot (browser automation needed) | GeneCards, OMIM, HMDB |
| 🧩 JS-heavy, no usable REST API | SwissTargetPrediction (`api.php`/`predict.php` 404 or HTML; async one-at-a-time), SEA (captcha-gated endpoints `/api/submit`, `/api/result`) |
| ❌ Broken/dead | DAVID (timeout → use Metascape), Enrichr API (returns HTML / 500 → use g:Profiler), Super-PRED (timeout → use STP) |

## Target prediction & disease-target mapping

- **SwissTargetPrediction (STP) is NOT curl-scriptable**: `api.php` returns 404, `predict.php` POST returns an HTML page with NO job ID (job is assigned client-side). Don't waste time probing the API. **Browser automation IS the way, validated at 124-compound scale (2026-08)** — see `references/stp-browser-automation.md` for the exact loop. Key facts:
  - **VALIDATED fill method (browser-use CLI 3.0): `js("document.querySelector('#smilesBox').focus()")` + `type_text(smi)` + `js("...dispatchEvent(new Event('input',{bubbles:true}))")`, then click `#submitButton`.** `fill_input()` is dead in 3.0 (box value stays EMPTY) and bare JS value-set without events never registers (page stays on home → "Provide a SMILES before submitting"). `js()` takes NO extra args — string-concat values into the expression.
  - **⚠️ MANDATORY: capture ALL 100 targets, not the default Top 15.** The result table defaults to "Showing 1 to 15 of 100 entries" — Top-15 capture silently drops ~85% of targets and undercounts intersections badly (42 → 78 genes after fix). After the result page loads, expand the table: `sel = document.querySelectorAll('select')[0]; sel.value = '-1'; sel.dispatchEvent(new Event('change',{bubbles:true}))` (`-1` = "All"), wait 4s, THEN read `js("document.body.innerText")`. The DataTables "Show 50/All" buttons ignore click(); only the underlying `<select>` responds. Full re-run went 1871 → 7031 associations. See `references/stp-browser-automation.md`.
  - Wait ~26-30s, then read `js("document.body.innerText")` — targets (Target \t Common name \t Uniprot ID \t ChEMBL ID \t class \t probability) are in the text. Success marker: `"Target Classes" in innerText`.
  - The result URL is `result.php?job=<JOBID>&organism=Homo_sapiens` — **once you have a job ID, `curl -sL "<that URL>"` fetches the full 119KB result page (all 100 targets) with no browser.** Batch loop: submit in browser, then curl each job URL for parsing.
  - Batch 5-6 per browser_exec call on a fresh session; **CDP degrades after ~40 navigations** (`Runtime.evaluate timed out` / `Cannot read properties of null`) — recover via Chrome restart + `browser-use --reload`, then drop to 2-3 per call with a box-presence retry loop. Re-queue failures by scanning the results file for blocks lacking "Target Classes".
  - Alternatives when browser is unavailable: ChEMBL name-query fallback (below), or generate `STP输入_候选成分.smi` (SMILES<TAB>name<TAB>VAR per line) for manual web submission.
- **Disease target gene→UniProt mapping** (needed for network nodes):
  `https://rest.uniprot.org/uniprotkb/search?query=gene_exact:{GENE}+AND+organism_id:9606+AND+reviewed:true&format=json&fields=accession,id,protein_name,gene_names&size=1`
  **Must include `reviewed:true`** or you get random isoforms (A0A... accessions) instead of canonical Swiss-Prot entries. When parsing a gene-list text file, strip everything after `#` (inline Chinese comments become garbage tokens otherwise). Script: `scripts/uniprot_mapping.py`.
- Curated antioxidant gene set (Nrf2-ARE + enzymes + inflammation crosstalk): `references/antioxidant-targets.md`.

### GeneCards disease-target scraping (browser automation, verified 2026-08)

GeneCards is 403 for curl but works in the browser (user must authorize Chrome remote debugging once: `chrome://inspect/#remote-debugging` → tick "Allow remote debugging" → click Allow twice).

- Search URL: `https://www.genecards.org/Search/Keyword?queryString=antioxidant` → redirects to `/search/results?q=antioxidant` (12,341 hits for "antioxidant").
- `page_info()["text"]` is EMPTY on this JS-rendered page. Extract with `js("document.body.innerText")` instead.
- The result table appears in innerText as TAB-separated rows: `1\tATOX1\tAntioxidant 1 Copper Chaperone\tProtein Coding\t296.4`. Parse with regex `(\d+)\t([A-Z0-9]+)\t(.+?)\t(Protein Coding|RNA Gene|Pseudogene)\t([\d.]+)`.
- Clicking the "100 per page" pagination control has NO effect (DataTables widget) — the default top-20 is enough; combine with the GO-term gene set below for breadth.
- Top hits for antioxidant (relevance score): ATOX1(296) > PRDX3/5/4/2/6/1(117-169) > NFE2L2(114.6) > KEAP1(108.7) > CAT(89.2) > SELENOP > PON2 > HP > GSR(80.5) > SOD3(80.0) > NFE2L1 > TP53 > ATM.

### UniProt GO-term batch query (disease targets without GeneCards)

Replaces manual gene-list curation — pull ALL reviewed human genes annotated to antioxidant GO terms:

```
GET https://rest.uniprot.org/uniprotkb/stream?query=(GO:0006979)+AND+organism_id:9606+AND+reviewed:true&format=tsv&fields=accession,gene_primary
```

⚠️ **Correct query syntax is `(GO:0006979)` bare** — `go:GO:...` AND `go_id:GO:...` both return HTTP 400 "query parameter has an invalid syntax". Useful antioxidant terms: GO:0006979 (response to oxidative stress), GO:0016209 (antioxidant activity), GO:0045454 (cell redox homeostasis), GO:0004601 (peroxidase activity), GO:0004784 (SOD activity), GO:0004602 (glutathione peroxidase activity). Script: `scripts/step8_go_targets.py`.

### browser_exec (Browser Use CLI) output quirks — all observed on this user's Windows box

- **`print()` output frequently comes back as `output: null`** even on success. ALWAYS write results to a file in `$BH_AGENT_WORKSPACE` (os.path.join(ws, "out.txt")) and read it back with read_file. print only for status markers.
- Code passed to browser_exec must be pure ASCII — Chinese comments break stdin decoding (UnicodeDecodeError, GBK on this box).
- Chrome needs one-time remote-debugging authorization; the harness prints the exact steps when it fails — relay them to the user.

## Related

- `academic-research-tools` — literature search (Semantic Scholar MCP, CNKI) and paper→HTML visualization workflow.
- `academic-paper` / `deep-research` — writing up the results as a paper.
