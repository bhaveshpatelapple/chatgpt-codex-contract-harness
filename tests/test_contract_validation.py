import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "harness_verify.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("harness_verify", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALID_CONTRACT = """\
version: "0.1"
status: LOCKED
goal: Build a harness.
required_features:
  - locked contract
workflow:
  - CONTRACT_LOCK
invariants:
  - contract cannot silently change
out_of_scope:
  - web UI
"""


class ContractValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = load_validator()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.contract_path = Path(self.temp_dir.name) / "contract.yaml"
        self.lock_path = Path(self.temp_dir.name) / "contract.lock"

    def write_contract_and_lock(self, contract=VALID_CONTRACT):
        self.contract_path.write_text(contract, encoding="utf-8", newline="\n")
        digest = hashlib.sha256(contract.encode("utf-8")).hexdigest()
        self.lock_path.write_text(f"sha256:{digest}\n", encoding="utf-8")

    def test_accepts_a_valid_unchanged_locked_contract(self):
        self.write_contract_and_lock()

        result = self.validator.validate_contract(self.contract_path, self.lock_path)

        self.assertEqual(result["status"], "LOCKED")

    def test_rejects_a_contract_missing_a_required_field(self):
        contract = VALID_CONTRACT.replace("goal: Build a harness.\n", "")
        self.write_contract_and_lock(contract)

        with self.assertRaisesRegex(ValueError, "missing required field: goal"):
            self.validator.validate_contract(self.contract_path, self.lock_path)

    def test_rejects_a_contract_that_is_not_locked(self):
        contract = VALID_CONTRACT.replace("status: LOCKED", "status: DRAFT")
        self.write_contract_and_lock(contract)

        with self.assertRaisesRegex(ValueError, "status must be LOCKED"):
            self.validator.validate_contract(self.contract_path, self.lock_path)

    def test_rejects_a_silent_contract_change(self):
        self.write_contract_and_lock()
        self.contract_path.write_text(
            VALID_CONTRACT.replace("web UI", "cloud deployment"),
            encoding="utf-8",
            newline="\n",
        )

        with self.assertRaisesRegex(ValueError, "contract digest does not match lock"):
            self.validator.validate_contract(self.contract_path, self.lock_path)


if __name__ == "__main__":
    unittest.main()
