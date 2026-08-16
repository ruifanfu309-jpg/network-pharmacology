# SwissTargetPrediction — verified browser-automation recipe (2026-08)

Status: NO usable REST API. Browser automation is the working path; this recipe was validated at **124-compound scale** (final session run: 98/106 first-pass success + re-queue retries).

## Prerequisites

- User has authorized Chrome remote debugging (`chrome://inspect/#remote-debugging` → tick Allow → two Allow popups; harness prints these steps when it fails). **Chrome must be re-authorized (another Allow popup) every time Chrome is restarted** — expect it, relay the steps, don't assume it's a new problem.
- VPN/proxy not needed for STP (directly reachable); GeneCards in the same browser session needs the system proxy.
- browser-use CLI 3.0 is installed via `uv tool install browser-use --force`. **If pypi.org is blocked, install with the Tsinghua mirror: `export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple && uv tool install browser-use --force`** (a persistent mirror config also lives at `%APPDATA%\uv\uv.toml`). After a reinstall, the CLI may move from the old behavior to 3.0 — re-test one compound before launching a big batch.

## Per-compound loop — VALIDATED METHOD (browser-use 3.0)

`fill_input()` is dead in CLI 3.0 (returns None, box value stays empty) AND bare `js("box.value = ...")` without events does NOT register (page stays on the home screen, "Provide a SMILES before submitting"). The method that works at scale: **focus via JS + `type_text()` (CDP Input.insertText) + manual `input` event**:

```python
import os, time
ws = os.environ.get("BH_AGENT_WORKSPACE", ".")
outfile = os.path.join(ws, "stp_all_results.txt")

for item in batch:                       # each item: {"name":..., "smiles":...}
    goto_url("https://www.swisstargetprediction.ch/")
    wait_for_load()
    time.sleep(5-8)                       # page JS init; STP loads slowly
    # box-presence retry: page sometimes fails to render
    for attempt in range(3-4):
        if js("!!document.querySelector('#smilesBox')"):
            break
        time.sleep(8-10)
    if not js("!!document.querySelector('#smilesBox')"):
        raise RuntimeError("no smilesBox after retries")   # caught → FAIL, re-queued later
    js("document.querySelector('#smilesBox').focus()")
    time.sleep(0.5)
    type_text(smi)                        # CDP insertText — bypasses broken fill_input
    time.sleep(1)
    js("document.querySelector('#smilesBox').dispatchEvent(new Event('input', {bubbles:true}))")
    time.sleep(0.5)
    js("document.querySelector('#submitButton').click()")
    time.sleep(26-30)                     # prediction job takes 15-30s
    txt = js("document.body.innerText")
    if "Target Classes" not in str(txt):  # not done yet → wait more
        time.sleep(15-20)
        txt = js("document.body.innerText")
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(f"\n@@@@@ {safe_name} @@@@@\n" + str(txt)[:1700])
```

CRITICAL details that made or broke batches:
- **`js()` takes NO extra arguments in CLI 3.0** — `js("...value = arguments[0]", smi)` fails with "No target with given id found". String-concatenate the value into the JS expression instead.
- **`type_text()` needs the element focused first** (`js("...focus()")`); it inserts at the cursor via CDP, so focus is mandatory.
- Detect success by `"Target Classes" in innerText` (result page marker). If absent after the extra wait, the compound FAILED — do NOT count it; re-queue it.

## Batch sizing, degradation & recovery (learned at 124-compound scale)

- Fresh browser session: ~5-6 compounds per browser_exec call (each ≈ 40-45s; 6 ≈ 5 min < 700s timeout).
- **CDP/chrome connection degrades after ~40+ consecutive navigations** — symptoms: `Runtime.evaluate timed out`, `Cannot read properties of null (reading 'focus')`, "No target with given id found". Recovery: user restarts Chrome (re-authorizes Allow once), then `"<uv-tools-path>/browser-use.exe" --reload` (stops the stale daemon; it restarts fresh on next call). After recovery, DROP to 2-3 compounds per call and add the box-presence retry loop — sustained throughput beats batch size.
- **Re-queue pattern for failures**: keep the queue in a workspace JSON (`{"todo":[...]}`), pop the front N per call, append results to a shared results file, write the trimmed queue back. To retry, scan the results file for blocks whose body lacks `"Target Classes"` (or starts with ERROR), map safe-names back to compounds via the todo JSON, merge (dedupe by VAR) into the queue, and run again. Expect ~20% of a 100+ batch to need one retry.
- Sanitize compound names for block markers: keep only `[A-Za-z0-9 _-]`, replace spaces with `_`, truncate to 40 chars — chemical names contain `'`, `''`, `(`, `)`, `,`, `/` that would otherwise break `@@@@@` splitting.
- `goto_url()` back to the STP homepage between compounds — the form/page state resets.
- Wait time: 21s worked for small phenolic acids; large glycosides need 25-30s. Big molecules (glycosides >500 Da) sometimes legitimately return no targets — if the page shows the result table but all probabilities are low/absent, that's a real "no targets" result, not a failure.

