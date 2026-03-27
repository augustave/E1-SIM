import unittest

from protctr_sim.physics import ControlState
from protctr_sim.simulator import FlightState, SimulationConfig, simulate
from protctr_sim.vehicle import default_vehicle


class SimulatorTests(unittest.TestCase):
    def test_simulation_returns_progressive_timeline(self):
        vehicle = default_vehicle()
        config = SimulationConfig(duration_s=40.0, dt_s=1.0)
        points = simulate(vehicle, config)
        self.assertGreater(len(points), 20)
        self.assertAlmostEqual(points[0].t_s, 0.0, places=6)
        self.assertGreater(points[-1].t_s, points[0].t_s)

    def test_state_values_remain_physical(self):
        vehicle = default_vehicle()
        config = SimulationConfig(duration_s=60.0, dt_s=1.0)
        points = simulate(vehicle, config)
        for p in points:
            self.assertGreaterEqual(p.altitude_m, 0.0)
            self.assertGreater(p.velocity_m_s, 0.0)
            self.assertGreater(p.mach, 0.0)
            self.assertGreaterEqual(p.q_dyn_kpa, 0.0)

    def test_control_values_propagate_into_timeline(self):
        vehicle = default_vehicle()
        config = SimulationConfig(
            duration_s=8.0,
            dt_s=1.0,
            controls=ControlState(wing_morph_pct=0.12, flap_deflection_deg=8.0, body_morph_pct=0.05),
        )
        points = simulate(vehicle, config)
        self.assertTrue(all(abs(p.wing_morph_pct - 0.12) < 1e-6 for p in points))
        self.assertTrue(all(abs(p.flap_deflection_deg - 8.0) < 1e-6 for p in points))
        self.assertTrue(all(abs(p.body_morph_pct - 0.05) < 1e-6 for p in points))

    def test_simulation_can_continue_from_midflight_state(self):
        vehicle = default_vehicle()
        first_leg = simulate(vehicle, SimulationConfig(duration_s=12.0, dt_s=1.0))
        pivot = first_leg[-1]
        continuation = simulate(
            vehicle,
            SimulationConfig(
                duration_s=8.0,
                dt_s=1.0,
                controls=ControlState(wing_morph_pct=0.10, flap_deflection_deg=10.0),
            ),
            initial_state=FlightState(
                t_s=pivot.t_s,
                altitude_m=pivot.altitude_m,
                downrange_m=pivot.downrange_m,
                velocity_m_s=pivot.velocity_m_s,
                gamma_deg=pivot.gamma_deg,
            ),
        )
        self.assertAlmostEqual(continuation[0].t_s, pivot.t_s, places=6)
        self.assertAlmostEqual(continuation[0].altitude_m, pivot.altitude_m, places=6)
        self.assertGreater(continuation[-1].t_s, continuation[0].t_s)
        self.assertAlmostEqual(continuation[0].flap_deflection_deg, 10.0, places=6)


if __name__ == "__main__":
    unittest.main()
