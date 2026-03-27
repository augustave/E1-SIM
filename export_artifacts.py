#!/usr/bin/env python3
"""Generate autonomous-aerospace-collective program artifacts."""

from __future__ import annotations

from protctr_sim.artifacts import write_program_artifacts
from protctr_sim.tooling_readiness import write_tooling_readiness_package
from protctr_sim.workspace import write_swarm_workspace


def main() -> None:
    artifact_paths = write_program_artifacts()
    workspace_paths = write_swarm_workspace()
    tooling_paths = write_tooling_readiness_package()

    print("Generated program artifacts:")
    for path in artifact_paths:
        print(path)

    print("\nGenerated four-cell workspace files:")
    for path in workspace_paths:
        print(path)

    print("\nGenerated tooling readiness files:")
    for path in tooling_paths:
        print(path)


if __name__ == "__main__":
    main()
