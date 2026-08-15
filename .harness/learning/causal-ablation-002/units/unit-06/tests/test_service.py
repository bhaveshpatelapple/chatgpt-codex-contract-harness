import unittest

from fixture_app.service import service_settings


class ServiceSettingsTests(unittest.TestCase):
    def test_port_override_retains_required_http_defaults(self):
        self.assertEqual(
            {
                "bind": "127.0.0.1:9090",
                "read_timeout": 10,
                "log_level": "INFO",
            },
            service_settings({"http": {"port": 9090}}),
        )


if __name__ == "__main__":
    unittest.main()
