Create {{count}} listening exercises for an English learner at CEFR level {{level}}.
Topic of the lesson: {{module_title}}. Target structures: {{target_structures}}.

Each exercise is a short realistic spoken line (or two-line exchange) that uses the target structures.
Make exactly {{choice_count}} items of kind "choice" (3 or 4 options; the answer must be one of them)
and exactly {{gap_count}} items of kind "gap" (the learner types the missing word; put ___ in the prompt).

Mistakes this learner made recently on this topic (focus on them, vary the situations):
{{recent_mistakes}}

Reply with JSON only, in this shape:
{"items": [{"kind": "choice or gap", "audio_text": "what the speaker says", "prompt": "the question shown on screen",
"options": ["only for choice items"], "answer": "...", "explanation": "one short sentence in Brazilian Portuguese"}]}
