import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_SIM = REPO_ROOT / "run_sim.py"


class CliTests(unittest.TestCase):
    def test_plot_flag_auto_writes_default_csv_and_png(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cmd = [sys.executable, str(RUN_SIM), "--duration", "8", "--dt", "1", "--plot"]
            result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            csv_path = tmp / "outputs" / "protctr_profile.csv"
            png_path = tmp / "outputs" / "protctr_profile.png"
            self.assertTrue(csv_path.exists())
            self.assertTrue(png_path.exists())
            self.assertGreater(png_path.stat().st_size, 0)

    def test_plot_csv_runs_plot_only_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "input.csv"
            png_path = tmp / "outputs" / "protctr_profile.png"

            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with csv_path.open("w", newline="", encoding="utf-8") as fp:
                writer = csv.DictWriter(
                    fp,
                    fieldnames=["t_s", "altitude_m", "mach", "heat_flux_mw_m2", "tps_margin_mw_m2"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "t_s": 0.0,
                        "altitude_m": 19000.0,
                        "mach": 3.4,
                        "heat_flux_mw_m2": 0.35,
                        "tps_margin_mw_m2": 2.15,
                    }
                )
                writer.writerow(
                    {
                        "t_s": 1.0,
                        "altitude_m": 19100.0,
                        "mach": 3.5,
                        "heat_flux_mw_m2": 0.36,
                        "tps_margin_mw_m2": 2.14,
                    }
                )

            cmd = [
                sys.executable,
                str(RUN_SIM),
                "--plot-csv",
                str(csv_path),
            ]
            result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(png_path.exists())
            self.assertGreater(png_path.stat().st_size, 0)
            self.assertNotIn("Hypersonic Physics Summary", result.stdout)


if __name__ == "__main__":
    unittest.main()
