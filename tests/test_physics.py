import unittest

from protctr_sim.atmosphere import isa_atmosphere
from protctr_sim.physics import ControlState, aerodynamic_model
from protctr_sim.vehicle import default_vehicle


class PhysicsTests(unittest.TestCase):
    def test_hypersonic_engagement_increases_lift(self):
        vehicle = default_vehicle()
        atmo = isa_atmosphere(26000.0)
        low_m = aerodynamic_model(vehicle, atmo, velocity_m_s=1200.0, alpha_deg=4.5)
        high_m = aerodynamic_model(vehicle, atmo, velocity_m_s=2200.0, alpha_deg=4.5)
        self.assertGreater(high_m.cl, low_m.cl)

    def test_heating_scales_with_velocity(self):
        vehicle = default_vehicle()
        atmo = isa_atmosphere(30000.0)
        slow = aerodynamic_model(vehicle, atmo, velocity_m_s=1000.0, alpha_deg=3.0)
        fast = aerodynamic_model(vehicle, atmo, velocity_m_s=2000.0, alpha_deg=3.0)
        self.assertGreater(fast.heat_flux_mw_m2, slow.heat_flux_mw_m2 * 6.5)

    def test_drag_positive(self):
        vehicle = default_vehicle()
        atmo = isa_atmosphere(18000.0)
        res = aerodynamic_model(vehicle, atmo, velocity_m_s=1400.0, alpha_deg=6.0)
        self.assertGreater(res.cd, 0.0)
        self.assertGreater(res.ld_ratio, 0.0)

    def test_flap_deflection_changes_lift_and_drag(self):
        vehicle = default_vehicle()
        atmo = isa_atmosphere(22000.0)
        baseline = aerodynamic_model(vehicle, atmo, velocity_m_s=1600.0, alpha_deg=4.0)
        flapped = aerodynamic_model(
            vehicle,
            atmo,
            velocity_m_s=1600.0,
            alpha_deg=4.0,
            controls=ControlState(flap_deflection_deg=12.0),
        )
        self.assertGreater(flapped.cl, baseline.cl)
        self.assertGreater(flapped.cd, baseline.cd)


if __name__ == "__main__":
    unittest.main()
