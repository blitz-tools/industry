"""Server-rendered SVG charts for the Observability page (M15).

Zero client dependencies by design — the investigation outcome: the
alternatives (matplotlib, pygal, Altair/Vega, Plotly, Bokeh) all bring
raster output or a vendored JS runtime for what is, here, a handful of
small time-series figures; a ~150-line SVG generator styled entirely
with the app's design tokens keeps the page DB-pure, server-rendered,
and exactly on the design system. The one interactive piece — the line
chart's crosshair + tooltip — is vanilla JS (static/observability.js),
the same approach as every other script in the app.

Conventions (the dataviz method): 2px round-join lines, hairline solid
gridlines, 8px end markers with a 2px surface ring, text in text tokens
(never series colors), a legend for >= 2 series, selective end labels,
and every chart ships a table-view twin in the page.

Hues: the brand's cyan/yellow stepped down into the dark-mode lightness
band — the raw tokens (#66d9ef/#e6db74) sit above the band and glow as
marks. The pair passes the six-checks validator on the app surface
(#232526): lightness band, chroma floor, CVD separation, normal-vision
floor, and 3:1 contrast all PASS. Slots assign in fixed kind order and
never cycle — color follows the entity, not its rank.
"""

import math
from collections.abc import Callable
from datetime import datetime

# Fixed slot order (validated pair on var(--panel) #232526).
SERIES_HUES = ("#1f99b0", "#a8942a")
# The --muted token: sparklines are trend, not identity (de-emphasis).
DE_EMPHASIS = "#7e8e91"
# The --cyan token: sparkline end dots (a small saturated accent).
ACCENT = "#66d9ef"

# Shared plot geometry: line_chart and chart_data must agree exactly —
# the tooltip layer maps pointer position onto the pixels drawn here.
_LEFT, _RIGHT, _TOP, _BOTTOM = 40, 56, 10, 26


def sparkline(points: list[tuple[datetime, float]], *, unit: str = "") -> str:
    """A stat-tile trend sparkline: auto-scaled (the meter beside it
    carries the absolute position), 2px de-emphasis line, accent end dot
    with its 2px surface ring. Single series — no legend; the cell's
    label names it. Empty input renders nothing."""
    if not points:
        return ""
    width, height, pad = 200, 36, 4
    xs = [stamp.timestamp() for stamp, _ in points]
    ys = [value for _, value in points]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    if x_max == x_min:
        x_max = x_min + 1
    if y_max == y_min:
        y_min, y_max = y_min - 1, y_max + 1  # flat series: center the line

    def x_at(x: float) -> float:
        return pad + (x - x_min) / (x_max - x_min) * (width - 2 * pad)

    def y_at(y: float) -> float:
        return height - pad - (y - y_min) / (y_max - y_min) * (height - 2 * pad)

    coords = " ".join(
        f"{x_at(x):.1f},{y_at(y):.1f}" for x, y in zip(xs, ys, strict=True)
    )
    end_x, end_y = x_at(xs[-1]), y_at(ys[-1])
    suffix = f" {unit}" if unit else ""
    label = f"trend: latest {ys[-1]:g}{suffix}, range {y_min:g} to {y_max:g}{suffix}"
    return (
        f'<svg class="sparkline" viewBox="0 0 {width} {height}" role="img"'
        f' aria-label="{label}">'
        f'<polyline points="{coords}" fill="none" stroke="{DE_EMPHASIS}"'
        f' stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="4" fill="{ACCENT}"'
        f' stroke="var(--panel)" stroke-width="2"/></svg>'
    )


def _nice_step(span: float) -> float:
    """A clean 1/2/5x10^k step covering the span in ~4 gridlines."""
    raw = span / 4 if span > 0 else 1.0
    magnitude = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1.0
    for multiple in (1, 2, 5, 10):
        if raw <= multiple * magnitude:
            return multiple * magnitude
    return 10 * magnitude


def _layout(
    series: list[dict], width: int, height: int
) -> tuple[
    Callable[[float], float],
    Callable[[float], float],
    float,
    float,
    float,
    float,
]:
    """The shared x/y scales for a chart and its data twin: (x_at, y_at,
    x_min, x_max, y_max, tick_step) over the union of every series'
    points."""
    plot_w = width - _LEFT - _RIGHT
    plot_h = height - _TOP - _BOTTOM
    stamps = [stamp.timestamp() for entry in series for stamp, _ in entry["points"]]
    values = [value for entry in series for _, value in entry["points"]]
    x_min, x_max = min(stamps), max(stamps)
    if x_max == x_min:
        x_max = x_min + 1
    span = max(values) - min(values)
    step = _nice_step(span if span > 0 else max(values, 1))
    y_max = math.ceil(max(values) / step) * step
    if y_max <= 0:
        y_max = step

    def x_at(x: float) -> float:
        return _LEFT + (x - x_min) / (x_max - x_min) * plot_w

    def y_at(y: float) -> float:
        return _TOP + plot_h - y / y_max * plot_h

    return x_at, y_at, x_min, x_max, y_max, step


