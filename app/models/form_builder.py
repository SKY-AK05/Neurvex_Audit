from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class QuestionBase(BaseModel):
    field_name: str
    short_title: str
    question_text: str
    order_index: int = 0
    score_mapping: Dict[str, int] = Field(
        default_factory=lambda: {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0, "N/A": 0}
    )

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    section_id: int

class SectionBase(BaseModel):
    section_code: str
    title: str
    icon: Optional[str] = None
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    tip: Optional[str] = None
    gating_question: Optional[str] = None
    gating_field: Optional[str] = None
    order_index: int = 0

class SectionCreate(SectionBase):
    pass

class SectionResponse(SectionBase):
    id: int
    questions: List[QuestionResponse] = []
