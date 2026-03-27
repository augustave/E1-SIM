import unittest

from protctr_sim.atmosphere import isa_atmosphere


class AtmosphereTests(unittest.TestCase):
    def test_sea_level_reasonable(self):
        sl = isa_atmosphere(0.0)
        self.assertAlmostEqual(sl.temperature_k, 288.15, places=2)
        self.assertAlmostEqual(sl.pressure_pa, 101325.0, delta=600.0)
        self.assertAlmostEqual(sl.density_kg_m3, 1.225, delta=0.03)

    def test_density_decreases_with_altitude(self):
        low = isa_atmosphere(5000.0)
        high = isa_atmosphere(20000.0)
        self.assertGreater(low.density_kg_m3, high.density_kg_m3)
        self.assertGreater(low.speed_of_sound_m_s, high.speed_of_sound_m_s)


if __name__ == "__main__":
    unittest.main()
