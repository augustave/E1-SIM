"""Time-marching point-mass simulator for the PROTCTR concept."""

from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, List

from .atmosphere import G0, isa_atmosphere
from .physics import ControlState, aerodynamic_model, alpha_schedule_deg, thrust_model
from .vehicle import ProtctrVehicle

EARTH_RADIUS_M = 6_371_000.0


@dataclass(frozen=True)
class SimulationConfig:
    duration_s: float = 260.0
    dt_s: float = 0.5
    initial_altitude_m: float = 19000.0
    initial_mach: float = 3.4
    initial_gamma_deg: float = 9.0
    controls: ControlState = field(default_factory=ControlState)


@dataclass(frozen=True)
class FlightState:
    t_s: float
    altitude_m: float
    downrange_m: float
    velocity_m_s: float
    gamma_deg: float


@dataclass(frozen=True)
class SimPoint:
    t_s: float
    altitude_m: float
    downrange_m: float
    velocity_m_s: float
    gamma_deg: float
    mach: float
    alpha_deg: float
    q_dyn_kpa: float
    lift_kn: float
    drag_kn: float
    thrust_kn: float
    cl: float
    cd: float
    ld_ratio: float
    heat_flux_mw_m2: float
    static_margin_proxy: float
    tps_margin_mw_m2: float
    wing_morph_pct: float
    flap_deflection_deg: float
    body_morph_pct: float
    effective_sweep_deg: float
    effective_area_factor: float


def _initial_flight_state(config: SimulationConfig) -> FlightState:
    atmosphere_0 = isa_atmosphere(config.initial_altitude_m)
    velocity = max(300.0, config.initial_mach * atmosphere_0.speed_of_sound_m_s)
    return FlightState(
        t_s=0.0,
        altitude_m=config.initial_altitude_m,
        downrange_m=0.0,
        velocity_m_s=velocity,
        gamma_deg=config.initial_gamma_deg,
    )


def point_to_flight_state(point: SimPoint) -> FlightState:
    return FlightState(
        t_s=point.t_s,
        altitude_m=point.altitude_m,
        downrange_m=point.downrange_m,
        velocity_m_s=point.velocity_m_s,
        gamma_deg=point.gamma_deg,
    )


def simulate(
    vehicle: ProtctrVehicle,
    config: SimulationConfig,
    initial_state: FlightState | None = None,
    control_schedule: Callable[[float, FlightState], ControlState] | None = None,
) -> List[SimPoint]:
    start_state = initial_state or _initial_flight_state(config)
    velocity = start_state.velocity_m_s
    altitude = start_state.altitude_m
    gamma = math.radians(start_state.gamma_deg)
    downrange = start_state.downrange_m
    start_time_s = start_state.t_s

    points: List[SimPoint] = []
    steps = int(config.duration_s / config.dt_s) + 1

    for i in range(steps):
        t_local = i * config.dt_s
        t = start_time_s + t_local
        atmo = isa_atmosphere(altitude)
        mach = max(0.01, velocity / atmo.speed_of_sound_m_s)
        current_state = FlightState(
            t_s=t,
            altitude_m=altitude,
            downrange_m=downrange,
            velocity_m_s=velocity,
            gamma_deg=math.degrees(gamma),
        )
        controls = control_schedule(t_local, current_state) if control_schedule else config.controls
        controls = controls.clamped()
        alpha_deg = alpha_schedule_deg(mach, altitude)
        aero = aerodynamic_model(vehicle, atmo, velocity, alpha_deg, controls)

        q_dyn = 0.5 * atmo.density_kg_m3 * velocity**2
        effective_area = vehicle.reference_area_m2 * aero.effective_area_factor
        lift = q_dyn * effective_area * aero.cl
        drag = q_dyn * effective_area * aero.cd
        thrust = thrust_model(altitude, mach)

        g = G0 * (EARTH_RADIUS_M / (EARTH_RADIUS_M + altitude)) ** 2
        d_v = ((thrust - drag) / vehicle.mass_kg - g * math.sin(gamma)) * config.dt_s
        gamma_term = lift / (vehicle.mass_kg * max(velocity, 1.0))
        curve_term = (velocity / (EARTH_RADIUS_M + altitude)) * math.cos(gamma)
        gravity_turn = (g / max(velocity, 1.0)) * math.cos(gamma)
        d_gamma = (gamma_term + curve_term - gravity_turn) * config.dt_s

        d_alt = velocity * math.sin(gamma) * config.dt_s
        d_x = velocity * math.cos(gamma) * config.dt_s

        tps_margin = vehicle.tps_heat_limit_mw_m2 - aero.heat_flux_mw_m2
        points.append(
            SimPoint(
                t_s=t,
                altitude_m=altitude,
                downrange_m=downrange,
                velocity_m_s=velocity,
                gamma_deg=math.degrees(gamma),
                mach=mach,
                alpha_deg=alpha_deg,
                q_dyn_kpa=q_dyn / 1000.0,
                lift_kn=lift / 1000.0,
                drag_kn=drag / 1000.0,
                thrust_kn=thrust / 1000.0,
                cl=aero.cl,
                cd=aero.cd,
                ld_ratio=aero.ld_ratio,
                heat_flux_mw_m2=aero.heat_flux_mw_m2,
                static_margin_proxy=aero.static_margin_proxy,
                tps_margin_mw_m2=tps_margin,
                wing_morph_pct=controls.wing_morph_pct,
                flap_deflection_deg=controls.flap_deflection_deg,
                body_morph_pct=controls.body_morph_pct,
                effective_sweep_deg=aero.effective_sweep_deg,
                effective_area_factor=aero.effective_area_factor,
            )
        )

        velocity = max(10.0, velocity + d_v)
        gamma = max(math.radians(-25.0), min(math.radians(30.0), gamma + d_gamma))
        altitude = max(0.0, altitude + d_alt)
        downrange += max(0.0, d_x)

        if altitude <= 0.0 and i > 0:
            break

    return points


def write_csv(points: List[SimPoint], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not points:
        return
    with output_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(asdict(points[0]).keys()))
        writer.writeheader()
        for point in points:
            writer.writerow(asdict(point))
