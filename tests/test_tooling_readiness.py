import tempfile
import unittest
from pathlib import Path

from protctr_sim.tooling_readiness import build_tooling_readiness_assessment, write_tooling_readiness_package


class ToolingReadinessTests(unittest.TestCase):
    def test_current_repo_state_is_blocked_for_tooling(self):
        assessment = build_tooling_readiness_assessment()
        self.assertEqual(
            assessment["tool_summary"]["status"],
            "[BLOCKED: Manufacturing Target CAD Missing]",
        )
        self.assertEqual(len(assessment["missing_release_inputs"]), 1)

    def test_tooling_package_writer_emits_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_tooling_readiness_package(Path(tmpdir))
            names = {path.name for path in written}
            self.assertIn("tooling_readiness_assessment_v1.json", names)
            self.assertIn("tooling_blockers_v1.md", names)
            self.assertIn("tooling_input_contract_v1.md", names)
            self.assertIn("tooling_next_step_package_v1.md", names)


if __name__ == "__main__":
    unittest.main()
