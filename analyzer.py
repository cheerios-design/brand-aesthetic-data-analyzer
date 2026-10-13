"""Brand Aesthetic Data Analyzer.

Loads raw brand design-system data, cleans it, computes WCAG contrast
ratios between primary and background colors, and saves two charts.
"""

import re
from pathlib import Path
from typing import Optional, Tuple

import matplotlib

matplotlib.use("Agg")  # Render to files without needing a display.
import matplotlib.pyplot as plt
import pandas as pd

DATA_FILE = Path("brands_data.csv")
OUTPUT_DIR = Path("output")
WCAG_THRESHOLD = 4.5
HEX_PATTERN = re.compile(r"^#[0-9A-F]{6}$")


def load_data(path: Path) -> pd.DataFrame:
    """Load the brand CSV file into a DataFrame.

    Args:
        path: Location of the CSV file.

    Returns:
        A DataFrame containing the raw, unmodified rows.
    """
    return pd.read_csv(path, dtype=str, keep_default_na=True)


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading and trailing whitespace from every text column.

    Args:
        df: DataFrame with string columns.

    Returns:
        A copy of the DataFrame with trimmed strings; empty strings
        become missing values.
    """
    cleaned = df.copy()
    for column in cleaned.columns:
        cleaned[column] = cleaned[column].str.strip().replace("", pd.NA)
    return cleaned


def normalize_hex(value: Optional[str]) -> Optional[str]:
    """Normalize a single hex color string to the form #RRGGBB.

    Adds a missing leading '#', expands 3-digit shorthand, and uppercases.
    Values that are not valid hex colors are returned as None.

    Args:
        value: Raw hex string, possibly messy or missing.

    Returns:
        A normalized 7-character hex string, or None if invalid.
    """
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().upper().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    candidate = "#" + text
    return candidate if HEX_PATTERN.match(candidate) else None


def normalize_hex_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply hex normalization to PrimaryHex and BackgroundHex.

    Args:
        df: DataFrame with PrimaryHex and BackgroundHex columns.

    Returns:
        A copy of the DataFrame with normalized hex columns.
    """
    result = df.copy()
    for column in ("PrimaryHex", "BackgroundHex"):
        result[column] = result[column].apply(normalize_hex)
    return result