def line_chart(
    series: list[dict],
    *,
    y_unit: str = "",
    value_format: str = "{:.2f}",
    width: int = 720,
    height: int = 200,
) -> str:
    """A multi-series time-series line chart as inline SVG.

    `series` items carry name, hue, and points [(datetime, value)].
    Furniture (grid, axis text) wears the app's text/line tokens — CSS
    custom properties resolve inside inline SVG; marks never color text.
    The crosshair + tooltip layer (static/observability.js) reads the
    JSON twin from chart_data(), which shares this layout."""
    if not any(entry["points"] for entry in series):
        return ""
    plot_w = width - _LEFT - _RIGHT
    plot_h = height - _TOP - _BOTTOM
    x_at, y_at, x_min, x_max, y_max, step = _layout(series, width, height)

    # Gridlines: solid hairlines, one shade off the surface, at clean
    # y steps from the baseline up.
    grid = []
    tick = 0.0
    while tick <= y_max + step / 2:
        y = y_at(tick)
        grid.append(
            f'<line x1="{_LEFT}" y1="{y:.1f}" x2="{_LEFT + plot_w}" y2="{y:.1f}"'
            f' stroke="var(--line)" stroke-width="1"/>'
            f'<text x="{_LEFT - 6}" y="{y + 3:.1f}" text-anchor="end"'
            f' class="chart-tick">{tick:g}</text>'
        )
        tick += step

    # X ticks: five evenly spaced time labels; the format follows the
    # span (intraday gets clock times, longer spans get dates).
    span = x_max - x_min
    time_format = "%H:%M" if span < 48 * 3600 else "%b %d"
    x_ticks = [
        f'<text x="{x_at(x_min + span * i / 4):.1f}" y="{height - 8}"'
        f' text-anchor="middle" class="chart-tick">'
        f'{datetime.fromtimestamp(x_min + span * i / 4).strftime(time_format)}</text>'
        for i in range(5)
    ]

    lines = []
    end_labels = []
    placed: list[float] = []  # end-label y positions, for collision nudges
    for entry in series:
        if not entry["points"]:
            continue
        coords = " ".join(
            f"{x_at(stamp.timestamp()):.1f},{y_at(value):.1f}"
            for stamp, value in entry["points"]
        )
        lines.append(
            f'<polyline points="{coords}" fill="none" stroke="{entry["hue"]}"'
            f' stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        last_stamp, last_value = entry["points"][-1]
        end_x, end_y = x_at(last_stamp.timestamp()), y_at(last_value)
        lines.append(
            f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="4"'
            f' fill="{entry["hue"]}" stroke="var(--panel)" stroke-width="2"/>'
        )
        # Selective direct label: the value at the line's end, nudged
        # off any neighbor label (text token, never the series hue).
        label_y = end_y
        while any(abs(label_y - other) < 12 for other in placed):
            label_y -= 12
        placed.append(label_y)
        end_labels.append(
            f'<text x="{end_x + 8:.1f}" y="{label_y + 4:.1f}"'
            f' class="chart-end">{value_format.format(last_value)}{y_unit}</text>'
        )

    names = " and ".join(entry["name"] for entry in series if entry["points"])
    return (
        f'<svg class="line-chart" viewBox="0 0 {width} {height}" role="img"'
        f' aria-label="time series: {names} over time" tabindex="0">'
        + "".join(grid)
        + "".join(x_ticks)
        + "".join(lines)
        + "".join(end_labels)
        + '<line class="chart-crosshair" x1="0" y1="10" x2="0"'
        f' y2="{_TOP + plot_h}" stroke="var(--muted)" stroke-width="1"'
        ' visibility="hidden"/>'
        "</svg>"
    )


def chart_data(
    series: list[dict],
    *,
    y_unit: str = "",
    value_format: str = "{:.2f}",
    width: int = 720,
    height: int = 200,
) -> dict:
    """The JSON twin of a line chart's series — the tooltip layer's feed.
    Points carry the pixel coordinates the SVG drew (the crosshair maps
    pointer position to the nearest sample without recomputing scales)
    plus the formatted value strings (unit included). Width/height must
    match the line_chart call."""
    if not any(entry["points"] for entry in series):
        return {"series": []}
    x_at, y_at, _, _, _, _ = _layout(series, width, height)
    return {
        "series": [
            {
                "name": entry["name"],
                "hue": entry["hue"],
                "points": [
                    {
                        "x": round(x_at(stamp.timestamp()), 1),
                        "y": round(y_at(value), 1),
                        "value": value_format.format(value) + y_unit,
                    }
                    for stamp, value in entry["points"]
                ],
            }
            for entry in series
            if entry["points"]
        ]
    }
