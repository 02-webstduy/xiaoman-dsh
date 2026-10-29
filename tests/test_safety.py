"""安全协议：触发词、固定回应、接口。"""

from __future__ import annotations

from fastapi.testclient import TestClient

from xiaoman import safety
from xiaoman.app import app
from xiaoman.config import SafetyConfig


def test_clear_crisis_phrases_trigger() -> None:
    cfg = SafetyConfig()
    for text in [
        "我不想活了",
        "真的撑不下去了",
        "活着没意思",
        "我想自杀",
        "我打算结束自己",
        "一了百了算了",
        "我想消失",
        "不想再撑了",
    ]:
        assert safety.detect(text, cfg) is not None, text


def test_hyperbole_does_not_trigger() -> None:
    cfg = SafetyConfig()
    for text in [
        "笑死我了",
        "累死了，今天不想动",
        "我想死你了",
        "气死我了",
        "困死了",
        "这电影笑死我了",
    ]:
        assert safety.detect(text, cfg) is None, text


def test_negation_does_not_trigger() -> None:
    cfg = SafetyConfig()
    for text in ["我不想死，只是很累", "我不会自杀的", "我没想过自杀"]:
        assert safety.detect(text, cfg) is None, text


def test_mixed_hyperbole_and_intent_triggers() -> None:
    cfg = SafetyConfig()
    assert safety.detect("累死了，真的不想活了", cfg) is not None


def test_extra_phrases_are_configurable() -> None:
    cfg = SafetyConfig(extra_phrases=("不想醒来",))
    assert safety.detect("最近总是不想醒来", cfg) is not None


def test_reply_contains_safety_check_contacts_and_hotlines() -> None:
    cfg = SafetyConfig(contacts=("妈妈 13800000000",))
    reply = safety.build_reply(cfg)

    assert "安全吗" in reply
    assert "妈妈 13800000000" in reply
    assert "12356" in reply
    assert "120" in reply


def test_crisis_message_bypasses_model() -> None:
    """命中后走固定回应：不调模型，响应里必须有热线。"""
    with TestClient(app) as client:
        res = client.post("/api/chat", json={"text": "我不想活了"})
        assert res.status_code == 200
        body = res.text
        assert "12356" in body
        assert "安全吗" in body
        assert '"safety": true' in body


def test_safety_endpoint_returns_resources() -> None:
    with TestClient(app) as client:
        info = client.get("/api/safety").json()
        assert info["hotlines"]
        assert "note" in info
