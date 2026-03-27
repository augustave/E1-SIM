"""Standard atmosphere utilities (0-47 km)."""

from __future__ import annotations

import math
from dataclasses import dataclass

G0 = 9.80665
R_AIR = 287.05
GAMMA_AIR = 1.4


@dataclass(frozen=True)
class AtmospherePoint:
    altitude_m: float
    temperature_k: float
    pressure_pa: float
    density_kg_m3: float
    speed_of_sound_m_s: float


def _layer_pressure(
    h_m: float,
    h0_m: float,
    t0_k: float,
    p0_pa: float,
    lapse_k_m: float,
) -> float:
    if abs(lapse_k_m) < 1e-12:
        return p0_pa * math.exp((-G0 / (R_AIR * t0_k)) * (h_m - h0_m))
    t_h = t0_k + lapse_k_m * (h_m - h0_m)
    return p0_pa * (t_h / t0_k) ** (-G0 / (R_AIR * lapse_k_m))


def isa_atmosphere(altitude_m: float) -> AtmospherePoint:
    """Return ISA-like atmospheric properties for 0-47km.

    Values above 47km are clamped to the 47km boundary.
    """

    h = max(0.0, min(47000.0, altitude_m))

    # Layer definitions: (h0, h1, lapse[K/m])
    layers = (
        (0.0, 11000.0, -0.0065),
        (11000.0, 20000.0, 0.0),
        (20000.0, 32000.0, 0.0010),
        (32000.0, 47000.0, 0.0028),
    )

    t0 = 288.15
    p0 = 101325.0
    h0 = 0.0

    for layer_h0, layer_h1, lapse in layers:
        if h <= layer_h1:
            t = t0 + lapse * (h - h0)
            p = _layer_pressure(h, h0, t0, p0, lapse)
            rho = p / (R_AIR * t)
            a = math.sqrt(GAMMA_AIR * R_AIR * t)
            return AtmospherePoint(h, t, p, rho, a)

        # march to top of layer as new base
        t_top = t0 + lapse * (layer_h1 - h0)
        p_top = _layer_pressure(layer_h1, h0, t0, p0, lapse)
        h0, t0, p0 = layer_h1, t_top, p_top

    # fallback (should be unreachable due to clamping)
    t = t0
    p = p0
    rho = p / (R_AIR * t)
    a = math.sqrt(GAMMA_AIR * R_AIR * t)
    return AtmospherePoint(h, t, p, rho, a)
