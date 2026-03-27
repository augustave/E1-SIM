"""Interactive PROTCTR aerodynamic simulation webapp."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from protctr_sim.artifacts import DEFAULT_ARTIFACT_DIR, build_program_summary, write_program_artifacts
from protctr_sim.physics import ControlState
from protctr_sim.simulator import FlightState, SimulationConfig, simulate
from protctr_sim.tooling_readiness import (
    DEFAULT_TOOLING_DIR,
    build_tooling_readiness_assessment,
    write_tooling_readiness_package,
)
from protctr_sim.vehicle import default_vehicle
from protctr_sim.workspace import DEFAULT_WORKSPACE_DIR, build_workspace_manifest, write_swarm_workspace

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PROGRAM_ARTIFACTS_DIR = DEFAULT_ARTIFACT_DIR
WORKSPACE_DIR = DEFAULT_WORKSPACE_DIR
TOOLING_DIR = DEFAULT_TOOLING_DIR


def _ensure_workspace_assets() -> None:
    expected_artifact = PROGRAM_ARTIFACTS_DIR / "architecture_spec_v1.json"
    expected_workspace = WORKSPACE_DIR / "shared" / "handoff_manifest_v1.json"
    expected_tooling = TOOLING_DIR / "tooling_readiness_assessment_v1.json"
    if not expected_artifact.exists():
        write_program_artifacts(PROGRAM_ARTIFACTS_DIR)
    if not expected_workspace.exists():
        write_swarm_workspace(WORKSPACE_DIR)
    if not expected_tooling.exists():
        write_tooling_readiness_package(TOOLING_DIR)

app = FastAPI(title="PROTCTR Aerodynamic Webapp", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
PROGRAM_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
TOOLING_DIR.mkdir(parents=True, exist_ok=True)
_ensure_workspace_assets()
app.mount("/program-artifacts", StaticFiles(directory=PROGRAM_ARTIFACTS_DIR), name="program-artifacts")
app.mount("/workspace-files", StaticFiles(directory=WORKSPACE_DIR), name="workspace-files")
app.mount("/tooling-readiness-files", StaticFiles(directory=TOOLING_DIR), name="tooling-readiness-files")


class SimulationRequest(BaseModel):
    duration_s: float = Field(default=260.0, ge=10.0, le=1200.0)
    dt_s: float = Field(default=0.5, gt=0.05, le=5.0)
    initial_altitude_m: float = Field(default=19000.0, ge=0.0, le=47000.0)
    initial_mach: float = Field(default=3.4, ge=0.3, le=12.0)
    initial_gamma_deg: float = Field(default=9.0, ge=-20.0, le=30.0)
    wing_morph_pct: float = Field(default=0.0, ge=-0.25, le=0.25)
    flap_deflection_deg: float = Field(default=0.0, ge=-5.0, le=20.0)
    body_morph_pct: float = Field(default=0.0, ge=-0.20, le=0.20)


class FlightStateRequest(BaseModel):
    t_s: float = Field(ge=0.0)
    altitude_m: float = Field(ge=0.0)
    downrange_m: float = Field(ge=0.0)
    velocity_m_s: float = Field(gt=0.0)
    gamma_deg: float = Field(ge=-30.0, le=30.0)


class ContinuationRequest(BaseModel):
    duration_s: float = Field(default=120.0, ge=2.0, le=1200.0)
    dt_s: float = Field(default=0.5, gt=0.05, le=5.0)
    state: FlightStateRequest
    wing_morph_pct: float = Field(default=0.0, ge=-0.25, le=0.25)
    flap_deflection_deg: float = Field(default=0.0, ge=-5.0, le=20.0)
    body_morph_pct: float = Field(default=0.0, ge=-0.20, le=0.20)


def _control_state_from_request(req: SimulationRequest | ContinuationRequest) -> ControlState:
    return ControlState(
        wing_morph_pct=req.wing_morph_pct,
        flap_deflection_deg=req.flap_deflection_deg,
        body_morph_pct=req.body_morph_pct,
    )


def _build_summary(timeline: List[Dict[str, Any]], heat_limit_mw_m2: float) -> Dict[str, float]:
    return {
        "samples": len(timeline),
        "max_mach": max(point["mach"] for point in timeline),
        "max_altitude_km": max(point["altitude_m"] for point in timeline) / 1000.0,
        "range_km": timeline[-1]["downrange_m"] / 1000.0,
        "peak_heat_flux_mw_m2": max(point["heat_flux_mw_m2"] for point in timeline),
        "min_tps_margin_mw_m2": min(point["tps_margin_mw_m2"] for point in timeline),
        "time_over_tps_limit_pct": 100.0
        * sum(point["heat_flux_mw_m2"] > heat_limit_mw_m2 for point in timeline)
        / len(timeline),
        "max_ld_ratio": max(point["ld_ratio"] for point in timeline),
    }


def _simulation_response(points: List[Dict[str, Any]], vehicle) -> Dict[str, Any]:
    return {
        "vehicle": {
            "designation": vehicle.designation,
            "length_m": vehicle.length_m,
            "span_m": vehicle.span_m,
            "reference_area_m2": vehicle.reference_area_m2,
            "fineness_ratio": vehicle.fineness_ratio,
            "sweep_deg": vehicle.sweep_deg,
            "tps_heat_limit_mw_m2": vehicle.tps_heat_limit_mw_m2,
        },
        "summary": _build_summary(points, vehicle.tps_heat_limit_mw_m2),
        "timeline": points,
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/program")
def program_summary() -> Dict[str, Any]:
    program = build_program_summary()
    artifact_names = [
        "market_requirements_doc.md",
        "mission_conops_v1.md",
        "constraints_export_control_v1.md",
        "architecture_spec_v1.json",
        "power_budget_v1.json",
        "rf_link_budget_v1.md",
        "interface_control_doc_v1.md",
        "test_validation_report_v1.md",
        "validated_claims_sheet_v1.md",
    ]
    program["artifact_urls"] = {
        name: f"/program-artifacts/{name}"
        for name in artifact_names
        if (PROGRAM_ARTIFACTS_DIR / name).exists()
    }
    program["workspace_manifest_url"] = "/workspace-files/shared/handoff_manifest_v1.json"
    return program


@app.get("/api/workspace")
def workspace_summary() -> Dict[str, Any]:
    manifest = build_workspace_manifest()
    manifest["manifest_url"] = "/workspace-files/shared/handoff_manifest_v1.json"
    return manifest


@app.get("/api/tooling-readiness")
def tooling_readiness_summary() -> Dict[str, Any]:
    assessment = build_tooling_readiness_assessment()
    assessment["files"] = {
        "assessment": "/tooling-readiness-files/tooling_readiness_assessment_v1.json",
        "blockers": "/tooling-readiness-files/tooling_blockers_v1.md",
        "contract": "/tooling-readiness-files/tooling_input_contract_v1.md",
        "next_steps": "/tooling-readiness-files/tooling_next_step_package_v1.md",
        "target_decision": "/tooling-readiness-files/tooling_target_decision_v1.md",
        "selected_target_datum": "/tooling-readiness-files/selected_target_avionics_bay_hatch/datum_structure_definition_v1.json",
        "selected_target_quality": "/tooling-readiness-files/selected_target_avionics_bay_hatch/quality_inspection_plan_v1.json",
        "selected_target_process": "/tooling-readiness-files/selected_target_avionics_bay_hatch/manufacturing_process_definition_v1.json",
        "selected_target_plan": "/tooling-readiness-files/selected_target_avionics_bay_hatch/production_process_plan_v1.md",
        "selected_target_volume": "/tooling-readiness-files/selected_target_avionics_bay_hatch/production_volume_target_v1.json",
    }
    return assessment


@app.post("/api/simulate")
def run_simulation(req: SimulationRequest) -> Dict[str, Any]:
    vehicle = default_vehicle()
    config = SimulationConfig(
        duration_s=req.duration_s,
        dt_s=req.dt_s,
        initial_altitude_m=req.initial_altitude_m,
        initial_mach=req.initial_mach,
        initial_gamma_deg=req.initial_gamma_deg,
        controls=_control_state_from_request(req),
    )
    points = simulate(vehicle, config)
    timeline = [asdict(point) for point in points]
    return _simulation_response(timeline, vehicle)


@app.post("/api/continue")
def continue_simulation(req: ContinuationRequest) -> Dict[str, Any]:
    vehicle = default_vehicle()
    config = SimulationConfig(
        duration_s=req.duration_s,
        dt_s=req.dt_s,
        controls=_control_state_from_request(req),
    )
    initial_state = FlightState(
        t_s=req.state.t_s,
        altitude_m=req.state.altitude_m,
        downrange_m=req.state.downrange_m,
        velocity_m_s=req.state.velocity_m_s,
        gamma_deg=req.state.gamma_deg,
    )
    points = simulate(vehicle, config, initial_state=initial_state)
    timeline = [asdict(point) for point in points]
    return _simulation_response(timeline, vehicle)
