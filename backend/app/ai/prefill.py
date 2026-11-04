import time

from app.ai.listening import ensure_lesson_bank, load_bank
from app.deps import AppDeps
from app.errors import ProviderRateLimited, ProviderUnavailable


def prefill_lesson_bank(
    deps: AppDeps,
    module_ids: list[str],
    sleep=time.sleep,
    wait_s: float = 30,
    max_waits: int = 20,
    log=print,
) -> dict[str, list[str]]:
    """Make the lesson exercises of every module that lacks them, patiently.

    When the AI provider says "too many requests" or "overloaded", wait and try again; after `max_waits`
    waits in a row the remaining modules are reported as failed (run it again later to continue).
    """
    result: dict[str, list[str]] = {"done": [], "skipped": [], "failed": []}
    waits = 0
    for index, module_id in enumerate(module_ids):
        if load_bank(deps.conn, module_id) is not None:
            result["skipped"].append(module_id)
            continue
        while True:
            try:
                ensure_lesson_bank(deps, module_id)
                result["done"].append(module_id)
                waits = 0
                log(f"[{index + 1}/{len(module_ids)}] {module_id}: ok")
                break
            except (ProviderRateLimited, ProviderUnavailable) as exc:
                if waits >= max_waits:
                    log(f"[{index + 1}/{len(module_ids)}] {module_id}: giving up ({exc.code})")
                    result["failed"].extend(m for m in module_ids[index:] if load_bank(deps.conn, m) is None)
                    return result
                waits += 1
                log(f"[{index + 1}/{len(module_ids)}] {module_id}: {exc.code}, waiting {wait_s:.0f}s ({waits}/{max_waits})")
                sleep(wait_s)
    return result
