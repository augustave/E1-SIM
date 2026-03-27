# PROTCTR Hypersonic Waverider Program Sandbox

This project now packages the **PROTCTR** concept as a traceable aerospace
program sandbox with:

- blended-wing-body (BWB) + waverider geometry
- hypersonic lift/drag response with shock-capture factors
- approximate stagnation-point heating
- twin-tail stability proxy outside the thermal/plasma wake
- 2D point-mass flight simulation with a booster + scramjet envelope
- autonomous-aerospace-collective style program artifacts for mission,
  architecture, interfaces, validation, and claims traceability
- a generated four-cell workspace with `vanguard`, `architect`, `foundry`,
  and `assurance` handoff directories
- a tooling-readiness assessment that blocks manufacturing tooling release
  until CAD, datum, inspection, and process inputs exist

## Quick Start

```bash
python3 run_sim.py --duration 260 --dt 0.5 --csv outputs/protctr_profile.csv
python3 run_sim.py --duration 260 --dt 0.5 --plot --plot-out outputs/protctr_profile.png
python3 run_sim.py --plot-csv outputs/protctr_profile.csv --plot --show-plot
python3 export_artifacts.py
```

## Interactive Webapp

```bash
python3 run_webapp.py
# or:
python3 -m uvicorn --app-dir "/Users/taoconrad/Dev/GitHub 4/E1" webapp.main:app --reload
```

Then open the exact URL printed by `python3 run_webapp.py` for:
- interactive simulation controls
- morphing wing / flap / body controls
- mid-flight continuation from the current trajectory state
- PROTCTR blueprint regions with hover/click inspection
- live altitude / Mach / heating charts with timeline scrubber
- program mission/architecture/validation artifacts exposed through `/api/program`
- four-cell workspace manifest exposed through `/api/workspace`
- tooling readiness exposed through `/api/tooling-readiness`

The webapp now auto-generates the required artifact/workspace files on startup if they are missing.
To change geometry mid-flight: pause or stage the controls, then press `Apply Mid-Flight`.

## Program Artifacts

Generated artifacts live under `program_artifacts/` and include:
- `market_requirements_doc.md`
- `mission_conops_v1.md`
- `constraints_export_control_v1.md`
- `architecture_spec_v1.json`
- `power_budget_v1.json`
- `rf_link_budget_v1.md`
- `interface_control_doc_v1.md`
- `test_validation_report_v1.md`
- `validated_claims_sheet_v1.md`

Generated workspace files live under `workspace/` and include:
- `vanguard/inbox` and `vanguard/outbox`
- `architect/inbox` and `architect/outbox`
- `foundry/inbox` and `foundry/outbox`
- `assurance/inbox` and `assurance/outbox`
- `shared/handoff_manifest_v1.json`

Generated tooling readiness files live under `tooling_readiness/` and include:
- `tooling_readiness_assessment_v1.json`
- `tooling_blockers_v1.md`
- `tooling_input_contract_v1.md`
- `tooling_next_step_package_v1.md`

Current senior-selected first tooling target:
- `selected_target_avionics_bay_hatch/`

Current tooling blocker after that decision:
- released manufacturing CAD for the selected hatch target is still missing

## Model Scope

This is a conceptual engineering simulator for trend analysis and design
intuition, not a high-fidelity CFD/6-DOF flight cert tool.

## Tests

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall protctr_sim webapp run_sim.py run_webapp.py export_artifacts.py tests
```
