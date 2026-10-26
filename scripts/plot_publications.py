"""Grouped bar chart of annual publication counts, 2015-2025.

Reads data/annual_counts_2015_2025.csv and writes one PDF:
figures/publication_growth_2015_2025.pdf

Counts are database-specific records. They are not summed across databases.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, TextArea, VPacker
from matplotlib.ticker import FuncFormatter, MultipleLocator
from matplotlib.transforms import blended_transform_factory

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "annual_counts_2015_2025.csv"
OUTPUT_PDF = ROOT / "figures" / "publication_growth_2015_2025.pdf"

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "pdf.fonttype": 42,
        "font.size": 9,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.linewidth": 0.6,
        "axes.axisbelow": True,
        "legend.frameon": False,
    }
)

WIDTH_MM = 170.0
HEIGHT_MM = 62.0

# Within each year the bars run IEEE Xplore, PubMed, then Web of Science.
SERIES = (
    ("IEEE Xplore", "IEEE Xplore", "#1F7A6B"),
    ("PubMed", "PubMed", "#1F4E79"),
    ("Web of Science", "Web of Science", "#C47A2C"),
)


def load_counts(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    expected = ["year", "PubMed", "IEEE Xplore", "Web of Science"]
    missing = [column for column in expected if column not in frame.columns]
    if missing:
        raise ValueError(f"Source table is missing columns: {missing}")
    frame = frame.loc[:, expected].copy()
    frame["year"] = frame["year"].astype(int)
    for column in expected[1:]:
        frame[column] = frame[column].astype(int)
    return frame.sort_values("year")


def add_release_callout(figure: plt.Figure, axis: plt.Axes, release_x: float) -> None:
    """Rounded note and dotted line between the 2022 and 2023 groups."""
    label_color = "#7A4E2C"
    line_color = "#C48A4A"
    title = TextArea(
        "ChatGPT released",
        textprops={
            "color": label_color,
            "fontsize": 8,
            "fontweight": "bold",
            "ha": "center",
        },
    )
    subtitle = TextArea(
        "November 2022",
        textprops={
            "color": label_color,
            "fontsize": 7,
            "ha": "center",
        },
    )
    packed = VPacker(children=[title, subtitle], align="center", pad=0, sep=1)
    callout = AnnotationBbox(
        packed,
        (release_x, 0.86),
        xycoords=blended_transform_factory(axis.transData, axis.transAxes),
        frameon=True,
        box_alignment=(0.5, 1.0),
        pad=0.15,
        zorder=6,
        bboxprops={
            "boxstyle": "round,pad=0.25,rounding_size=0.25",
            "facecolor": "#FBF4EA",
            "edgecolor": "#E2B07A",
            "linewidth": 0.8,
        },
    )
    axis.add_artist(callout)
    figure.canvas.draw()
    extent = callout.patch.get_window_extent(figure.canvas.get_renderer())
    _, line_below = axis.transData.inverted().transform((extent.x0, extent.y0 - 8))
    _, line_above = axis.transData.inverted().transform((extent.x0, extent.y1 + 8))
    _, frame_top = axis.transData.inverted().transform((extent.x0, axis.bbox.y1 - 3))
    line_style = dict(
        color=line_color,
        linestyle=(0, (0.8, 1.6)),
        linewidth=1.35,
        solid_capstyle="round",
        zorder=4,
    )
    axis.plot([release_x, release_x], [0, line_below], **line_style)
    axis.plot([release_x, release_x], [line_above, frame_top], **line_style)


def draw(frame: pd.DataFrame) -> plt.Figure:
    years = frame["year"].to_numpy()
    positions = np.arange(len(years), dtype=float)
    positions[years >= 2023] += 0.7
    bar_width = 0.24
    offsets = np.array([-bar_width, 0.0, bar_width])

    figure, axis = plt.subplots(
        figsize=(WIDTH_MM / 25.4, HEIGHT_MM / 25.4),
        constrained_layout=True,
    )
    for spine in axis.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)
        spine.set_color("#2C2C2C")
    for offset, (label, column, color) in zip(offsets, SERIES):
        axis.bar(
            positions + offset,
            frame[column].to_numpy(),
            width=bar_width * 0.92,
            color=color,
            label=label,
            linewidth=0,
            zorder=3,
        )

    x_right = float(positions[-1]) + 0.55
    axis.set_xlim(-0.55, x_right)
    axis.set_ylim(0, 1600)
    axis.yaxis.set_major_locator(MultipleLocator(200))
    axis.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{int(value):,}"))
    axis.set_xticks(positions)
    axis.set_xticklabels([str(year) for year in years])
    axis.set_xlabel("Publication year")
    axis.set_ylabel("Number of publications")
    axis.tick_params(axis="both", length=3, width=0.6, pad=2)
    release_x = (float(positions[years == 2022][0]) + float(positions[years == 2023][0])) / 2
    axis.axvspan(release_x, x_right, facecolor="#F0F0F0", linewidth=0, zorder=0)
    add_release_callout(figure, axis, release_x)
    axis.legend(
        loc="upper left",
        bbox_to_anchor=(0.0, 1.0),
        ncol=1,
        handlelength=1.1,
        handleheight=0.7,
        borderaxespad=0.2,
        labelspacing=0.35,
    )
    return figure


def main() -> None:
    frame = load_counts(DATA_PATH)
    figure = draw(frame)
    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_PDF)
    plt.close(figure)


if __name__ == "__main__":
    main()
