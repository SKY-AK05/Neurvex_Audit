from fastapi import APIRouter, HTTPException, Depends
from typing import List
import json
from app.core.database import get_conn
from app.models.form_builder import SectionCreate, SectionResponse, QuestionCreate, QuestionResponse

router = APIRouter()

@router.get("/sections", response_model=List[SectionResponse])
def get_all_sections():
    conn = get_conn()
    sections = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index
                FROM form_sections
                ORDER BY order_index ASC
            """)
            section_rows = cur.fetchall()
            
            for row in section_rows:
                section = {
                    "id": row[0],
                    "section_code": row[1],
                    "title": row[2],
                    "icon": row[3],
                    "summary": row[4],
                    "why_it_matters": row[5],
                    "tip": row[6],
                    "gating_question": row[7],
                    "gating_field": row[8],
                    "order_index": row[9],
                    "questions": []
                }
                
                cur.execute("""
                    SELECT id, section_id, field_name, short_title, question_text, order_index, score_mapping
                    FROM form_questions
                    WHERE section_id = %s
                    ORDER BY order_index ASC
                """, (section["id"],))
                question_rows = cur.fetchall()
                
                for q_row in question_rows:
                    section["questions"].append({
                        "id": q_row[0],
                        "section_id": q_row[1],
                        "field_name": q_row[2],
                        "short_title": q_row[3],
                        "question_text": q_row[4],
                        "order_index": q_row[5],
                        "score_mapping": q_row[6]
                    })
                sections.append(section)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    
    return sections

@router.post("/sections", response_model=SectionResponse)
def create_section(section: SectionCreate):
    conn = get_conn()
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
            return {**section.dict(), "id": section_id, "questions": []}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/sections/{section_id}", response_model=SectionResponse)
def update_section(section_id: int, section: SectionCreate):
    conn = get_conn()
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
            return {**section.dict(), "id": section_id, "questions": []} # In complete app, you'd fetch questions again
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/sections/{section_id}")
def delete_section(section_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM form_sections WHERE id=%s", (section_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Section not found")
            conn.commit()
            return {"message": "Section deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@router.post("/sections/{section_id}/questions", response_model=QuestionResponse)
def create_question(section_id: int, question: QuestionCreate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index, score_mapping)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                section_id, question.field_name, question.short_title, question.question_text, 
                question.order_index, json.dumps(question.score_mapping)
            ))
            q_id = cur.fetchone()[0]
            conn.commit()
            return {**question.dict(), "id": q_id, "section_id": section_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(question_id: int, question: QuestionCreate):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT section_id FROM form_questions WHERE id=%s", (question_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Question not found")
            section_id = row[0]
            
            cur.execute("""
                UPDATE form_questions 
                SET field_name=%s, short_title=%s, question_text=%s, order_index=%s, score_mapping=%s
                WHERE id=%s
            """, (
                question.field_name, question.short_title, question.question_text, 
                question.order_index, json.dumps(question.score_mapping), question_id
            ))
            conn.commit()
            return {**question.dict(), "id": question_id, "section_id": section_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/questions/{question_id}")
def delete_question(question_id: int):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM form_questions WHERE id=%s", (question_id,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Question not found")
            conn.commit()
            return {"message": "Question deleted"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
