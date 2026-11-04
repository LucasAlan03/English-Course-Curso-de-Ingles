You are writing one grammar module for a Brazilian Portuguese speaker learning English at CEFR level {{level}}.
Topic: {{title}}
Syllabus reference: {{source}}

Write:
1. theory_md: a SHORT lesson (about 120-180 words, 2-3 minutes to read) in Brazilian Portuguese with English examples.
   Use markdown: a "# " heading, "- " bullets and **bold** for the key forms. Include the rule, 3-4 example sentences,
   and one common mistake Brazilians make with this topic.
2. scenario: a realistic everyday situation where this topic comes up naturally. "title" (short), "character"
   (who the AI plays, e.g. "A friendly barista"), "goal" (what the learner should accomplish in the conversation).
3. target_structures: 2-5 short English structure names the conversation should make the learner use.

Reply with JSON only, in this shape:
{"theory_md": "...", "scenario": {"title": "...", "character": "...", "goal": "..."}, "target_structures": ["..."]}
