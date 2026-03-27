"""CSV-driven plotting utilities for PROTCTR flight profiles."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional


def _load_profile(csv_path: Path) -> Dict[str, List[float]]:
    with csv_path.open("r", newline="", encoding="utf-8") as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV has no rows: {csv_path}")

    data: Dict[str, List[float]] = {}
    for key in rows[0].keys():
        try:
            data[key] = [float(row[key]) for row in rows]
        except (TypeError, ValueError, KeyError):
            continue
    return data


def plot_profile_from_csv(
    csv_path: Path,
    png_path: Optional[Path] = None,
    show: bool = False,
) -> Optional[Path]:
    """Plot altitude, Mach, and heating trends from simulator CSV output."""

    if not show:
        import matplotlib

        matplotlib.use("Agg", force=True)

    import matplotlib.pyplot as plt

    csv_path = Path(csv_path)
    data = _load_profile(csv_path)

    required = ("t_s", "altitude_m", "mach", "heat_flux_mw_m2")
    missing = [column for column in required if column not in data]
    if missing:
        raise ValueError(f"Missing required CSV columns for plotting: {missing}")

    time_s = data["t_s"]
    altitude_km = [value / 1000.0 for value in data["altitude_m"]]
    mach = data["mach"]
    heat_flux = data["heat_flux_mw_m2"]

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    fig.suptitle("PROTCTR Slipstream and Thermal Envelope", fontsize=14, fontweight="bold")

    axes[0].plot(time_s, altitude_km, color="#1f77b4", linewidth=2.0)
    axes[0].set_ylabel("Altitude (km)")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(time_s, mach, color="#2ca02c", linewidth=2.0)
    axes[1].set_ylabel("Mach")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(time_s, heat_flux, color="#d62728", linewidth=2.0, label="Heat Flux")
    if "tps_margin_mw_m2" in data:
        tps_limit = [heat + margin for heat, margin in zip(heat_flux, data["tps_margin_mw_m2"])]
        axes[2].plot(
            time_s,
            tps_limit,
            color="#7f7f7f",
            linestyle="--",
            linewidth=1.5,
            label="TPS Limit",
        )
    axes[2].set_ylabel("Heat Flux (MW/m^2)")
    axes[2].set_xlabel("Time (s)")
    axes[2].grid(True, alpha=0.3)
    axes[2].legend(loc="best")

    fig.tight_layout(rect=[0, 0.02, 1, 0.95])

    saved_to: Optional[Path] = None
    if png_path is not None:
        png_path = Path(png_path)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_path, dpi=160)
        saved_to = png_path

    if show:
        plt.show()

    plt.close(fig)
    return saved_to
