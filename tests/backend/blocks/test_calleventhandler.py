import pytest
import writer.core
from writer.blocks.calleventhandler import CallEventHandler


def valid_handler(state):
    state["animal"] = "duck"
    return 1


def invalid_handler(state):
    state["animal"] = "cat"
    return 1 / 0


class MockHandlerRegistry:
    def find_handler_callable(self, handler_name: str):
        if handler_name == "valid_handler":
            return valid_handler
        elif handler_name == "invalid_handler":
            return invalid_handler
        raise None


class MockAppProcess:
    def __init__(self):
        self.handler_registry = MockHandlerRegistry()


def test_call_event_handler(session, runner, monkeypatch):
    monkeypatch.setattr("writer.core.get_app_process", lambda: MockAppProcess())
    component = session.add_fake_component({"name": "valid_handler"})
    block = CallEventHandler(component, runner, {})
    block.run()
    assert block.outcome == "success"
    assert block.result == 1
    assert session.session_state["animal"] == "duck"


def test_invalid_json(session, runner, monkeypatch):
    monkeypatch.setattr("writer.core.get_app_process", lambda: MockAppProcess())
    component = session.add_fake_component({"name": "invalid_handler"})
    block = CallEventHandler(component, runner, {})
    with pytest.raises(BaseException):
        block.run()
    assert block.outcome == "error"
    assert session.session_state["animal"] == "cat"
