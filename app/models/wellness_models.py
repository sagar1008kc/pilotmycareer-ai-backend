"""Mental fitness support models.

This agent is supportive and educational only. It is never a medical diagnosis or crisis
counseling. The response always includes a disclaimer and may surface crisis resources.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.models.common import ResponseMeta


class WellnessCheckinRequest(BaseModel):
    message: str | None = Field(default=None, description="Free-text check-in")
    answers: dict[str, str] | None = Field(default=None, description="Structured answers")

    @model_validator(mode="after")
    def _require_some_input(self) -> "WellnessCheckinRequest":
        if not self.message and not self.answers:
            raise ValueError("Provide either 'message' or 'answers'.")
        return self


class WellnessCheckinResponse(ResponseMeta):
    reflection: str = ""
    suggestions: list[str] = Field(default_factory=list)
    crisis_flag: bool = False
    crisis_resources: list[str] = Field(default_factory=list)
    disclaimer: str = ""