def drop_incomplete_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows lacking a brand name or a usable color value.

    Args:
        df: DataFrame after hex normalization.

    Returns:
        A DataFrame containing only complete rows with a fresh index.
    """
    required = ["BrandName", "PrimaryHex", "BackgroundHex"]
    return df.dropna(subset=required).reset_index(drop=True)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning pipeline on raw brand data.

    Args:
        df: Raw DataFrame from load_data.

    Returns:
        A cleaned DataFrame ready for analysis.
    """
    df = strip_whitespace(df)
    df = normalize_hex_columns(df)
    return drop_incomplete_rows(df)


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert a normalized #RRGGBB string to an RGB tuple.

    Args:
        hex_code: Hex color such as '#1DB954'.

    Returns:
        Red, green and blue channel values from 0 to 255.
    """
    digits = hex_code.lstrip("#")
    return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Compute WCAG relative luminance for an sRGB color.

    Args:
        rgb: Channel values from 0 to 255.

    Returns:
        Luminance between 0.0 (black) and 1.0 (white).
    """
    def linearize(channel: int) -> float:
        """Convert one sRGB channel to its linear-light value."""
        srgb = channel / 255
        if srgb <= 0.03928:
            return srgb / 12.92
        return ((srgb + 0.055) / 1.055) ** 2.4

    red, green, blue = (linearize(c) for c in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Calculate the WCAG contrast ratio between two hex colors.

    Args:
        hex_a: First color as #RRGGBB.
        hex_b: Second color as #RRGGBB.

    Returns:
        Contrast ratio from 1.0 to 21.0, rounded to two decimals.
    """
    lum_a = relative_luminance(hex_to_rgb(hex_a))
    lum_b = relative_luminance(hex_to_rgb(hex_b))
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def add_contrast_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add ContrastRatio and PassesAA columns to the DataFrame.

    Args:
        df: Cleaned DataFrame with normalized hex columns.

    Returns:
        A copy with the contrast ratio and a boolean AA pass flag.
    """
    result = df.copy()
    result["ContrastRatio"] = [
        contrast_ratio(p, b)
        for p, b in zip(result["PrimaryHex"], result["BackgroundHex"])
    ]
    result["PassesAA"] = result["ContrastRatio"] >= WCAG_THRESHOLD
    return result


def plot_typography_frequency(df: pd.DataFrame, out_path: Path) -> None:
    """Save a bar chart of typography class frequencies.

    Args:
        df: Analyzed DataFrame with a TypographyClass column.
        out_path: Destination PNG path.
    """
    counts = df["TypographyClass"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(counts.index, counts.values, color="#4C78A8")
    ax.set_title("Typography Class Frequency")
    ax.set_xlabel("Typography Class")
    ax.set_ylabel("Number of Brands")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_contrast_scores(df: pd.DataFrame, out_path: Path) -> None:
    """Save a scatter plot of contrast ratios with pass/fail highlighting.

    Args:
        df: Analyzed DataFrame with ContrastRatio and PassesAA columns.
        out_path: Destination PNG path.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    for passed, color, label in ((True, "#2E8B57", "Pass (>= 4.5:1)"),
                                 (False, "#C0392B", "Fail (< 4.5:1)")):
        subset = df[df["PassesAA"] == passed]
        ax.scatter(subset["BrandName"], subset["ContrastRatio"],
                   color=color, label=label, s=60)
    ax.axhline(WCAG_THRESHOLD, color="gray", linestyle="--", linewidth=1)
    ax.set_title("WCAG Contrast Ratio by Brand")
    ax.set_xlabel("Brand")
    ax.set_ylabel("Contrast Ratio")
    ax.legend()
    plt.setp(ax.get_xticklabels(), rotation=60, ha="right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def answer_typography_question(df: pd.DataFrame) -> str:
    """Answer: which typography class is most common, and how does each
    class perform on contrast?

    Uses aggregation (count and mean) grouped by typography class.

    Args:
        df: Analyzed DataFrame with TypographyClass and ContrastRatio.

    Returns:
        A text answer justified by the aggregated numbers.
    """
    summary = df.groupby("TypographyClass")["ContrastRatio"].agg(
        Brands="count", AvgContrast="mean").sort_values("Brands", ascending=False)
    top = summary.index[0]
    lines = [f"Q1. Which typography class is most common and how does "
             f"contrast compare by class?",
             f"A1. {top} is most common ({int(summary.iloc[0]['Brands'])} of "
             f"{len(df)} brands). Average contrast by class:"]
    for name, row in summary.iterrows():
        lines.append(f"    {name}: {int(row['Brands'])} brands, "
                     f"avg {row['AvgContrast']:.2f}:1")
    return "\n".join(lines)


def answer_accessibility_question(df: pd.DataFrame) -> str:
    """Answer: how many brands meet WCAG AA, and which ones fail?

    Uses filtering on the pass flag and sorting by contrast ratio.

    Args:
        df: Analyzed DataFrame with ContrastRatio and PassesAA.

    Returns:
        A text answer listing the failing brands from worst to best.
    """
    failing = df[~df["PassesAA"]].sort_values("ContrastRatio")
    lines = ["Q2. How many brands meet the 4.5:1 WCAG AA minimum, and which "
             "fail?",
             f"A2. {int(df['PassesAA'].sum())} of {len(df)} pass; "
             f"{len(failing)} fail (worst first):"]
    for _, row in failing.iterrows():
        lines.append(f"    {row['BrandName']}: {row['ContrastRatio']}:1")
    return "\n".join(lines)


def answer_extreme_question(df: pd.DataFrame) -> str:
    """Answer: which brands have the highest and lowest contrast?

    Uses sorting to find the extremes of the contrast distribution.

    Args:
        df: Analyzed DataFrame with BrandName and ContrastRatio.

    Returns:
        A text answer naming the top and bottom brands.
    """
    ranked = df.sort_values("ContrastRatio", ascending=False)
    best, worst = ranked.iloc[0], ranked.iloc[-1]
    return ("Q3. Which brands have the highest and lowest contrast?\n"
            f"A3. Highest: {best['BrandName']} ({best['ContrastRatio']}:1). "
            f"Lowest: {worst['BrandName']} ({worst['ContrastRatio']}:1).")


def main() -> None:
    """Run the full pipeline: load, clean, analyze, and visualize."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    raw = load_data(DATA_FILE)
    cleaned = clean_data(raw)
    analyzed = add_contrast_column(cleaned)
    analyzed.to_csv(OUTPUT_DIR / "brands_analyzed.csv", index=False)
    answers = "\n\n".join([answer_typography_question(analyzed),
                           answer_accessibility_question(analyzed),
                           answer_extreme_question(analyzed)])
    print(answers)
    (OUTPUT_DIR / "analysis_results.txt").write_text(answers, encoding="utf-8")
    plot_typography_frequency(analyzed, OUTPUT_DIR / "typography_frequency.png")
    plot_contrast_scores(analyzed, OUTPUT_DIR / "contrast_scores.png")
    print(f"Loaded {len(raw)} rows; kept {len(analyzed)} after cleaning.")
    print(f"Passing WCAG AA: {int(analyzed['PassesAA'].sum())}")
    print(f"Charts saved to {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
