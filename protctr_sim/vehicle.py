"""Vehicle geometry and material-oriented parameters for PROTCTR."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtctrVehicle:
    designation: str
    mass_kg: float
    length_m: float
    span_m: float
    reference_area_m2: float
    nose_radius_m: float
    sweep_deg: float
    shock_capture_efficiency: float
    spine_compression_gain: float
    twin_tail_stability_gain: float
    base_cd0: float
    tps_heat_limit_mw_m2: float

    @property
    def aspect_ratio(self) -> float:
        return self.span_m**2 / self.reference_area_m2

    @property
    def mean_chord_m(self) -> float:
        return self.reference_area_m2 / self.span_m

    @property
    def fineness_ratio(self) -> float:
        return self.length_m / self.mean_chord_m


def default_vehicle() -> ProtctrVehicle:
    return ProtctrVehicle(
        designation="PROTCTR / E1",
        mass_kg=9000.0,
        length_m=21.0,
        span_m=8.6,
        reference_area_m2=34.0,
        nose_radius_m=0.028,
        sweep_deg=73.0,
        shock_capture_efficiency=0.90,
        spine_compression_gain=0.18,
        twin_tail_stability_gain=0.32,
        base_cd0=0.022,
        tps_heat_limit_mw_m2=2.5,
    )
