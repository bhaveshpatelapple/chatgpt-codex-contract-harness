import argparse
import hashlib
import re
from pathlib import Path

import yaml


REQUIRED_FIELDS = {
    "version": str,
    "status": str,
    "goal": str,
    "required_features": list,
    "workflow": list,
    "invariants": list,
    "out_of_scope": list,
}
LOCK_PATTERN = re.compile(r"sha256:([0-9a-f]{64})\n?\Z")


def normalized_contract_bytes(contract_path):
    text = Path(contract_path).read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def validate_contract(contract_path, lock_path):
    contract_bytes = normalized_contract_bytes(contract_path)
    contract = yaml.safe_load(contract_bytes)

    if not isinstance(contract, dict):
        raise ValueError("contract must be a YAML mapping")

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in contract:
            raise ValueError(f"missing required field: {field}")
        if not isinstance(contract[field], expected_type):
            raise ValueError(f"field {field} must be {expected_type.__name__}")

    if contract["status"] != "LOCKED":
        raise ValueError("status must be LOCKED")

    lock_text = Path(lock_path).read_text(encoding="utf-8")
    match = LOCK_PATTERN.fullmatch(lock_text)
    if match is None:
        raise ValueError("lock must contain sha256:<64 lowercase hex characters>")

    actual_digest = hashlib.sha256(contract_bytes).hexdigest()
    if actual_digest != match.group(1):
        raise ValueError("contract digest does not match lock")

    return contract


def main():
    parser = argparse.ArgumentParser(description="Validate the locked harness contract.")
    parser.add_argument("--contract", type=Path, default=Path(".harness/contract.yaml"))
    parser.add_argument("--lock", type=Path, default=Path(".harness/contract.lock"))
    args = parser.parse_args()

    try:
        contract = validate_contract(args.contract, args.lock)
    except (OSError, UnicodeError, yaml.YAMLError, ValueError) as error:
        parser.exit(1, f"contract validation failed: {error}\n")

    print(f"contract {contract['version']} is LOCKED and unchanged")


if __name__ == "__main__":
    main()
