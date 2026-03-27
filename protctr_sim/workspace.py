"""Four-cell workspace generation for the PROTCTR program."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .artifacts import (
    DEFAULT_ARTIFACT_DIR,
    build_architecture_spec,
    build_power_budget,
    build_program_summary,
    write_program_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE_DIR = REPO_ROOT / "workspace"


def build_workspace_manifest() -> Dict[str, Any]:
    program = build_program_summary()
    return {
        "workspace_name": "PROTCTR Four-Cell Workspace",
        "cells": {
            "vanguard": {
                "role": "Market translation, mission framing, claims discipline",
                "inputs": ["validated claims", "assurance feedback"],
                "outputs": [
                    "market_requirements_doc_v1.md",
                    "mission_conops_v1.md",
                    "constraints_export_control_v1.md",
                    "capture_strategy_deck_v1.md",
                ],
            },
            "architect": {
                "role": "Flight sciences, MOSA architecture, subsystem definition",
                "inputs": ["vanguard handoff"],
                "outputs": [
                    "architecture_spec_v1.json",
                    "power_budget_v1.json",
                    "rf_link_budget_v1.md",
                    "interface_control_doc_v1.md",
                ],
            },
            "foundry": {
                "role": "Avionics integration planning, manufacturable build package placeholders",
                "inputs": ["architect handoff"],
                "outputs": [
                    "prototype_build_record_v1.md",
                    "pcb_fabrication_pack_v1.md",
                    "bringup_firmware_v1.md",
                ],
            },
            "assurance": {
                "role": "Validation, failure reporting, sign-off discipline",
                "inputs": ["foundry handoff"],
                "outputs": [
                    "test_validation_report_v1.md",
                    "bug_report_v1.md",
                    "root_cause_analysis_v1.md",
                ],
            },
        },
        "current_mission": program["market_requirements"]["mission"],
        "current_claim_count": len(program["validated_claims"]),
        "operator_workflow": [
            "Vanguard frames mission and guardrails",
            "Architect defines interfaces and budgets",
            "Foundry packages build intent and risks",
            "Assurance validates and feeds claims back to Vanguard",
        ],
    }


def write_swarm_workspace(output_dir: Path = DEFAULT_WORKSPACE_DIR) -> List[Path]:
    artifact_dir = DEFAULT_ARTIFACT_DIR
    write_program_artifacts(artifact_dir)

    vanguard_dir = output_dir / "vanguard"
    architect_dir = output_dir / "architect"
    foundry_dir = output_dir / "foundry"
    assurance_dir = output_dir / "assurance"
    shared_dir = output_dir / "shared"

    directories = [
        vanguard_dir / "inbox",
        vanguard_dir / "outbox",
        architect_dir / "inbox",
        architect_dir / "outbox",
        foundry_dir / "inbox",
        foundry_dir / "outbox",
        assurance_dir / "inbox",
        assurance_dir / "outbox",
        shared_dir,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    manifest = build_workspace_manifest()
    architecture_spec = build_architecture_spec()
    power_budget = build_power_budget()

    files: Dict[Path, str] = {
        output_dir / "README.md": (
            "# PROTCTR Four-Cell Workspace\n\n"
            "This workspace operationalizes the autonomous-aerospace-collective model.\n\n"
            "Flow:\n"
            "1. Vanguard issues market, CONOPS, and compliance framing.\n"
            "2. Architect publishes architecture, power, link, and interface artifacts.\n"
            "3. Foundry converts those into build-oriented handoff records.\n"
            "4. Assurance validates, reports, and closes the loop back to Vanguard.\n"
        ),
        vanguard_dir / "CELL_PROFILE.md": (
            "# Vanguard Cell Profile\n\n"
            "Primary workflow: translate mission demand into operator-ready requirements and evidence-safe claims.\n"
            "Acceptance: every outbound claim points to a validation source or is explicitly marked conceptual.\n"
        ),
        architect_dir / "CELL_PROFILE.md": (
            "# Architect Cell Profile\n\n"
            "Primary workflow: convert mission intent into flight-sciences, MOSA interfaces, and budget artifacts.\n"
            "Acceptance: architecture is traceable, modular, and consistent with simulation constraints.\n"
        ),
        foundry_dir / "CELL_PROFILE.md": (
            "# Foundry Cell Profile\n\n"
            "Primary workflow: prepare build-oriented artifacts, integration notes, and implementation risks.\n"
            "Acceptance: manufacturable intent, testability hooks, and unresolved blockers are explicit.\n"
        ),
        assurance_dir / "CELL_PROFILE.md": (
            "# Assurance Cell Profile\n\n"
            "Primary workflow: validate behavior, document failures mechanistically, and gate claims.\n"
            "Acceptance: no closure without evidence path or stated open risk.\n"
        ),
        vanguard_dir / "outbox" / "market_requirements_doc_v1.md": (
            "# market_requirements_doc_v1\n\n"
            "Canonical source: `program_artifacts/market_requirements_doc.md`\n\n"
            "Mission: long-range desert surveillance and systems pathfinder.\n"
        ),
        vanguard_dir / "outbox" / "mission_conops_v1.md": (
            "# mission_conops_v1\n\n"
            "Canonical source: `program_artifacts/mission_conops_v1.md`\n\n"
            "Operator flow: launch -> cruise corridor -> health-monitored pass -> mission branch.\n"
        ),
        vanguard_dir / "outbox" / "constraints_export_control_v1.md": (
            "# constraints_export_control_v1\n\n"
            "Canonical source: `program_artifacts/constraints_export_control_v1.md`\n\n"
            "Only conceptual modeling and evidence-safe claims are in scope.\n"
        ),
        architect_dir / "inbox" / "vanguard_handoff_v1.md": (
            "# vanguard_handoff_v1\n\n"
            "Received from Vanguard:\n"
            "- `../../vanguard/outbox/market_requirements_doc_v1.md`\n"
            "- `../../vanguard/outbox/mission_conops_v1.md`\n"
            "- `../../vanguard/outbox/constraints_export_control_v1.md`\n\n"
            "Design implication: prioritize thermal survivability, modular interfaces, and evidence discipline.\n"
        ),
        architect_dir / "outbox" / "rf_link_budget_v1.md": (
            "# rf_link_budget_v1\n\n"
            "Canonical source: `program_artifacts/rf_link_budget_v1.md`\n\n"
            "Status: notional BLOS relay architecture placeholder.\n"
        ),
        architect_dir / "outbox" / "interface_control_doc_v1.md": (
            "# interface_control_doc_v1\n\n"
            "Canonical source: `program_artifacts/interface_control_doc_v1.md`\n\n"
            "Operator-visible interfaces: CLI, CSV export, `/api/simulate`, `/api/program`.\n"
        ),
        foundry_dir / "inbox" / "architect_handoff_v1.md": (
            "# architect_handoff_v1\n\n"
            "Received from Architect:\n"
            "- `../../architect/outbox/architecture_spec_v1.json`\n"
            "- `../../architect/outbox/power_budget_v1.json`\n"
            "- `../../architect/outbox/rf_link_budget_v1.md`\n"
            "- `../../architect/outbox/interface_control_doc_v1.md`\n\n"
            "Build focus: preserve testability hooks and identify hardware placeholders versus implemented software.\n"
        ),
        foundry_dir / "outbox" / "prototype_build_record_v1.md": (
            "# prototype_build_record_v1\n\n"
            "Current implementation state:\n"
            "- Software simulator and webapp are implemented.\n"
            "- No physical hardware prototype exists in this repository.\n"
            "- Avionics, PCB, and firmware deliverables remain placeholders pending hardware scope.\n"
        ),
        foundry_dir / "outbox" / "pcb_fabrication_pack_v1.md": (
            "# pcb_fabrication_pack_v1\n\n"
            "Status: not generated.\n\n"
            "Reason: repository scope is software simulation and workspace design only.\n"
        ),
        foundry_dir / "outbox" / "bringup_firmware_v1.md": (
            "# bringup_firmware_v1\n\n"
            "Status: not generated.\n\n"
            "Reason: no embedded target or board support package is in scope.\n"
        ),
        assurance_dir / "inbox" / "foundry_handoff_v1.md": (
            "# foundry_handoff_v1\n\n"
            "Received from Foundry:\n"
            "- `../../foundry/outbox/prototype_build_record_v1.md`\n"
            "- `../../foundry/outbox/pcb_fabrication_pack_v1.md`\n"
            "- `../../foundry/outbox/bringup_firmware_v1.md`\n\n"
            "Validation focus: software-only traceability, UI interaction correctness, and model claims labeling.\n"
        ),
        assurance_dir / "outbox" / "test_validation_report_v1.md": (
            "# test_validation_report_v1\n\n"
            "Canonical source: `program_artifacts/test_validation_report_v1.md`\n\n"
            "Repository validation is software-only and simulation-backed.\n"
        ),
        assurance_dir / "outbox" / "bug_report_v1.md": (
            "# bug_report_v1\n\n"
            "Current open issues:\n"
            "- No mechanistic software defect is carried forward in the workspace export.\n"
            "- Hardware qualification remains unstarted, not failed.\n"
        ),
        assurance_dir / "outbox" / "root_cause_analysis_v1.md": (
            "# root_cause_analysis_v1\n\n"
            "No closed RCA exists because no hardware failure campaign has been executed.\n"
        ),
        vanguard_dir / "inbox" / "assurance_feedback_handoff_v1.md": (
            "# assurance_feedback_handoff_v1\n\n"
            "Received from Assurance:\n"
            "- `../../assurance/outbox/test_validation_report_v1.md`\n"
            "- `../../assurance/outbox/bug_report_v1.md`\n"
            "- `../../assurance/outbox/root_cause_analysis_v1.md`\n\n"
            "Claims discipline: only software-validated and model-predicted statements may exit Vanguard.\n"
        ),
        vanguard_dir / "outbox" / "capture_strategy_deck_v1.md": (
            "# capture_strategy_deck_v1\n\n"
            "Storyline:\n"
            "1. Mission problem and operator environment.\n"
            "2. Architecture and interface modularity.\n"
            "3. Validation-backed claims and open risks.\n"
            "4. Next-step path to hardware and field evidence.\n"
        ),
        vanguard_dir / "outbox" / "validated_claims_sheet_v1.md": (
            "# validated_claims_sheet_v1\n\n"
            "Canonical source: `program_artifacts/validated_claims_sheet_v1.md`\n"
        ),
    }

    written: List[Path] = []
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
        written.append(path)

    json_files: Dict[Path, Any] = {
        shared_dir / "handoff_manifest_v1.json": manifest,
        architect_dir / "outbox" / "architecture_spec_v1.json": architecture_spec,
        architect_dir / "outbox" / "power_budget_v1.json": power_budget,
    }
    for path, payload in json_files.items():
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        written.append(path)

    return written
