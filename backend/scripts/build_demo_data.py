"""Gera os dados da vitrine web (demo-data.json): ~12 dias de estudo fictício.

Uso:  python scripts/build_demo_data.py <saida.json> [--audio-from data/audio --audio-out <pasta>]

Roda o backend em memória com provedores falsos (sem IA, sem custo), simula os dias
de estudo pela própria API e grava as respostas dos GETs que o app usa. Também guarda
as respostas certas dos exercícios, para a vitrine corrigir no navegador.
Nada aqui toca em backend/data.
"""
import argparse
import json
import random
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.clock import FixedClock  # noqa: E402
from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.providers.base import Providers  # noqa: E402
from app.providers.fakes import FakeStt, FakeTextModel, FakeTts  # noqa: E402
from app.reviews import exercise_audio_name  # noqa: E402

TOKEN = "demo"
DAYS = 12
# Canção de domínio público (1806), para não publicar letra protegida.
SONG = {
    "title": "Twinkle, Twinkle, Little Star",
    "artist": "Jane Taylor",
    "lyrics": (
        "Twinkle, twinkle, little star,\nHow I wonder what you are!\n"
        "Up above the world so high,\nLike a diamond in the sky.\n\n"
        "When the blazing sun is gone,\nWhen he nothing shines upon,\n"
        "Then you show your little light,\nTwinkle, twinkle, all the night.\n\n"
        "Then the traveller in the dark\nThanks you for your tiny spark;\n"
        "He could not see which way to go,\nIf you did not twinkle so.\n\n"
        "In the dark blue sky you keep,\nAnd often through my curtains peep,\n"
        "For you never shut your eye,\nTill the sun is in the sky.\n\n"
        "As your bright and tiny spark\nLights the traveller in the dark,\n"
        "Though I know not what you are,\nTwinkle, twinkle, little star."
    ),
}


