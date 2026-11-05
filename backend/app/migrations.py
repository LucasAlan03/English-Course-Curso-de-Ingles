"""Small, idempotent schema and data migrations run at startup."""

import sqlite3

# Old combined module id -> first of the new split modules.
MODULE_MIGRATION: dict[str, str] = {
    "b1_past_simple_continuous": "b1_past_simple",
    "b1_present_perfect_vs_past": "b1_present_perfect",
    "b1_futures": "b1_future_will",
    "b1_first_second_conditionals": "b1_first_conditional",
    "b1_modals_obligation_advice": "b1_modals_obligation",
    "b1_comparatives_superlatives": "b1_comparatives",
    "b1_prepositions": "b1_prepositions_time",
    "b1_gerund_infinitive": "b1_verb_ing",
    "b2_third_mixed_conditionals": "b2_third_conditional",
    "b2_passive_voice": "b2_passive_basic",
    "b2_reported_speech": "b2_reported_statements",
    "b2_modals_deduction": "b2_deduction_present",
    "b2_wish_if_only": "b2_wish_present",
    "b2_contrast_connectors": "b2_contrast",
    "c1_inversion": "c1_inversion_negative",
    "c1_cleft_sentences": "c1_it_cleft",
    "c1_past_modals": "c1_past_modals_criticism",
    "c1_collocations_idioms": "c1_collocations",
}


def ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, decl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    conn.commit()


def migrate_module_ids(conn: sqlite3.Connection) -> None:
    for old, new in MODULE_MIGRATION.items():
        old_row = conn.execute("SELECT next_due FROM reviews WHERE module_id=?", (old,)).fetchone()
        if old_row is not None:
            new_row = conn.execute("SELECT next_due FROM reviews WHERE module_id=?", (new,)).fetchone()
            if new_row is None:
                conn.execute("UPDATE reviews SET module_id=? WHERE module_id=?", (new, old))
            elif old_row["next_due"] < new_row["next_due"]:
                conn.execute("DELETE FROM reviews WHERE module_id=?", (new,))
                conn.execute("UPDATE reviews SET module_id=? WHERE module_id=?", (new, old))
            else:
                conn.execute("DELETE FROM reviews WHERE module_id=?", (old,))
        conn.execute("UPDATE sessions SET module_id=? WHERE module_id=?", (new, old))
        conn.execute("UPDATE mistakes SET module_id=? WHERE module_id=?", (new, old))
    conn.commit()
