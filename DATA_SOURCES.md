# Data sources and reuse

The FEATS data packages are collections of normalized or filtered sentence
pairs. Each subset retains its upstream terms; the repository's code does not
replace those terms.

## MultiSim

- Source: https://github.com/XenonMolecule/MultiSim
- Dataset card: https://github.com/XenonMolecule/MultiSim/blob/main/DataCard.md
- Declared license: MIT
- Citation: Michael J. Ryan, Tarek Naous, and Wei Xu (2023), *Revisiting
  non-English Text Simplification: A Unified Multilingual Benchmark*.

MultiSim asks users to cite both the benchmark and the individual corpora used.
The dataset card contains the corresponding citations.

## Align-and-Shine Wikipedia–Vikidia corpus

- Source: https://github.com/kenjihilasak/Align-and-Shine
- Released aligned-corpus license: CC BY-SA 4.0
- Wikipedia reuse terms:
  https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use
- Vikidia reuse terms: https://en.vikidia.org/wiki/Vikidia:Copyright

This subset contains aligned and processed text derived from Wikipedia and
Vikidia, rather than raw source dumps. Reuse must preserve attribution to the
upstream projects and comply with the applicable share-alike requirements.

## SimplifyUR

- Source: https://github.com/harisbinzia/SimplifyUR
- Pinned source revision: `cdb3203d39abfcc365232c8aae1b35afa5d43bd8`
- Citation: Namoos Hayat Qasmi, Haris Bin Zia, Awais Athar, and Agha Ali Raza
  (2020), *SimplifyUR: Unsupervised Lexical Text Simplification for Urdu*.

The upstream README declares the dataset as CC BY 4.0. The repository also
contains an older `Data/LICENSE` text identifying Attribution,
NonCommercial, and ShareAlike terms. Until the upstream discrepancy is
clarified, users should follow the more restrictive notice as well as the
README attribution requirement.

## FEATS processing

FEATS changes representation and applies automatic quality filters; it does
not claim ownership of the upstream sentences. Cite the source datasets and
the FEATS/Align-and-Shine papers as applicable. Model scores and automatic
filter decisions do not constitute additional human quality annotation.
