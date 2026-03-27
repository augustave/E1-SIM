import tempfile
import unittest
from pathlib import Path

from protctr_sim.workspace import build_workspace_manifest, write_swarm_workspace


class WorkspaceTests(unittest.TestCase):
    def test_workspace_manifest_contains_all_cells(self):
        manifest = build_workspace_manifest()
        self.assertIn("cells", manifest)
        for cell in ("vanguard", "architect", "foundry", "assurance"):
            self.assertIn(cell, manifest["cells"])

    def test_workspace_writer_emits_handoffs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_swarm_workspace(Path(tmpdir))
            names = {path.name for path in written}
            self.assertIn("handoff_manifest_v1.json", names)
            self.assertIn("vanguard_handoff_v1.md", names)
            self.assertIn("architect_handoff_v1.md", names)
            self.assertIn("foundry_handoff_v1.md", names)


if __name__ == "__main__":
    unittest.main()
