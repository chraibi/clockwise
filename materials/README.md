# Materials

Source material for the study, kept for reference. These are **not our work** — they belong to the
original authors and are collected here so the study is self-contained.

## Paper

`paper-echeverria-huarte-2026-ccw.pdf`

> Echeverría-Huarte I., Feliciani C., Shi Z., Nishinari K., Sánchez A., Garcimartín A., Zuriguel I.
> **Individual locomotor bias drives counterclockwise motion in pedestrian crowds.**
> *Nature Communications* 17:4869 (2026). https://doi.org/10.1038/s41467-026-73713-w
> Open access (CC BY).

Popular summary (LinkedIn): "The mystery of the counterclockwise walk" by Celia Lozano Grijalba.

## Data and code (from the paper's supplementary release)

| File | Size | In git? | Contents |
|------|------|---------|----------|
| `Codes.zip` | 21 KB | yes | The authors' figure/analysis Python scripts (`figure_*.py`, `statistical_analysis.py`). |
| `ExperimentalData.zip` | 62 MB | **no** (gitignored) | Per-trial pedestrian trajectory CSVs, Spain and Japan, by arena/condition. |
| `SourceData.xlsx` | 32 MB | **no** (gitignored) | Source data behind the paper's figures. |

The two large files are excluded from version control to keep the repository light. They live in this
folder locally; re-obtain them from the paper's *Data availability* section (or the original
`Downloads/Clockwise` bundle) if missing.

## How we use these

- The **paper** defines the phenomenon and the polarization metric `M` we reproduce.
- The **trajectory data** is a reference for the experimental `M̄ ≈ 0.2` and could be used later to
  compute `M` from the real data for comparison (out of scope for the first mechanism test).
- The **authors' code** documents exactly how they computed their figures and `M`.
