import unittest

from fastapi.testclient import TestClient

from webapp.main import app


class WebAppApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_index_serves_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        self.assertIn("PROTCTR Aerodynamic Digital Twin", response.text)

    def test_simulate_endpoint_returns_timeline(self):
        payload = {
            "duration_s": 30.0,
            "dt_s": 1.0,
            "initial_altitude_m": 19000.0,
            "initial_mach": 3.4,
            "initial_gamma_deg": 9.0,
            "wing_morph_pct": 0.08,
            "flap_deflection_deg": 6.0,
            "body_morph_pct": 0.03,
        }
        response = self.client.post("/api/simulate", json=payload)
        self.assertEqual(response.status_code, 200, msg=response.text)

        body = response.json()
        self.assertIn("vehicle", body)
        self.assertIn("summary", body)
        self.assertIn("timeline", body)
        self.assertGreater(len(body["timeline"]), 5)
        self.assertGreater(body["summary"]["max_mach"], 0.0)
        self.assertAlmostEqual(body["timeline"][0]["wing_morph_pct"], 0.08, places=6)

    def test_program_endpoint_returns_artifact_summary(self):
        response = self.client.get("/api/program")
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assertIn("market_requirements", body)
        self.assertIn("architecture_spec", body)
        self.assertIn("artifact_urls", body)
        self.assertIn("validated_claims", body)
        self.assertGreater(len(body["validated_claims"]), 0)

    def test_workspace_endpoint_returns_cell_manifest(self):
        response = self.client.get("/api/workspace")
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assertIn("cells", body)
        self.assertIn("manifest_url", body)
        self.assertIn("vanguard", body["cells"])

    def test_tooling_readiness_endpoint_reports_blocked_state(self):
        response = self.client.get("/api/tooling-readiness")
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assertIn("tool_summary", body)
        self.assertIn("files", body)
        self.assertEqual(body["tool_summary"]["status"], "[BLOCKED: Manufacturing Target CAD Missing]")

    def test_continue_endpoint_resumes_from_given_state(self):
        initial = self.client.post(
            "/api/simulate",
            json={
                "duration_s": 12.0,
                "dt_s": 1.0,
                "initial_altitude_m": 19000.0,
                "initial_mach": 3.4,
                "initial_gamma_deg": 9.0,
            },
        ).json()
        pivot = initial["timeline"][6]
        response = self.client.post(
            "/api/continue",
            json={
                "duration_s": 10.0,
                "dt_s": 1.0,
                "state": {
                    "t_s": pivot["t_s"],
                    "altitude_m": pivot["altitude_m"],
                    "downrange_m": pivot["downrange_m"],
                    "velocity_m_s": pivot["velocity_m_s"],
                    "gamma_deg": pivot["gamma_deg"],
                },
                "wing_morph_pct": 0.1,
                "flap_deflection_deg": 8.0,
                "body_morph_pct": 0.04,
            },
        )
        self.assertEqual(response.status_code, 200, msg=response.text)
        body = response.json()
        self.assertAlmostEqual(body["timeline"][0]["t_s"], pivot["t_s"], places=6)
        self.assertAlmostEqual(body["timeline"][0]["downrange_m"], pivot["downrange_m"], places=6)
        self.assertAlmostEqual(body["timeline"][0]["flap_deflection_deg"], 8.0, places=6)


if __name__ == "__main__":
    unittest.main()
