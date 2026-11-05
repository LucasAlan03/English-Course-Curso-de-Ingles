import re
from pathlib import Path

# Variables each shipped prompt expects (checked by tests against the files).
PROMPT_VARS: dict[str, set[str]] = {
    "chat_persona": {"level", "scenario_title", "character", "goal", "target_structures"},
    "report": {"level", "module_context", "known_module_ids", "transcript"},
    "summary": {"previous_summary", "transcript"},
    "writing_prompt": {"level", "recent_topics"},
    "writing_feedback": {"level", "prompt", "known_module_ids", "text"},
    "module_content": {"level", "title", "source"},
    "song_grammar": {"modules", "chunks"},
    "translate": {"word", "sentence"},
    "teach_persona": {"level", "module_title", "target_structures"},
}


def render(name: str, prompts_dir: str, /, **variables) -> str:
    text = (Path(prompts_dir) / f"{name}.md").read_text(encoding="utf-8")
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", str(value))
    missing = re.findall(r"\{\{(\w+)\}\}", text)
    if missing:
        raise KeyError(missing[0])
    return text
