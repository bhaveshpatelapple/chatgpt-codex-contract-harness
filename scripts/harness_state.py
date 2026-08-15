import copy
import json
from pathlib import Path

import yaml


STATE_FIELDS = {
    "version": str,
    "phase": str,
    "active_step": (int, type(None)),
    "completed_steps": list,
    "next_step": (int, type(None)),
}


def plan_step_ids(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get("steps"), list):
        raise ValueError("plan must contain a steps list")

    step_ids = [step.get("id") for step in plan["steps"] if isinstance(step, dict)]
    if len(step_ids) != len(plan["steps"]) or any(not isinstance(item, int) for item in step_ids):
        raise ValueError("every plan step must have an integer id")
    if step_ids != list(range(1, len(step_ids) + 1)):
        raise ValueError("plan step ids must be consecutive starting at 1")
    return step_ids


def validate_state(plan, state):
    if not isinstance(state, dict):
        raise ValueError("state must be a JSON object")
    for field, expected_type in STATE_FIELDS.items():
        if field not in state:
            raise ValueError(f"state is missing required field: {field}")
        if not isinstance(state[field], expected_type):
            raise ValueError(f"state field {field} has the wrong type")

    step_ids = plan_step_ids(plan)
    completed = state["completed_steps"]
    if completed != step_ids[: len(completed)]:
        raise ValueError("completed steps must be an ordered prefix of the plan")

    expected_next = step_ids[len(completed)] if len(completed) < len(step_ids) else None
    if state["next_step"] != expected_next:
        raise ValueError(f"next step must be {expected_next}")
    if state["active_step"] not in (None, expected_next):
        raise ValueError("active step must be empty or equal to the next step")
    return state


def start_step(plan, state, step_id):
    validate_state(plan, state)
    if state["active_step"] is not None:
        raise ValueError(f"step {state['active_step']} is already active")
    if state["next_step"] != step_id:
        raise ValueError(f"next step is {state['next_step']}")

    updated = copy.deepcopy(state)
    updated["active_step"] = step_id
    updated["phase"] = "EXECUTE_ONE_STEP"
    return updated


def complete_step(plan, state, step_id):
    validate_state(plan, state)
    if state["active_step"] != step_id:
        raise ValueError(f"step {step_id} is not active")

    step_ids = plan_step_ids(plan)
    updated = copy.deepcopy(state)
    updated["completed_steps"].append(step_id)
    updated["active_step"] = None
    updated["next_step"] = (
        step_ids[len(updated["completed_steps"])]
        if len(updated["completed_steps"]) < len(step_ids)
        else None
    )
    updated["phase"] = "CHECKPOINT"
    return updated


def load_plan(path):
    plan = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    plan_step_ids(plan)
    return plan


def save_state(path, state):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(destination)


def load_state(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
