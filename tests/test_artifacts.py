import tempfile
import unittest
from pathlib import Path

from protctr_sim.artifacts import build_program_summary, write_program_artifacts


class ArtifactTests(unittest.TestCase):
    def test_program_summary_contains_traceable_sections(self):
        summary = build_program_summary()
        self.assertIn("market_requirements", summary)
        self.assertIn("architecture_spec", summary)
        self.assertIn("validated_claims", summary)
        self.assertGreater(len(summary["validated_claims"]), 0)

    def test_artifact_writer_emits_expected_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            written = write_program_artifacts(Path(tmpdir))
            names = {path.name for path in written}
            self.assertIn("architecture_spec_v1.json", names)
            self.assertIn("power_budget_v1.json", names)
            self.assertIn("validated_claims_sheet_v1.md", names)


if __name__ == "__main__":
    unittest.main()