## Result format — ⚠️ TOP 15 IS NOT ENOUGH (major finding, 2026-08)

innerText rows (TAB-separated):

```
Target\tCommon name\tUniprot ID\tChEMBL ID\tTarget Class\tProbability*\tKnown actives (3D/2D)
Carbonic anhydrase 2\tCA2\tP00918\tCHEMBL205\tLyase\t1.0\t273 / 92
```

**CRITICAL: STP predicts 100 targets per compound, but the result table DEFAULTS to showing only 15 ("Showing 1 to 15 of 100 entries").** Capturing `document.body.innerText` without expanding the table silently loses ~85% of the target list. A user's manual full-list check caught antioxidant genes (NQO1 p=0.194, PTGS2 p=0.42, AKT1, SRC, CYP1B1, HSPA1A, PSMB5) that were ALL below the Top-15 cutoff — the intersection analysis built on Top-15 data was badly undercounting (42 genes → 78 genes after re-capture, nearly 2×). Earlier advice in this file ("Top 15 is sufficient") is WRONG — do not trust it.

**The DataTables "Show 50/All" buttons DON'T respond to click(), but the underlying `<select>` DOES respond to a value set + change event.** VALIDATED fix — after the result page appears, run:

```python
js("""
(() => {
  const sel = document.querySelectorAll('select')[0];
  if (sel) { sel.value = '-1'; sel.dispatchEvent(new Event('change', {bubbles:true})); }
})()
""")
time.sleep(4)
txt = js("document.body.innerText")   # now contains ALL ~100 targets
```

`-1` is the select's value for "All" (options are 15=15, 25=25, 50=50, All=-1). Verify success by counting target rows in the captured text (regex `\t([OPQ][0-9][A-Z0-9]{4}|[A-NR][0-9][A-Z0-9]{3}[0-9]|[A-Z0-9]{6})\t(CHEMBL\d+)\t` should find ~95-100). A 74-compound full re-run captured 7031 associations vs 1871 for the Top-15 version — the full capture is mandatory for any intersection/enrichment downstream.

## curl shortcut for the full result page

The browser lands on `https://www.swisstargetprediction.ch/result.php?job=<JOBID>&organism=Homo_sapiens`.
That URL is directly curl-able (119KB HTML, all 100 targets server-rendered):

```bash
curl -sL "https://www.swisstargetprediction.ch/result.php?job=1087144002&organism=Homo_sapiens" \
  -H "User-Agent: Mozilla/5.0" -o stp_job.html   # HTTP 200
```

Parse with regex on the `Target\t...\tProbability` rows. So the fastest hybrid: browser submits, you curl each job URL and parse in Python. (The select-All browser route above is the alternative when job IDs aren't being tracked.)

## Gotchas that burned batches

1. `fill_input("#smilesBox", smi)` → page says "Provide a SMILES before submitting" — value never landed (broken in CLI 3.0 too: value stays EMPTY). Use focus + type_text.
2. `js("box.value = smi")` WITHOUT dispatching events → framework never sees the change, page stays on home. Events (`input` + `change`) are mandatory.
3. `js(expr, args)` with arguments → "No target with given id found". String-concat only.
4. Do NOT probe `api.php` / `api/v2/predict` (404) or `predict.php` POST expecting a job ID in the response (it's client-side assigned). The job ID only appears in the result-page URL after the browser submits.
5. Chinese comments anywhere in browser_exec code → UnicodeDecodeError on this user's box (GBK stdin). Pure ASCII only.
