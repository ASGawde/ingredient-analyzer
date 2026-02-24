"""
schema.py — Single source of truth for all column definitions.

The output CSV has two header rows (matching the original format):
  Row 0: numeric index (0–89) for the first 90 cols, blank for the last 4
  Row 1: actual column names
"""

# ── Column definitions ────────────────────────────────────────────────────────
# Each entry: (column_name, numeric_index_or_None, data_type, default_value)
#   data_type: "str" | "float" | "bool" | "int"
#   numeric_index: the value shown in row 0 of the original file (None = blank)

COLUMNS = [
    # ── Identity ──────────────────────────────────────────────────────────────
    ("Ingredient name",                   0,    "str",   None),
    ("INCI Name",                         1,    "str",   None),
    ("Aliases",                           2,    "str",   None),

    # ── Safety & Usage ────────────────────────────────────────────────────────
    ("Allergen potential",                3,    "str",   None),
    ("Risk of irritation",               4,    "str",   None),
    ("Role in formulation",              5,    "str",   None),
    ("Note",                             6,    "str",   None),
    ("Source",                           7,    "str",   None),
    ("Comedogenic Rating",               8,    "float", None),
    ("Concentration rinse-off",          9,    "str",   None),
    ("Concentration Leave-on",           10,   "str",   None),
    ("Concentration Sensitive/eye area", 11,   "str",   None),
    ("Side effects",                     12,   "str",   None),
    ("Incompatible with",                13,   "str",   None),
    ("Works well with",                  14,   "str",   None),

    # ── Skin Type Suitability ─────────────────────────────────────────────────
    ("Normal",                           15,   "bool",  None),
    ("Dry",                              16,   "bool",  None),
    ("Oily",                             17,   "bool",  None),
    ("Combination",                      18,   "bool",  None),

    # Sensitivity scale (Not sensitive → Extremely sensitive)
    ("Not sensitive",                    19,   "bool",  None),
    ("A little sensitive",               20,   "bool",  None),
    ("Moderately sensitive",             21,   "bool",  None),
    ("Sensitive",                        22,   "bool",  None),
    ("Very sensitive",                   23,   "bool",  None),
    ("Extremely sensitive",              24,   "bool",  None),

    # Acne-prone scale
    ("Not acne prone",                   25,   "bool",  None),
    ("A little acne-prone",              26,   "bool",  None),
    ("Moderately acne-prone",            27,   "bool",  None),
    ("Acne-prone",                       28,   "bool",  None),
    ("Very acne-prone",                  29,   "bool",  None),
    ("Extremely acne-prone",             30,   "bool",  None),

    # ── Age Groups ────────────────────────────────────────────────────────────
    ("Teen",                             31,   "bool",  None),
    ("20s",                              32,   "bool",  None),
    ("30s",                              33,   "bool",  None),
    ("40s",                              34,   "bool",  None),
    ("50s",                              35,   "bool",  None),
    ("60+",                              36,   "bool",  None),

    # ── Dietary / Lifestyle Flags ─────────────────────────────────────────────
    ("Vegetarian",                       37,   "bool",  None),
    ("Vegan",                            38,   "bool",  None),
    ("Gluten-free",                      39,   "bool",  None),
    ("Paleo",                            40,   "bool",  None),
    ("Unscented",                        41,   "bool",  None),
    ("Paraben-free",                     42,   "bool",  None),
    ("Sulphate-free",                    43,   "bool",  None),
    ("Silicon-free",                     44,   "bool",  None),
    ("Nut-free",                         45,   "bool",  None),
    ("Soy-free",                         46,   "bool",  None),
    ("Latex-free",                       47,   "bool",  None),
    ("Sesame-free",                      48,   "bool",  None),
    ("Citrus-free",                      49,   "bool",  None),
    ("Dye-free",                         50,   "bool",  None),
    ("Fragrance-free",                   51,   "bool",  None),
    ("Scent-free",                       52,   "bool",  None),
    ("Seafood-free",                     53,   "bool",  None),
    ("Dairy-free",                       54,   "bool",  None),

    # ── Skin Concerns (concern flag + description pairs) ──────────────────────
    ("Rosacea",                          55,   "bool",  None),
    ("Description",                      56,   "str",   None),   # Rosacea description

    ("Hyperpigmentation & Uneven skin tone", 57, "bool", None),
    ("Description",                      58,   "str",   None),

    ("Acne",                             59,   "bool",  None),
    ("Description",                      60,   "str",   None),

    ("Dryness/Dehydration",              61,   "bool",  None),
    ("Description",                      62,   "str",   None),

    ("Oiliness & Shine",                 63,   "bool",  None),
    ("Description",                      64,   "str",   None),

    ("Fine lines & Wrinkles",            65,   "bool",  None),
    ("Description",                      66,   "str",   None),

    ("Loss of Elasticity/firmness",      67,   "bool",  None),
    ("Description",                      68,   "str",   None),

    ("Visible pores & Uneven texture",   69,   "bool",  None),
    ("Description",                      70,   "str",   None),

    ("Clogged pores, blackheads",        71,   "bool",  None),
    ("Description",                      72,   "str",   None),

    ("Dullness",                         73,   "bool",  None),
    ("Description",                      74,   "str",   None),

    ("Dark circles",                     75,   "bool",  None),
    ("Description",                      76,   "str",   None),

    ("Blemishes",                        77,   "bool",  None),
    ("Description",                      78,   "str",   None),

    # ── Benefit Tags ──────────────────────────────────────────────────────────
    ("Moisturizing",                     79,   "bool",  None),
    ("Nourishing",                       80,   "bool",  None),
    ("Exfoliating",                      81,   "bool",  None),
    ("Soothing",                         82,   "bool",  None),
    ("Healing",                          83,   "bool",  None),
    ("Smoothing",                        84,   "bool",  None),
    ("Brightening",                      85,   "bool",  None),
    ("Minimizes pores",                  86,   "bool",  None),
    ("Firming",                          87,   "bool",  None),

    # ── Concentration QA ──────────────────────────────────────────────────────
    ("Known concentration Rinse-off",    88,   "str",   None),
    ("Known concentration Leave-on",     89,   "str",   None),

    # ── QA / Audit (no numeric index in row 0) ────────────────────────────────
    ("Description",                      None, "str",   None),   # concentration description
    ("Predicted or manual",              None, "str",   None),
    ("Correction made",                  None, "str",   None),
    ("Description",                      None, "str",   None),   # correction description
]

# Derived helpers used by output/csv_writer.py
COLUMN_NAMES   = [c[0] for c in COLUMNS]          # 94 names (with duplicates)
NUMERIC_INDEX  = [c[1] for c in COLUMNS]          # row-0 values (int or None)
COLUMN_TYPES   = {i: c[2] for i, c in enumerate(COLUMNS)}
COLUMN_DEFAULTS= {i: c[3] for i, c in enumerate(COLUMNS)}

# Positional groups (by column index) for enricher routing
GROUPS = {
    "identity":   list(range(0, 3)),
    "safety":     list(range(3, 15)),
    "skin_type":  list(range(15, 31)),
    "age":        list(range(31, 37)),
    "dietary":    list(range(37, 55)),
    "concerns":   list(range(55, 79)),
    "benefits":   list(range(79, 88)),
    "conc_qa":    list(range(88, 94)),
}
