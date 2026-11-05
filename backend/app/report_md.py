"""A finished conversation as a Markdown file the learner can download and share."""

import json
from datetime import datetime

from app.deps import AppDeps
from app.errors import AppError
from app.sessions_repo import get_session

KIND_TITLES = {"lesson": "Ligação", "review": "Revisão", "free": "Conversa livre", "teach": "Ensine a IA"}


def report_markdown(deps: AppDeps, session_id: int) -> str:
    session = get_session(deps.conn, session_id)
    if not session["report_json"] or session["is_finished"] != 1:
        raise AppError("not_finished", 409, "Esta conversa ainda não tem relatório.")
    data = json.loads(session["report_json"])
    report = data["report"]
    subject = session["topic"] or ""
    if session["module_id"]:
        try:
            subject = deps.content.get(session["module_id"]).title
        except KeyError:
            subject = session["module_id"]
    day = session["day"] or datetime.fromisoformat(session["started_at"]).astimezone(deps.clock.tz).date().isoformat()
    lines = [f"# {KIND_TITLES.get(session['kind'], session['kind'])}: {subject}".rstrip(": "), "",
             f"- Data: {day}", f"- Nota: {data.get('final_score', report.get('score'))}", "", "## Conversa", ""]
    for m in deps.conn.execute("SELECT role, text FROM messages WHERE session_id = ? ORDER BY id", (session_id,)):
        who = "Você" if m["role"] == "user" else "IA"
        lines += [f"**{who}:** {m['text']}", ""]
    lines += ["## Erros", ""]
    lines += [f"- {x['said']} → {x['corrected']} — {x['explanation']}" for x in report["mistakes"]] or ["- Nenhum"]
    lines += ["", "## Expressões naturais", ""] + [f"- {x}" for x in report["natural_expressions"]]
    lines += ["", "## Pontos fortes", ""] + [f"- {x}" for x in report["strengths"]]
    return "\n".join(lines) + "\n"
