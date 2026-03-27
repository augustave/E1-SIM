#!/usr/bin/env python3
"""CLI entrypoint for the PROTCTR simulator."""

from __future__ import annotations

import argparse
from pathlib import Path

from protctr_sim.plotting import plot_profile_from_csv
from protctr_sim.simulator import SimulationConfig, simulate, write_csv
from protctr_sim.vehicle import default_vehicle

DEFAULT_CSV_PATH = Path("outputs/protctr_profile.csv")
DEFAULT_PLOT_PATH = Path("outputs/protctr_profile.png")


def _format_summary(points, heat_limit_mw_m2: float) -> str:
    max_mach = max(p.mach for p in points)
    peak_heat = max(p.heat_flux_mw_m2 for p in points)
    min_tps_margin = min(p.tps_margin_mw_m2 for p in points)
    peak_q = max(p.q_dyn_kpa for p in points)
    min_static = min(p.static_margin_proxy for p in points)
    max_ld = max(p.ld_ratio for p in points)
    final = points[-1]

    overheat_pct = 100.0 * sum(p.heat_flux_mw_m2 > heat_limit_mw_m2 for p in points) / len(points)

    lines = [
        "PROTCTR Hypersonic Physics Summary",
        f"- Samples: {len(points)}",
        f"- Max Mach: {max_mach:.2f}",
        f"- Peak Heat Flux: {peak_heat:.3f} MW/m^2",
        f"- Min TPS Margin: {min_tps_margin:.3f} MW/m^2",
        f"- Time Over TPS Limit: {overheat_pct:.1f}%",
        f"- Peak Dynamic Pressure: {peak_q:.1f} kPa",
        f"- Max L/D: {max_ld:.2f}",
        f"- Minimum Static Margin Proxy: {min_static:.2f}",
        f"- Final Altitude: {final.altitude_m/1000.0:.1f} km",
        f"- Final Downrange: {final.downrange_m/1000.0:.1f} km",
    ]
    return "\n".join(lines)


def _print_samples(points) -> None:
    print("\nTimeline (20-second cadence)")
    print("t(s) | Mach | Alt(km) | alpha(deg) | L/D | Heat(MW/m^2) | TPS Margin")
    for point in points:
        if abs(point.t_s % 20.0) < 1e-6:
            print(
                f"{point.t_s:4.0f} | {point.mach:4.2f} | {point.altitude_m/1000.0:7.2f} | "
                f"{point.alpha_deg:9.2f} | {point.ld_ratio:4.2f} | "
                f"{point.heat_flux_mw_m2:11.3f} | {point.tps_margin_mw_m2:9.3f}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="PROTCTR hypersonic concept simulator")
    parser.add_argument("--duration", type=float, default=260.0, help="simulation duration in seconds")
    parser.add_argument("--dt", type=float, default=0.5, help="simulation time step in seconds")
    parser.add_argument("--altitude", type=float, default=19000.0, help="initial altitude in meters")
    parser.add_argument("--mach", type=float, default=3.4, help="initial Mach number")
    parser.add_argument("--gamma", type=float, default=9.0, help="initial flight path angle in degrees")
    parser.add_argument("--csv", type=Path, default=None, help="optional CSV output path")
    parser.add_argument("--plot", action="store_true", help="write a PNG plot from CSV data")
    parser.add_argument(
        "--plot-out",
        type=Path,
        default=DEFAULT_PLOT_PATH,
        help=f"PNG output path (default: {DEFAULT_PLOT_PATH})",
    )
    parser.add_argument("--show-plot", action="store_true", help="display an interactive plot window")
    parser.add_argument(
        "--plot-csv",
        type=Path,
        default=None,
        help="plot an existing CSV profile and skip simulation",
    )
    args = parser.parse_args()

    if args.plot_csv is not None:
        should_save_plot = args.plot or not args.show_plot
        png_target = args.plot_out if should_save_plot else None
        saved = plot_profile_from_csv(args.plot_csv, png_path=png_target, show=args.show_plot)
        if saved is not None:
            print(f"Plot written to: {saved}")
        if args.show_plot:
            print("Interactive plot displayed.")
        return

    vehicle = default_vehicle()
    config = SimulationConfig(
        duration_s=args.duration,
        dt_s=args.dt,
        initial_altitude_m=args.altitude,
        initial_mach=args.mach,
        initial_gamma_deg=args.gamma,
    )
    points = simulate(vehicle, config)

    print(_format_summary(points, vehicle.tps_heat_limit_mw_m2))
    _print_samples(points)

    csv_target = args.csv
    if csv_target is None and (args.plot or args.show_plot):
        csv_target = DEFAULT_CSV_PATH

    if csv_target is not None:
        write_csv(points, csv_target)
        print(f"\nCSV written to: {csv_target}")

    if args.plot or args.show_plot:
        saved = plot_profile_from_csv(csv_target, png_path=args.plot_out if args.plot else None, show=args.show_plot)
        if saved is not None:
            print(f"Plot written to: {saved}")
        if args.show_plot:
            print("Interactive plot displayed.")


if __name__ == "__main__":
    main()