class MovableClock(FixedClock):
    def set(self, now: datetime) -> None:
        self._now = now


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--audio-from")
    ap.add_argument("--audio-out")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp())
    settings = Settings(api_token=TOKEN, data_dir=str(tmp), warm_up=False, _env_file=None)
    now = datetime.now(timezone.utc).replace(hour=15, minute=0, second=0, microsecond=0)
    clock = MovableClock(now - timedelta(days=DAYS), settings.tz)
    providers = Providers(chat=FakeTextModel(), report=FakeTextModel(), stt=FakeStt(), tts=FakeTts())
    app = create_app(settings, providers=providers, clock=clock)
    client = TestClient(app, headers={"X-API-Token": TOKEN})
    content = app.state.deps.content
    rng = random.Random(7)

    def ok(r):
        assert r.status_code < 400, (r.request.url, r.status_code, r.text)
        return r

    b1 = ok(client.get("/modules")).json()["levels"][0]["modules"]
    modules = [m["id"] for m in sorted(b1, key=lambda m: m["order"])]

    def complete(module_id: str, hit_rate: float) -> None:
        for e in content.exercises(module_id):
            answer = e.answers[0] if rng.random() < hit_rate else "x"
            ok(client.post(f"/exercises/{module_id}/{e.id}/answer",
                           json={"answer": answer, "seconds": rng.randint(20, 70)}))

    def do_reviews() -> None:
        for due in ok(client.get("/home")).json()["reviews_due"]:
            m = due["module_id"]
            run = ok(client.post(f"/reviews/{m}/start")).json()
            by_id = {e.id: e for e in content.exercises(m)}
            for item in run["exercises"]:
                e = by_id[item["id"]]
                answer = e.answers[0] if rng.random() < 0.9 else "x"
                ok(client.post(f"/exercises/{m}/{e.id}/answer",
                               json={"answer": answer, "seconds": rng.randint(15, 50), "run_id": run["run_id"]}))

    def practice_song() -> None:
        chunk = ok(client.get("/songs/current/today")).json()["chunk"]
        ok(client.post(f"/songs/chunks/{chunk['id']}/dictation", json={"text": chunk["text"]}))
        ok(client.post(f"/songs/chunks/{chunk['id']}/shadow",
                       files={"audio": ("a.webm", b"fake", "audio/webm")}))

    shows = ["Friends", "The Office", "Modern Family"]
    full_days = 4  # os últimos dias têm os 7 blocos: a sequência mostra 4 dias
    next_module = 0
    for d in range(DAYS):
        day = now - timedelta(days=DAYS - d)
        clock.set(day)
        full = d >= DAYS - full_days
        if not full and rng.random() < 0.25:
            continue  # um dia de folga
        date = day.date().isoformat()
        if d == DAYS - full_days:
            ok(client.post("/songs", json=SONG))
        do_reviews()
        complete(modules[next_module], rng.uniform(0.75, 0.95))
        next_module += 1
        if full:
            practice_song()
        ok(client.post("/media", json={"date": date, "type": "watch", "category": "series",
                                       "title": rng.choice(shows), "episode": f"S01E0{d % 9 + 1}",
                                       "unit_minutes": 23, "count": 2}))
        ok(client.post("/media", json={"date": date, "type": "read", "category": "book",
                                       "title": "Animal Farm", "pages": rng.randint(8, 15),
                                       "minutes": rng.randint(40, 50) if full else rng.randint(25, 40)}))
        ok(client.post("/calls/external", json={"date": date, "source": "Be Confident",
                                                "minutes": rng.randint(20, 25) if full else rng.randint(10, 15)}))
        ok(client.post("/today/anki", json={"checked": True}))

    # Hoje: gramática feita, música é o bloco atual.
    clock.set(now)
    today = now.date().isoformat()
    done = [m for m in modules if ok(client.get(f"/modules/{m}")).json()["completed"]]
    do_reviews()
    nxt = next((m for m in modules if m not in done), modules[0])
    complete(nxt, 0.9)
    ok(client.post("/media", json={"date": today, "type": "watch", "category": "video",
                                   "title": "English with Lucy: phrasal verbs", "minutes": 14}))
    for w, t in [("wonder", "perguntar-se"), ("blazing", "escaldante"), ("spark", "faísca")]:
        ok(client.post("/words", json={"word": w, "translation": t, "sentence": "", "source": "tap"}))

    # Grava as respostas dos GETs que o app usa.
    responses: dict[str, dict] = {}

    def record(path: str) -> None:
        r = client.get(path)
        responses[path] = {"status": r.status_code, "body": r.json()}

    for p in ["/home", "/modules", "/settings", "/settings/reminders", "/songs", "/songs/current/today",
              "/words", "/usage/month", f"/media?date={today}", f"/media/summary?date={today}",
              f"/calls?date={today}", "/media", "/media/summary", "/calls"]:
        record(p)
    all_modules = [m.id for m in content.all()]
    for m in all_modules:
        record(f"/modules/{m}")
        record(f"/modules/{m}/exercises")

    answers = {}
    audio_names = []
    for m in all_modules:
        for e in content.exercises(m):
            answers[f"{m}/{e.id}"] = {"answers": e.answers, "explanation": e.explanation}
            if e.audio_text and responses[f"/modules/{m}/exercises"]["status"] == 200:
                audio_names.append(exercise_audio_name(m, e.id))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"date": today, "responses": responses, "answers": answers},
                              ensure_ascii=False), encoding="utf-8")
    print(f"{len(responses)} respostas, {len(answers)} exercícios -> {out}")

    if args.audio_from and args.audio_out:
        dest = Path(args.audio_out)
        dest.mkdir(parents=True, exist_ok=True)
        copied = 0
        for name in audio_names:  # só áudios de exercícios (voz sintética), nunca de conversas
            src = Path(args.audio_from) / name
            if src.exists():
                shutil.copy(src, dest / name)
                copied += 1
        print(f"{copied}/{len(audio_names)} áudios copiados para {dest}")


if __name__ == "__main__":
    main()
