# Data

Place one legally obtained plain-text (`.txt`) copy of the first book in
`data/input/`. The analysis command automatically selects the first file by
filename. Source text and generated output are ignored by Git.

`data/output/analysis.json` is produced only after successful, validated
interpretation. Deterministic candidates are written to
`data/output/candidates.json` first, so retrieval can be inspected without an
LLM.

Never commit the source book text or generated excerpts.

