# PubChem PUG REST API — compound lookup quirks

Base URL: `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/<name>/property/<props>/JSON`

## Correct property key

**Use `ConnectivitySMILES`** — the JSON response key is `ConnectivitySMILES`, NOT `CanonicalSMILES`.
Requesting `CanonicalSMILES` returns a JSON with CID/MolecularFormula/MolecularWeight populated but
`smiles` empty → looks like success, yields 0 usable structures.

```json
// GET /compound/name/Gallic Acid/property/ConnectivitySMILES,MolecularFormula,MolecularWeight/JSON
{
  "PropertyTable": { "Properties": [ {
    "CID": 370,
    "MolecularFormula": "C7H6O5",
    "MolecularWeight": "170.12",
    "ConnectivitySMILES": "C1=C(C=C(C(=C1O)O)O)C(=O)O"
  } ] }
}
```

## Other quirks

- **TXT output is limited to ONE property** (`Status: 400 ... TXT output is limited to a single property`).
  Use JSON for multi-property requests.
- **Name lookup returns exactly one best match**; for ambiguous or exotic names it 404s.
- Handle 404 by trying a cleaned candidate name before giving up.
- Rate limit: keep ≥ 0.3 s between requests in batch scripts; batch 138 names took ~3 min.
- Chemical names that trip the lookup:
  - double-prime `''` (e.g. `2'',6''-Diacetylorientin`)
  - bracket descriptors `[...]` (e.g. `Isorhamnetin 3-O-[B-L-Rhamnofuranosyl-(1->6)-D-Glucopyranoside]`)
  - salt suffixes (e.g. `Formononetin-B-D-Glucuronide Sodium Salt`)
  - lipid shorthands (e.g. `DGDG(18:2/18:2)`, `PE(18:1/18:2)`) — no name match; resolve via structure if needed.

## Name cleaning — the comma trap

**Do NOT blindly split chemical names on commas.** `Glycerol 1,3-Dihexadecanoate` has a comma
inside its name; splitting on `,` yields `Glycerol 1` → PubChem returns plain glycerol (MW 92),
a silently WRONG structure for a lipid of MW ~800.

Safe cleaning order (only when full-name lookup 404s):
1. Strip `''` / `"` / `'` quote variants.
2. Strip leading numeric/dash prefixes (`2-`, `3-`...).
3. Only then consider the comma suffix, and only when the comma clearly separates a second
   entry rather than being part of the nomenclature (heuristic: if the pre-comma token is a
   bare fragment like `2` or `Glycerol 1` with no second word, treat as truncation, not a fix).

## Reference script skeleton

```python
def query_pubchem(name, retries=3):
    q = urllib.parse.quote(name)
    url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{q}/"
           f"property/ConnectivitySMILES,MolecularFormula,MolecularWeight/JSON")
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                props = json.loads(resp.read().decode())["PropertyTable"]["Properties"][0]
                return {"name": name, "cid": props.get("CID"),
                        "smiles": props.get("ConnectivitySMILES", ""),
                        "formula": props.get("MolecularFormula", ""),
                        "mw": props.get("MolecularWeight", "")}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                break
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return {"name": name, "error": "not_found"}
```
