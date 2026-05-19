import pytest
from core.planner import VortexPlanner
from core.memory import VortexMemory

@pytest.fixture
def planner():
    # Use the ChromaDB integrated memory
    mem = VortexMemory()
    return VortexPlanner(mem)

def test_time_intent(planner):
    plan = planner.create_plan("what time is it right now")
    assert plan.mode == "realtime"
    assert plan.steps[0].tool == "realtime"
    assert plan.steps[0].action == "time"

def test_app_opening_intent(planner):
    plan = planner.create_plan("open google chrome")
    assert plan.mode == "system"
    assert plan.steps[0].tool == "system"
    assert plan.steps[0].action == "open_app"
    assert plan.steps[0].params["query"] == "google chrome"

def test_volume_intent(planner):
    plan = planner.create_plan("set volume to 45 percent")
    assert plan.mode == "system"
    assert plan.steps[0].action == "set_volume"
    assert plan.steps[0].params["percent"] == 45

def test_fallback_chat_intent(planner):
    plan = planner.create_plan("hey there")
    assert plan.mode == "chat"
    assert plan.steps[0].tool == "llm"
