"""Small helpers shared by the API tests."""
import json
from datetime import datetime, timezone

import yaml

from app.db import insert


def write_module(directory, module_id, level="B1", order=1, title="A topic"):
    data = {
        "id": module_id, "level": level, "title": title, "order": order,
        "theory_md": "Some theory with *examples*.", "source": "test",
        "scenario": {"title": "At a cafe", "character": "A friendly barista", "goal": "Order a coffee"},
        "target_structures": ["past simple", "past continuous"],
    }
    (directory / f"{module_id}.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")


def listening_json(count=5):
    choices, gaps = (3, 2) if count == 5 else (2, 1)
    items = []
    for i in range(choices):
        items.append({"kind": "choice", "audio_text": f"I went home {i}", "prompt": f"What happened {i}?",
                      "options": ["went", "go", "gone"], "answer": "went", "explanation": "Past simple."})
    for i in range(gaps):
        items.append({"kind": "gap", "audio_text": f"She went out {i}", "prompt": f"She ___ out {i}.",
                      "answer": "went", "explanation": "Past simple de go."})
    return json.dumps({"items": items})


def report_json(score=80, mistakes=None):
    return json.dumps({
        "mistakes": mistakes if mistakes is not None else [],
        "natural_expressions": ["How was your weekend?"], "strengths": ["Good vocabulary"], "score": score,
    })


def make_session(deps, kind="lesson", module_id="b1_past_simple_continuous", **cols):
    now = deps.clock.now().astimezone(timezone.utc).isoformat()
    return insert(deps.conn, "sessions", kind=kind, module_id=module_id, started_at=now, **cols)


def add_user_message(deps, session_id, text="I went to the park yesterday."):
    insert(deps.conn, "messages", session_id=session_id, role="user", text=text,
           created_at=datetime.now(timezone.utc).isoformat())
