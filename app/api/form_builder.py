import time
import threading
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import json
from app.core.database import get_db_connection, get_conn
from app.core.authorization import require_admin
from app.models.form_builder import SectionCreate, SectionResponse, QuestionCreate, QuestionResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory process-local cache for form sections
_cached_sections: Optional[List[dict]] = None
_cached_sections_time: float = 0.0
_SECTIONS_CACHE_TTL: float = 300.0  # 5 minutes
_cache_lock = threading.Lock()


def invalidate_form_sections_cache():
    """Invalidate process-local form sections cache on administrative mutation."""
    global _cached_sections, _cached_sections_time
    with _cache_lock:
        _cached_sections = None
        _cached_sections_time = 0.0
    logger.info("Form sections cache invalidated")
    
    # Also invalidate scoring_service cache to keep scoring in sync with admin edits
    try:
        from app.services import scoring_service
        if hasattr(scoring_service, "_cached_form_sections"):
            scoring_service._cached_form_sections = None
            scoring_service._cached_form_sections_time = 0
            logger.info("Scoring service sections cache invalidated")
    except Exception as e:
        logger.warning("Could not invalidate scoring service cache: %s", e)


def fetch_sections_from_db() -> List[dict]:
    """Execute a single query with LEFT JOIN and json_agg to retrieve all sections and questions."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    s.id,
                    s.section_code,
                    s.title,
                    s.icon,
                    s.summary,
                    s.why_it_matters,
                    s.tip,
                    s.gating_question,
                    s.gating_field,
                    s.order_index,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', q.id,
                                'section_id', q.section_id,
                                'field_name', q.field_name,
                                'short_title', q.short_title,
                                'question_text', q.question_text,
                                'order_index', q.order_index,
                                'score_mapping', q.score_mapping,
                                'depends_on_field', q.depends_on_field,
                                'depends_on_value', q.depends_on_value
                            ) ORDER BY q.order_index ASC
                        ) FILTER (WHERE q.id IS NOT NULL),
                        '[]'::json
                    ) AS questions
                FROM form_sections s
                LEFT JOIN form_questions q ON s.id = q.section_id
                GROUP BY s.id
                ORDER BY s.order_index ASC;
            """)
            rows = cur.fetchall()
            sections = []
            for r in rows:
                questions_data = r[10]
                if isinstance(questions_data, str):
                    try:
                        questions_data = json.loads(questions_data)
                    except Exception:
                        questions_data = []
                sections.append({
                    "id": r[0],
                    "section_code": r[1],
                    "title": r[2],
                    "icon": r[3],
                    "summary": r[4],
                    "why_it_matters": r[5],
                    "tip": r[6],
                    "gating_question": r[7],
                    "gating_field": r[8],
                    "order_index": r[9],
                    "questions": questions_data
                })
            return sections
    finally:
        conn.close()


@router.get("/sections", response_model=List[SectionResponse])
def get_all_sections():
    global _cached_sections, _cached_sections_time
    now = time.time()
    
    # Fast path: cache hit without lock or database checkout
    if _cached_sections is not None and (now - _cached_sections_time) < _SECTIONS_CACHE_TTL:
        return _cached_sections
    
    # Cache miss or expired: use lock to prevent thundering herd
    with _cache_lock:
        # Double-check inside lock
        now = time.time()
        if _cached_sections is not None and (now - _cached_sections_time) < _SECTIONS_CACHE_TTL:
            return _cached_sections
        
        try:
            fresh_sections = fetch_sections_from_db()
            _cached_sections = fresh_sections
            _cached_sections_time = now
            return _cached_sections
        except Exception as e:
            logger.error("Failed to fetch form sections from DB: %s", e)
            # Stale-while-revalidate: if DB fails, return previous cache if available
            if _cached_sections is not None:
                logger.warning("Serving stale form sections from cache following DB error")
                return _cached_sections
            raise HTTPException(status_code=500, detail="Failed to load form sections")


@router.post("/sections", response_model=SectionResponse)
def create_section(section: SectionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    section.section_code, section.title, section.icon, section.summary, 
                    section.why_it_matters, section.tip, section.gating_question, section.gating_field, section.order_index
                ))
                section_id = cur.fetchone()[0]
                conn.commit()
                invalidate_form_sections_cache()
                return {**section.dict(), "id": section_id, "questions": []}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.put("/sections/{section_id}", response_model=SectionResponse)
def update_section(section_id: int, section: SectionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE form_sections 
                    SET section_code=%s, title=%s, icon=%s, summary=%s, why_it_matters=%s, tip=%s, gating_question=%s, gating_field=%s, order_index=%s
                    WHERE id=%s
                """, (
                    section.section_code, section.title, section.icon, section.summary, 
                    section.why_it_matters, section.tip, section.gating_question, section.gating_field, section.order_index, section_id
                ))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Section not found")
                conn.commit()
                invalidate_form_sections_cache()
                return {**section.dict(), "id": section_id, "questions": []}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sections/{section_id}")
def delete_section(section_id: int, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM form_sections WHERE id=%s", (section_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Section not found")
                conn.commit()
                invalidate_form_sections_cache()
                return {"message": "Section deleted"}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/sections/{section_id}/questions", response_model=QuestionResponse)
def create_question(section_id: int, question: QuestionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index, score_mapping, depends_on_field, depends_on_value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    section_id, question.field_name, question.short_title, question.question_text, 
                    question.order_index, json.dumps(question.score_mapping), question.depends_on_field, question.depends_on_value
                ))
                q_id = cur.fetchone()[0]
                conn.commit()
                invalidate_form_sections_cache()
                return {**question.dict(), "id": q_id, "section_id": section_id}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(question_id: int, question: QuestionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT section_id FROM form_questions WHERE id=%s", (question_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Question not found")
                section_id = row[0]
                
                cur.execute("""
                    UPDATE form_questions 
                    SET field_name=%s, short_title=%s, question_text=%s, order_index=%s, score_mapping=%s, depends_on_field=%s, depends_on_value=%s
                    WHERE id=%s
                """, (
                    question.field_name, question.short_title, question.question_text, 
                    question.order_index, json.dumps(question.score_mapping), question.depends_on_field, question.depends_on_value, question_id
                ))
                conn.commit()
                invalidate_form_sections_cache()
                return {**question.dict(), "id": question_id, "section_id": section_id}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/questions/{question_id}")
def delete_question(question_id: int, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM form_questions WHERE id=%s", (question_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Question not found")
                conn.commit()
                invalidate_form_sections_cache()
                return {"message": "Question deleted"}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
