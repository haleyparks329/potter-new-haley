# Data

Place one legally obtained plain-text (`.txt`) copy of the first book in
`data/input/`. The analysis command automatically selects the first file by
filename. Source text and generated output are ignored by Git.

`data/output/friendship_timeline.json` is the stable preprocessing-to-
visualization contract. It is always produced by the deterministic pipeline
and may later be enriched by optional LLM interpretation without changing its
schema. Deterministic candidates are written to
`data/output/candidates.json` first, so retrieval can be inspected without an
LLM.

Never commit the source book text or generated excerpts.
