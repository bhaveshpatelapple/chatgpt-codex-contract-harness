import unittest

from fixture_app.config import DEFAULTS, merge_config


class MergeConfigTests(unittest.TestCase):
    def test_nested_override_preserves_default_siblings(self):
        merged = merge_config(DEFAULTS, {"http": {"port": 9090}})

        self.assertEqual("127.0.0.1", merged["http"]["host"])
        self.assertEqual(9090, merged["http"]["port"])
        self.assertEqual({"connect": 2, "read": 10}, merged["http"]["timeouts"])

    def test_merge_does_not_mutate_inputs(self):
        defaults = {"outer": {"kept": 1}}
        overrides = {"outer": {"added": 2}}

        merge_config(defaults, overrides)

        self.assertEqual({"outer": {"kept": 1}}, defaults)
        self.assertEqual({"outer": {"added": 2}}, overrides)


if __name__ == "__main__":
    unittest.main()
