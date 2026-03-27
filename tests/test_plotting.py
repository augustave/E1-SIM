import csv
import tempfile
import unittest
from pathlib import Path

from protctr_sim.plotting import plot_profile_from_csv
from protctr_sim.simulator import SimulationConfig, simulate, write_csv
from protctr_sim.vehicle import default_vehicle


class PlottingTests(unittest.TestCase):
    def test_plot_from_simulator_csv_writes_png(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "profile.csv"
            png_path = tmp / "profile.png"

            points = simulate(default_vehicle(), SimulationConfig(duration_s=12.0, dt_s=1.0))
            write_csv(points, csv_path)

            saved = plot_profile_from_csv(csv_path, png_path=png_path, show=False)
            self.assertEqual(saved, png_path)
            self.assertTrue(png_path.exists())
            self.assertGreater(png_path.stat().st_size, 0)

    def test_plot_handles_required_schema_without_tps_margin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            csv_path = tmp / "minimal.csv"
            png_path = tmp / "minimal.png"

            with csv_path.open("w", newline="", encoding="utf-8") as fp:
                writer = csv.DictWriter(fp, fieldnames=["t_s", "altitude_m", "mach", "heat_flux_mw_m2"])
                writer.writeheader()
                writer.writerow({"t_s": 0.0, "altitude_m": 19000.0, "mach": 3.4, "heat_flux_mw_m2": 0.35})
                writer.writerow({"t_s": 1.0, "altitude_m": 19100.0, "mach": 3.5, "heat_flux_mw_m2": 0.36})

            plot_profile_from_csv(csv_path, png_path=png_path, show=False)
            self.assertTrue(png_path.exists())
            self.assertGreater(png_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
