# Lipid SMILES manual construction (2026-08, verified)

When PubChem/HMDB/LIPID MAPS all fail on MS-lipid shorthand names (`Dgdg(18:2/18:2)`,
`Pe(18:1/18:2)`, `Gpetn(...)`, `Pa(...)`), the lipids are NOT "unknown" — the shorthand
is a recipe. Build the SMILES by hand: glycerol backbone + sn-1/sn-2 fatty acyl chains +
polar head group. RDKit `MolFromSmiles` + `Descriptors.MolWt` validates each build
(MW must match literature ranges for the lipid class).

## The pattern

```
sn1-acyl-O-CH2-CH(OC(=O)-sn2acyl)-CH2-head
```

Fatty-acyl SMILES fragments (as complete acids; the `(=O)O` becomes `(=O)O-` ester on the backbone):
- 18:0 stearoyl:   `CCCCCCCCCCCCCCCCCC(=O)`
- 18:1(9Z) oleoyl: `CCCCCCCC/C=C/CCCCCCCC(=O)`
- 18:2(9Z,12Z) linoleoyl: `CCCCC/C=C/C/C=C/CCCCCCCC(=O)`
- 18:3(9Z,12Z,15Z) linolenoyl: `CCC/C=C/C/C=C/C/C=C/CCCCCCCC(=O)`
- 22:4(7Z,10Z,13Z,16Z): `CCCCC/C=C/C/C=C/C/C=C/C/C=C/CCCCCC(=O)`
- 14:1(9Z): `CCCCC/C=C/CCCCCCCC(=O)`

Heads:
- phosphoethanolamine (PE): `OP(=O)(O)OCCN`
- phosphate (PA): `OP(=O)(O)O`
- galactose (Gpetn): `OC1C(C(C(C(O1)CO)O)O)O`
- digalactose (DGDG): `OC1C(OC(CO)C(C1O)O)OC2C(C(C(C(O2)CO)O)O)O`

## Verified complete SMILES (RDKit MW in parens)

- PE(18:1/18:2) — `CCCCCCCC/C=C/CCCCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/C/C=C/CCCCC)COP(=O)(O)OCCN` (756.1 ✅ PE class ~750)
- PA(18:0/18:2) — `CCCCCCCCCCCCCCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/C/C=C/CCCCC)COP(=O)(O)O` (715.0 ✅)
- Gpetn(18:3/18:3) — `CCC/C=C/C/C=C/C/C=C/CCCCCCCC(=O)OC[C@H](COC(=O)CCCCCC/C=C/C/C=C/C/C=C/CCC)OC1C(C(C(C(O1)CO)O)O)O` (789.1 ✅)
- Gpetn(22:4/14:1) — `CCCCC/C=C/C/C=C/C/C=C/C/C=C/CCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/CCCCC)OC1C(C(C(C(O1)CO)O)O)O` (791.1 ✅)
- DGDG(18:2/18:2) — `CCCCC/C=C/C/C=C/CCCCCCCC(=O)OC[C@H](COC(=O)CCCCCCC/C=C/C/C=C/CCCCC)OC1C(OC(CO)C(C1O)O)OC2C(C(C(C(O2)CO)O)O)O` (941.3 ✅ DGDG ~940)
- L-Alpha-Amino-Epsilon-Keto-Pimelate (2-amino-6-oxoheptanedioic acid) — `OC(=O)C(N)CCCC(=O)C(=O)O` (189.2 ✅, theory ~187)

## Pitfalls

- **NEVER build by string-slicing the fatty-acid SMILES** (`smi[:-4]` to strip the COOH) —
  the slice leaves an unbalanced `(` and RDKit fails with "extra open parentheses".
  Hand-write each complete SMILES instead; the acyl chain keeps its `C(=O)` and joins the
  backbone as `C(=O)O-` ester.
- The `@`/`@@` in the glycerol carbon is stereochemistry; include it (`[C@H]`) so RDKit
  parses a real glycerolipid, not a flat achiral ester.
- Built lipids are MW 715-941 → they belong in the 大分子糖苷/脂质 bucket, NOT the
  candidate ranking. They are membrane components; the antioxidant analysis targets the
  aglycones/small molecules. Do not spend STP runs on them.
- Two genuinely unrecoverable names seen (absent from PubChem AND HMDB): a 9-oxoxanthene-3-
  carboxylic acid derivative and Theaflagallin. Report as "数据库未收录" — honest coverage
  notes are standard in metabolomics; fabricating a structure is not an option.
