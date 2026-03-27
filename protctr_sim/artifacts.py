"""Program artifact generation for the PROTCTR concept."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .simulator import SimulationConfig, simulate
from .vehicle import default_vehicle

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_DIR = REPO_ROOT / "program_artifacts"


def _default_timeline() -> List[Dict[str, Any]]:
    points = simulate(default_vehicle(), SimulationConfig())
    return [asdict(point) for point in points]


def build_architecture_spec() -> Dict[str, Any]:
    vehicle = default_vehicle()
    return {
        "artifact": "architecture_spec_v1",
        "designation": vehicle.designation,
        "mission_class": "Conceptual hypersonic surveillance and systems-pathfinder demonstrator",
        "airframe": {
            "planform": "Blended wing body with waverider wedge integration",
            "length_m": vehicle.length_m,
            "span_m": vehicle.span_m,
            "reference_area_m2": vehicle.reference_area_m2,
            "fineness_ratio": round(vehicle.fineness_ratio, 3),
            "sweep_deg": vehicle.sweep_deg,
            "nose_radius_m": vehicle.nose_radius_m,
        },
        "subsystems": {
            "flight_sciences": "2D point-mass dynamics with hypersonic aero/heating model",
            "propulsion": "Booster to scramjet envelope approximation",
            "thermal_protection": "Carbon-carbon / TPS concept with 2.5 MW/m^2 conceptual limit",
            "stability": "Twin-tail wake-avoidance stability proxy",
            "mission_software": "FastAPI webapp plus CLI simulation and plotting",
        },
        "mosa_interfaces": [
            "SimulationConfig input contract",
            "SimPoint timeline schema",
            "CSV profile export format",
            "Web API /api/simulate and /api/program",
        ],
        "constraints": {
            "status": "conceptual",
            "notes": [
                "No 6-DOF flight control law implemented",
                "No CFD or structural FEM in repository",
                "Claims must be labeled model-predicted unless validated by test evidence",
            ],
        },
    }


def build_power_budget() -> Dict[str, Any]:
    items = [
        {"subsystem": "Flight computer", "power_w": 180},
        {"subsystem": "Navigation / IMU / GNSS", "power_w": 85},
        {"subsystem": "Telemetry / secure datalink", "power_w": 240},
        {"subsystem": "TPS sensing and health monitoring", "power_w": 65},
        {"subsystem": "Actuation and control surfaces", "power_w": 420},
        {"subsystem": "Mission payload reserve", "power_w": 350},
    ]
    total_w = sum(item["power_w"] for item in items)
    return {
        "artifact": "power_budget_v1",
        "voltage_bus_vdc": 270,
        "items": items,
        "total_continuous_power_w": total_w,
        "growth_margin_pct": 20,
        "total_with_margin_w": round(total_w * 1.2, 1),
        "status": "notional architecture estimate",
    }


def build_rf_link_budget() -> Dict[str, Any]:
    return {
        "artifact": "rf_link_budget_v1",
        "status": "notional",
        "mission_link": "Long-range telemetry and command relay",
        "assumptions": [
            "BLOS relay architecture required for operationally relevant ranges",
            "Encryption and export compliance are architecture constraints",
            "Detailed waveform and antenna trades remain open",
        ],
    }


def build_interface_control_doc() -> Dict[str, Any]:
    return {
        "artifact": "interface_control_doc_v1",
        "interfaces": [
            {"name": "SimulationConfig", "type": "input", "format": "JSON / CLI flags"},
            {"name": "SimPoint timeline", "type": "output", "format": "JSON / CSV"},
            {"name": "/api/simulate", "type": "web", "format": "POST JSON"},
            {"name": "/api/program", "type": "web", "format": "GET JSON"},
        ],
        "mosa_note": "Interfaces are versionable, separable, and usable without coupling to UI internals.",
    }


def build_validated_claims() -> List[Dict[str, str]]:
    timeline = _default_timeline()
    peak_mach = max(point["mach"] for point in timeline)
    peak_heat = max(point["heat_flux_mw_m2"] for point in timeline)
    peak_alt_km = max(point["altitude_m"] for point in timeline) / 1000.0
    range_km = timeline[-1]["downrange_m"] / 1000.0
    return [
        {
            "claim": f"Model predicts nominal profile peak Mach of {peak_mach:.2f}.",
            "claim_type": "analysis-backed conceptual",
            "evidence": "program_artifacts/test_validation_report_v1.md",
        },
        {
            "claim": f"Model predicts peak heating of {peak_heat:.3f} MW/m^2 under default profile.",
            "claim_type": "analysis-backed conceptual",
            "evidence": "program_artifacts/test_validation_report_v1.md",
        },
        {
            "claim": f"Model reaches approximately {peak_alt_km:.1f} km altitude and {range_km:.1f} km downrange in the default profile.",
            "claim_type": "analysis-backed conceptual",
            "evidence": "program_artifacts/test_validation_report_v1.md",
        },
        {
            "claim": "Interactive webapp reproduces simulation state transitions and blueprint subsystem inspection.",
            "claim_type": "software-verified",
            "evidence": "tests/test_webapp_api.py",
        },
    ]


def build_program_summary() -> Dict[str, Any]:
    return {
        "market_requirements": {
            "mission": "Long-range desert surveillance and rapid-response pathfinder",
            "theater": "High-temperature, long-baseline MENA operations",
            "operator_priorities": ["thermal survivability", "range", "modular avionics", "traceable claims"],
        },
        "mission_conops": {
            "phases": [
                "Boost and acceleration",
                "Hypersonic cruise in thin upper-atmosphere corridor",
                "Telemetry and health-monitoring pass",
                "Terminal mission or recovery concept branch",
            ]
        },
        "constraints": {
            "export_control": "Conceptual only. No implementation of restricted comms, guidance, or weaponization.",
            "anti_corruption": "No customer-specific or procurement content in code artifacts.",
            "physics_reality": "All performance statements remain model-predicted unless test-backed.",
        },
        "architecture_spec": build_architecture_spec(),
        "power_budget": build_power_budget(),
        "rf_link_budget": build_rf_link_budget(),
        "interface_control_doc": build_interface_control_doc(),
        "validated_claims": build_validated_claims(),
    }


def write_program_artifacts(output_dir: Path = DEFAULT_ARTIFACT_DIR) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    program = build_program_summary()
    timeline = _default_timeline()
    peak_mach = max(point["mach"] for point in timeline)
    peak_heat = max(point["heat_flux_mw_m2"] for point in timeline)
    peak_alt_km = max(point["altitude_m"] for point in timeline) / 1000.0

    files: Dict[str, str] = {
        "market_requirements_doc.md": (
            "# market_requirements_doc\n\n"
            "Mission: Long-range desert surveillance and rapid-response pathfinder.\n\n"
            "Priority characteristics:\n"
            "- High-temperature survivability in arid operating envelopes\n"
            "- Long-baseline reach with modular comms integration\n"
            "- MOSA-style avionics boundaries for rapid iteration\n"
            "- Evidence-backed claims only\n"
        ),
        "mission_conops_v1.md": (
            "# mission_conops_v1\n\n"
            "1. Launch and accelerate with booster assistance.\n"
            "2. Transition into shock-riding hypersonic corridor.\n"
            "3. Maintain telemetry/health monitoring through cruise segment.\n"
            "4. Execute mission branch or recovery branch depending payload fit.\n"
        ),
        "constraints_export_control_v1.md": (
            "# constraints_export_control_v1\n\n"
            "- Repository scope is conceptual simulation and UI only.\n"
            "- No deployable guidance, targeting, or restricted comms implementation.\n"
            "- All claims remain conceptual unless tied to explicit validation evidence.\n"
        ),
        "rf_link_budget_v1.md": (
            "# rf_link_budget_v1\n\n"
            "Status: notional.\n\n"
            "- Requires BLOS relay architecture for operational relevance.\n"
            "- Encryption/export constraints are treated as architecture gates.\n"
            "- Detailed waveform and antenna pattern trades remain open.\n"
        ),
        "interface_control_doc_v1.md": (
            "# interface_control_doc_v1\n\n"
            "Interfaces:\n"
            "- `SimulationConfig`: JSON/CLI input contract\n"
            "- `SimPoint timeline`: JSON/CSV output contract\n"
            "- `/api/simulate`: POST JSON\n"
            "- `/api/program`: GET JSON\n"
        ),
        "test_validation_report_v1.md": (
            "# test_validation_report_v1\n\n"
            "Validation basis:\n"
            "- `python3 -m unittest discover -s tests -v`\n"
            "- `python3 -m compileall protctr_sim webapp run_sim.py run_webapp.py tests`\n\n"
            "Default-profile observations:\n"
            f"- Peak Mach: {peak_mach:.2f}\n"
            f"- Peak heat flux: {peak_heat:.3f} MW/m^2\n"
            f"- Peak altitude: {peak_alt_km:.1f} km\n"
            "- Status: software validation only; no hardware or wind-tunnel evidence in repo.\n"
        ),
        "validated_claims_sheet_v1.md": (
            "# validated_claims_sheet_v1\n\n"
            "| Claim | Type | Evidence |\n"
            "| --- | --- | --- |\n"
            + "\n".join(
                f"| {item['claim']} | {item['claim_type']} | {item['evidence']} |"
                for item in program["validated_claims"]
            )
            + "\n"
        ),
    }

    json_files: Dict[str, Any] = {
        "architecture_spec_v1.json": program["architecture_spec"],
        "power_budget_v1.json": program["power_budget"],
    }

    written: List[Path] = []
    for filename, content in files.items():
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)

    for filename, payload in json_files.items():
        path = output_dir / filename
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(path)

    return written
