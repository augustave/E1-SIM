"""Aerothermodynamic and propulsion approximations for PROTCTR."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .atmosphere import AtmospherePoint
from .vehicle import ProtctrVehicle


@dataclass(frozen=True)
class ControlState:
    wing_morph_pct: float = 0.0
    flap_deflection_deg: float = 0.0
    body_morph_pct: float = 0.0

    def clamped(self) -> "ControlState":
        return ControlState(
            wing_morph_pct=max(-0.25, min(0.25, self.wing_morph_pct)),
            flap_deflection_deg=max(-5.0, min(20.0, self.flap_deflection_deg)),
            body_morph_pct=max(-0.20, min(0.20, self.body_morph_pct)),
        )


@dataclass(frozen=True)
class AeroResult:
    mach: float
    alpha_deg: float
    cl: float
    cd: float
    ld_ratio: float
    cm_alpha: float
    static_margin_proxy: float
    heat_flux_mw_m2: float
    effective_sweep_deg: float
    effective_area_factor: float
    controls: ControlState = field(default_factory=ControlState)


def _hypersonic_engagement(mach: float) -> float:
    return 1.0 - math.exp(-max(0.0, mach - 2.0) / 2.0)


def aerodynamic_model(
    vehicle: ProtctrVehicle,
    atmosphere: AtmospherePoint,
    velocity_m_s: float,
    alpha_deg: float,
    controls: ControlState | None = None,
) -> AeroResult:
    controls = (controls or ControlState()).clamped()
    mach = max(0.01, velocity_m_s / atmosphere.speed_of_sound_m_s)
    alpha_rad = math.radians(alpha_deg)
    effective_sweep_deg = vehicle.sweep_deg - 12.0 * controls.wing_morph_pct
    sweep_rad = math.radians(effective_sweep_deg)

    engagement = _hypersonic_engagement(mach)
    shock_gain = vehicle.shock_capture_efficiency * engagement * (1.0 + 0.10 * controls.wing_morph_pct)
    spine_gain = vehicle.spine_compression_gain * (0.5 + 0.5 * engagement)
    spine_gain *= 1.0 + 0.85 * controls.body_morph_pct
    flap_rad = math.radians(controls.flap_deflection_deg)
    effective_area_factor = 1.0 + 0.25 * controls.wing_morph_pct + 0.10 * max(0.0, controls.body_morph_pct)

    cl_alpha = 0.25 + 1.15 * shock_gain + 0.55 * spine_gain + 0.20 * math.cos(sweep_rad)
    cl = cl_alpha * alpha_rad
    cl += 0.85 * flap_rad * (0.65 + 0.35 * engagement)
    cl *= effective_area_factor
    cl *= 1.0 + 0.05 * max(0.0, mach - 5.0)
    cl = max(-0.2, min(1.5, cl))

    # Drag model: skin friction + wave drag + induced drag.
    cd_skin = vehicle.base_cd0 * (1.0 + 0.07 * math.sqrt(max(mach, 0.0)))
    cd_skin *= 1.0 + 0.20 * abs(controls.body_morph_pct) + 0.10 * abs(controls.wing_morph_pct)
    cd_wave = 0.13 * (alpha_rad**2 + 1.0 / (mach + 0.6) ** 2)
    cd_wave *= 1.0 - 0.20 * engagement
    cd_wave *= 1.0 + 0.18 * abs(controls.body_morph_pct)
    cd_flap = 0.055 * abs(flap_rad) * (0.8 + 0.2 * mach / (mach + 1.0))
    oswald_e = 0.78
    cd_induced = cl**2 / (math.pi * vehicle.aspect_ratio * oswald_e)
    cd = max(0.01, cd_skin + cd_wave + cd_induced + cd_flap)

    ld_ratio = cl / cd if cd > 0.0 else 0.0

    # Twin tails stay outside most of the hypersonic wake as Mach rises.
    wake_escape = 0.60 + 0.40 * (1.0 / (1.0 + math.exp(-(mach - 4.5))))
    cm_alpha = (
        -0.020
        - 0.022 * shock_gain
        - 0.018 * vehicle.twin_tail_stability_gain * wake_escape
        - 0.010 * abs(alpha_rad)
        - 0.008 * flap_rad
        + 0.005 * controls.body_morph_pct
    )
    static_margin_proxy = max(0.0, min(2.0, (-cm_alpha) / 0.03))

    # Sutton-Graves style stagnation-point convective heating estimate.
    heat_flux_w_m2 = 1.83e-4 * math.sqrt(atmosphere.density_kg_m3 / vehicle.nose_radius_m)
    heat_flux_w_m2 *= velocity_m_s**3
    heat_flux_w_m2 *= 1.0 + 0.10 * abs(controls.body_morph_pct) + 0.04 * abs(controls.wing_morph_pct)
    heat_flux_mw_m2 = heat_flux_w_m2 / 1.0e6

    return AeroResult(
        mach=mach,
        alpha_deg=alpha_deg,
        cl=cl,
        cd=cd,
        ld_ratio=ld_ratio,
        cm_alpha=cm_alpha,
        static_margin_proxy=static_margin_proxy,
        heat_flux_mw_m2=heat_flux_mw_m2,
        effective_sweep_deg=effective_sweep_deg,
        effective_area_factor=effective_area_factor,
        controls=controls,
    )


def thrust_model(altitude_m: float, mach: float) -> float:
    """Combined booster + scramjet envelope in Newtons."""

    altitude_factor = max(0.0, 1.0 - altitude_m / 47000.0)
    if mach < 3.8:
        return 210000.0 * altitude_factor

    scramjet_band = math.exp(-((mach - 6.6) ** 2) / 6.0)
    return 165000.0 * scramjet_band * (0.4 + 0.6 * altitude_factor)


def alpha_schedule_deg(mach: float, altitude_m: float) -> float:
    if mach < 2.0:
        alpha = 8.5
    elif mach < 5.0:
        alpha = 8.5 - (mach - 2.0) * (3.0 / 3.0)
    elif mach < 8.0:
        alpha = 5.5 - (mach - 5.0) * (2.2 / 3.0)
    else:
        alpha = 3.3 - min(1.4, (mach - 8.0) * 0.25)

    if altitude_m < 25000.0:
        alpha += 0.8
    return max(1.8, min(10.0, alpha))
