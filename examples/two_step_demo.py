import sys
import tempfile
from pathlib import Path

from scripts.harness_state import (
    complete_step,
    load_state,
    run_verification,
    save_state,
    start_step,
)


PLAN = {
    "version": "0.1",
    "steps": [
        {"id": 1, "name": "Create a greeting"},
        {"id": 2, "name": "Expand the greeting"},
    ],
}
INITIAL_STATE = {
    "version": "0.1",
    "phase": "NEXT_STEP",
    "active_step": None,
    "completed_steps": [],
    "next_step": 1,
    "verification": None,
}
CHECK_TEXT = (
    "import pathlib,sys; expected=sys.argv[2]; "
    "actual=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'); "
    "raise SystemExit(0 if actual == expected else 1)"
)


def verification_command(artifact, expected):
    return [sys.executable, "-c", CHECK_TEXT, str(artifact), expected]


def run_demo(workspace):
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    state_path = workspace / "state.json"
    artifact = workspace / "message.txt"
    events = []

    save_state(state_path, INITIAL_STATE)
    state = start_step(PLAN, load_state(state_path), 1)
    artifact.write_text("hello\n", encoding="utf-8", newline="\n")
    state = run_verification(
        PLAN,
        state,
        1,
        verification_command(artifact, "hello\n"),
    )
    events.append("step 1 verification PASSED")
    state = complete_step(PLAN, state, 1)
    save_state(state_path, state)
    events.append("step 1 checkpointed")

    state = load_state(state_path)
    events.append("state reloaded")
    state = start_step(PLAN, state, 2)
    artifact.write_text("wrong value\n", encoding="utf-8", newline="\n")
    state = run_verification(
        PLAN,
        state,
        2,
        verification_command(artifact, "hello world\n"),
    )
    save_state(state_path, state)
    events.append("step 2 verification FAILED")
    try:
        complete_step(PLAN, state, 2)
    except ValueError:
        events.append("step 2 completion BLOCKED")
    else:
        raise AssertionError("failed verification advanced the demo")

    artifact.write_text("hello world\n", encoding="utf-8", newline="\n")
    state = run_verification(
        PLAN,
        load_state(state_path),
        2,
        verification_command(artifact, "hello world\n"),
    )
    events.append("step 2 verification PASSED")
    state = complete_step(PLAN, state, 2)
    save_state(state_path, state)
    events.append("step 2 checkpointed")
    return events, state


def main():
    with tempfile.TemporaryDirectory() as temp_dir:
        events, state = run_demo(Path(temp_dir))
    for event in events:
        print(event)
    print(f"demo complete: completed={state['completed_steps']} next={state['next_step']}")


if __name__ == "__main__":
    main()
