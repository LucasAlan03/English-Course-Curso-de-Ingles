from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ListeningItem(BaseModel):
    kind: Literal["choice", "gap"]
    audio_text: str
    prompt: str
    options: list[str] | None = None
    answer: str
    explanation: str

    @model_validator(mode="after")
    def check_options(self):
        if self.kind == "choice":
            if not self.options or not 3 <= len(self.options) <= 4:
                raise ValueError("choice items need 3-4 options")
            if self.answer not in self.options:
                raise ValueError("answer must be one of the options")
        elif self.options:
            raise ValueError("gap items have no options")
        return self


# items -> (choice, gap): full lesson (5) and short review (3)
_MIX = {5: (3, 2), 3: (2, 1)}


class ListeningSet(BaseModel):
    items: list[ListeningItem]

    @model_validator(mode="after")
    def check_mix(self):
        expected = _MIX.get(len(self.items))
        if expected is None:
            raise ValueError("a listening set has 5 (lesson) or 3 (review) items")
        got = (
            sum(i.kind == "choice" for i in self.items),
            sum(i.kind == "gap" for i in self.items),
        )
        if got != expected:
            raise ValueError(f"expected {expected} choice/gap items, got {got}")
        return self


class MistakeOut(BaseModel):
    said: str
    corrected: str
    explanation: str
    module_id: str | None = None


class Report(BaseModel):
    mistakes: list[MistakeOut]
    natural_expressions: list[str]
    strengths: list[str]
    score: int = Field(ge=0, le=100)


class WritingFeedback(BaseModel):
    corrected_text: str
    improved_text: str
    mistakes: list[MistakeOut]
    score: int = Field(ge=0, le=100)
