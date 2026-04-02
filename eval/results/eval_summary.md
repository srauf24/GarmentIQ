# Evaluation Summary

**Test set**: 50 images
**Predictions available**: 50
**Overall accuracy**: 62.0%

## Per-Attribute Accuracy

| Attribute | Correct | Total | Accuracy |
|-----------|---------|-------|----------|
| garment_type | 35 | 50 | 70.0% |
| style | 18 | 50 | 36.0% |
| material | 25 | 50 | 50.0% |
| occasion | 27 | 50 | 54.0% |
| location_country | 50 | 50 | 100.0% |

## Top Confusion Pairs

### garment_type

- **Top** misclassified as **Blouse** (2x)
- **Skirt** misclassified as **Top** (2x)
- **Trousers** misclassified as **Knitwear** (2x)

### style

- **Casual** misclassified as **Classic** (9x)
- **Casual** misclassified as **Minimalist** (5x)
- **Formal** misclassified as **Classic** (4x)

### material

- **Cotton** misclassified as **Knit** (3x)
- **Synthetic** misclassified as **Knit** (3x)
- **Knit** misclassified as **Wool** (3x)

### occasion

- **Casual Daily** misclassified as **Smart Casual** (10x)
- **Casual Daily** misclassified as **Business** (5x)
- **Casual Daily** misclassified as **Evening/Formal** (3x)

## Analysis

### Where the model excels

The model performs best on **garment type classification** (70%), correctly identifying primary garment categories like Dress, Jacket, Suit, and Coat in most cases. It also achieves **perfect accuracy on location inference** (100%) — correctly returning empty/null for studio Pexels images where no geographic cues are visible, demonstrating strong restraint against hallucinating location data. The model reliably distinguishes between major garment silhouettes (e.g., dresses vs. jackets vs. suits) and handles leather material identification well.

### Failure modes

**Style classification is the weakest attribute** (36%), largely due to semantic overlap between labels. The model frequently predicts "Classic" or "Minimalist" where human labelers chose "Casual" or "Formal" — these are genuinely ambiguous categories where reasonable annotators might disagree. **Occasion mapping** (54%) shows a similar pattern: the model tends to elevate "Casual Daily" items to "Smart Casual" (10 cases), suggesting it interprets styled photography as implying a more elevated occasion than the garment itself warrants. **Material identification** (50%) struggles with distinguishing knit from wool and cotton from synthetic — understandable since these require tactile information not available in photos.

### Improvements with more time

- **Constrain style/occasion vocabularies** — Reduce label overlap by merging "Casual" and "Classic" into fewer, more distinct categories, or provide clearer definitions in the prompt to reduce ambiguity.
- **Add fuzzy matching for evaluation** — Treat "Casual"/"Classic" and "Casual Daily"/"Smart Casual" as partial matches, since many disagreements reflect genuine label ambiguity rather than model errors. This would give a more accurate picture of real-world performance.
- **Expand material prompt with visual cues** — Provide the model with explicit guidance on distinguishing knit textures from woven fabrics, and synthetic sheen from natural fiber characteristics, to improve the 50% material accuracy.

