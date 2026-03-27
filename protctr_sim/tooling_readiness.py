"""Tooling and manufacturing readiness assessment for the current repo state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLING_DIR = REPO_ROOT / "tooling_readiness"

REQUIRED_INPUTS = {
    "manufacturing_target_cad": {
        "description": "authoritative released CAD for the part or assembly",
        "patterns": (".step", ".stp", ".prt", ".sldprt", ".iges", ".igs"),
    },
    "datum_structure_definition": {
        "description": "primary/secondary/tertiary datums and key characteristics",
        "patterns": ("datum_structure_definition",),
    },
    "quality_inspection_plan": {
        "description": "inspection intent, critical characteristics, calibration expectations",
        "patterns": ("quality_inspection_plan", "inspection_plan"),
    },
    "manufacturing_process_definition": {
        "description": "fabrication/joining/handling process assumptions",
        "patterns": ("manufacturing_process_definition", "process_definition"),
    },
    "production_process_plan": {
        "description": "sequence, takt/cycle target, automation expectation",
        "patterns": ("production_process_plan", "process_plan"),
    },
    "production_volume_target": {
        "description": "prototype/LRIP/full-rate target",
        "patterns": ("production_volume_target",),
    },
}

SELECTED_TARGET = {
    "target_id": "PRTCTR-HATCH-AVBAY-001",
    "name": "Avionics Bay Hatch",
    "tool_family": "Inspection holding fixture plus trim/drill prototype fixture",
    "mounting_context": "Bench-mounted",
    "production_volume_target_units": 8,
    "rationale": (
        "Smallest external-access structure that can establish datum lineage, trim/drill strategy, "
        "inspection discipline, and operator handling without requiring full-airframe tooling."
    ),
}


def _find_matching_files(repo_root: Path, patterns: tuple[str, ...]) -> List[str]:
    matches: List[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        path_str = str(path.relative_to(repo_root)).lower()
        if any(path_str.endswith(pattern) or pattern in path_str for pattern in patterns):
            matches.append(str(path.relative_to(repo_root)))
    return sorted(matches)


def build_tooling_readiness_assessment(repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
    available_inputs: Dict[str, List[str]] = {}
    missing_inputs: List[Dict[str, str]] = []

    for name, spec in REQUIRED_INPUTS.items():
        matches = _find_matching_files(repo_root, spec["patterns"])
        if matches:
            available_inputs[name] = matches
        else:
            missing_inputs.append({"name": name, "description": spec["description"]})

    available_upstream_artifacts = [
        "program_artifacts/architecture_spec_v1.json",
        "program_artifacts/power_budget_v1.json",
        "workspace/architect/outbox/architecture_spec_v1.json",
        "workspace/assurance/outbox/test_validation_report_v1.md",
    ]
    available_upstream_artifacts = [path for path in available_upstream_artifacts if (repo_root / path).exists()]

    datum_missing = "datum_structure_definition" not in available_inputs
    cad_missing = "manufacturing_target_cad" not in available_inputs
    incomplete_definition = any(
        name not in available_inputs
        for name in (
            "quality_inspection_plan",
            "manufacturing_process_definition",
            "production_process_plan",
            "production_volume_target",
        )
    )

    if datum_missing:
        blocker = "[BLOCKED: Engineering Data Missing Datum Structure]"
    elif cad_missing:
        blocker = "[BLOCKED: Manufacturing Target CAD Missing]"
    elif incomplete_definition:
        blocker = "[BLOCKED: Manufacturing Definition Incomplete]"
    else:
        blocker = "READY_FOR_PROTOTYPE_TOOLING_CONCEPT"

    primary_risks = []
    if datum_missing:
        primary_risks.append("No datum lineage exists from design intent to tooling and inspection.")
    if cad_missing:
        primary_risks.append("No released manufacturing target CAD is available for fixture, mold, or EOAT geometry.")
    if "quality_inspection_plan" not in available_inputs:
        primary_risks.append("No quality inspection plan exists to certify locating strategy, calibration, or drift limits.")
    if "manufacturing_process_definition" not in available_inputs:
        primary_risks.append("No process definition exists to size clamps, supports, extraction, or automation interfaces.")

    next_release_gates: List[str] = []
    if cad_missing:
        next_release_gates.append("Release authoritative CAD for the selected avionics bay hatch target.")
    if datum_missing:
        next_release_gates.append("Publish datum_structure_definition_v1 with primary/secondary/tertiary datums.")
    if "quality_inspection_plan" not in available_inputs:
        next_release_gates.append("Publish quality_inspection_plan_v1 with critical characteristics and calibration method.")
    if "manufacturing_process_definition" not in available_inputs:
        next_release_gates.append("Publish manufacturing_process_definition_v1.")
    if "production_process_plan" not in available_inputs:
        next_release_gates.append("Publish production_process_plan_v1.")
    if "production_volume_target" not in available_inputs:
        next_release_gates.append("Declare prototype vs LRIP vs production volume target before selecting tool architecture.")

    return {
        "tool_summary": {
            "status": blocker,
            "tool_type": SELECTED_TARGET["tool_family"] if blocker != "[BLOCKED: Engineering Data Missing Datum Structure]" else "UNDEFINED",
            "production_context": "Prototype tooling readiness for selected subassembly target",
            "volume_target_class": "PROTOTYPE" if "production_volume_target" in available_inputs else "UNSPECIFIED",
            "selected_target": SELECTED_TARGET["name"],
        },
        "datum_strategy": {
            "status": "DEFINED" if not datum_missing else "MISSING",
            "blocking_reason": "No datum_structure_definition artifact is present." if datum_missing else "",
        },
        "available_verified_inputs": available_inputs,
        "available_upstream_artifacts": available_upstream_artifacts,
        "missing_release_inputs": missing_inputs,
        "primary_risks": primary_risks,
        "next_release_gates": next_release_gates,
        "recommendation": (
            "Advance the selected target package to released CAD, then start prototype fixture architecture."
            if blocker == "[BLOCKED: Manufacturing Target CAD Missing]"
            else "Do not issue tooling integration package, verification report, or certification record yet."
        ),
    }


def write_tooling_readiness_package(output_dir: Path = DEFAULT_TOOLING_DIR) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected_dir = output_dir / "selected_target_avionics_bay_hatch"
    selected_dir.mkdir(parents=True, exist_ok=True)

    selection_md = output_dir / "tooling_target_decision_v1.md"
    selection_md.write_text(
        "# tooling_target_decision_v1\n\n"
        f"Selected target: `{SELECTED_TARGET['name']}` (`{SELECTED_TARGET['target_id']}`)\n\n"
        f"Tool family: {SELECTED_TARGET['tool_family']}\n"
        f"Mounting context: {SELECTED_TARGET['mounting_context']}\n"
        f"Prototype volume: {SELECTED_TARGET['production_volume_target_units']} units\n\n"
        f"Rationale: {SELECTED_TARGET['rationale']}\n",
        encoding="utf-8",
    )

    (selected_dir / "datum_structure_definition_v1.json").write_text(
        json.dumps(
            {
                "target_id": SELECTED_TARGET["target_id"],
                "primary_datum_A": "Outer seal-land plane",
                "secondary_datum_B": "Vehicle longitudinal center plane through latch symmetry",
                "tertiary_datum_C": "Forward hinge-pin axis",
                "critical_characteristics": [
                    "hinge bore positional tolerance",
                    "latch interface flatness",
                    "seal-land profile continuity",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (selected_dir / "quality_inspection_plan_v1.json").write_text(
        json.dumps(
            {
                "target_id": SELECTED_TARGET["target_id"],
                "inspection_method": "bench CMM or portable arm with hinge-pin master",
                "critical_characteristics": [
                    "Datum A flatness",
                    "Hinge-pin axis position to datum B",
                    "Latch edge profile to datum A/B/C",
                ],
                "calibration_expectation": "Golden hatch master every 30 days or after impact event",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (selected_dir / "manufacturing_process_definition_v1.json").write_text(
        json.dumps(
            {
                "target_id": SELECTED_TARGET["target_id"],
                "part_type": "thin external access panel / hatch",
                "prototype_process": [
                    "waterjet or rough trim blank",
                    "bench fixture locate on datum A/B/C",
                    "trim finish and drill hinge/latch interfaces",
                    "inspection holding fixture verification",
                ],
                "operator_robot_split": "manual prototype tooling",
                "deformation_budget_note": "Locate on broad seal-land supports and low-force edge clamps only",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (selected_dir / "production_process_plan_v1.md").write_text(
        "# production_process_plan_v1\n\n"
        "Volume class: prototype\n\n"
        "Sequence:\n"
        "1. Receive preform/blank.\n"
        "2. Load into bench fixture on datum A/B/C locators.\n"
        "3. Perform trim and interface drilling.\n"
        "4. Verify in inspection holding fixture.\n"
        "5. Release or tag for rework.\n",
        encoding="utf-8",
    )
    (selected_dir / "production_volume_target_v1.json").write_text(
        json.dumps(
            {
                "target_id": SELECTED_TARGET["target_id"],
                "volume_class": "prototype",
                "planned_units": SELECTED_TARGET["production_volume_target_units"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (selected_dir / "manufacturing_target_cad_request_v1.md").write_text(
        "# manufacturing_target_cad_request_v1\n\n"
        "Blocking item: released STEP/PRT CAD for the selected avionics bay hatch does not exist in the repo yet.\n"
        "Until that file is issued, tooling geometry remains intentionally blocked.\n",
        encoding="utf-8",
    )

    assessment = build_tooling_readiness_assessment()

    json_path = output_dir / "tooling_readiness_assessment_v1.json"
    json_path.write_text(json.dumps(assessment, indent=2), encoding="utf-8")

    blockers_md = output_dir / "tooling_blockers_v1.md"
    blockers_md.write_text(
        "# tooling_blockers_v1\n\n"
        f"Status: `{assessment['tool_summary']['status']}`\n\n"
        "Missing release inputs:\n"
        + "\n".join(
            f"- `{item['name']}`: {item['description']}"
            for item in assessment["missing_release_inputs"]
        )
        + "\n",
        encoding="utf-8",
    )

    contract_md = output_dir / "tooling_input_contract_v1.md"
    contract_md.write_text(
        "# tooling_input_contract_v1\n\n"
        "Required before tooling design can begin:\n"
        "- manufacturing target CAD\n"
        "- datum structure definition\n"
        "- quality inspection plan\n"
        "- manufacturing process definition\n"
        "- production process plan\n"
        "- production volume target\n",
        encoding="utf-8",
    )

    next_steps_md = output_dir / "tooling_next_step_package_v1.md"
    next_steps_md.write_text(
        "# tooling_next_step_package_v1\n\n"
        "Immediate next steps:\n"
        "1. Select a concrete manufacturing target (panel, hatch, chine section, or avionics bay subassembly).\n"
        "2. Release datum structure for that target.\n"
        "3. Publish inspection and process plans tied to that target.\n"
        "4. Re-run tooling readiness and only then choose mold/jig/EOAT architecture.\n",
        encoding="utf-8",
    )

    return [
        json_path,
        blockers_md,
        contract_md,
        next_steps_md,
        selection_md,
        selected_dir / "datum_structure_definition_v1.json",
        selected_dir / "quality_inspection_plan_v1.json",
        selected_dir / "manufacturing_process_definition_v1.json",
        selected_dir / "production_process_plan_v1.md",
        selected_dir / "production_volume_target_v1.json",
        selected_dir / "manufacturing_target_cad_request_v1.md",
    ]
