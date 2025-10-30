

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import openai
import os
from uuid import uuid4
import json

# Initialize FastAPI app
app = FastAPI(
    title="Interview Preparation API",
    description="Intelligent API for end-to-end interview preparation",
    version="1.0.0"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAI (set your API key)
openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")

# ==================== ENUMS ====================
class QuestionType(str, Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    HR = "hr"
    SYSTEM_DESIGN = "system_design"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class InterviewStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

# ==================== DATA MODELS ====================
class QuestionRequest(BaseModel):
    role: str = Field(..., description="Job role (e.g., 'Software Engineer', 'Data Scientist')")
    question_type: QuestionType
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    count: int = Field(5, ge=1, le=20, description="Number of questions to generate")
    topics: Optional[List[str]] = Field(None, description="Specific topics to focus on")

class Question(BaseModel):
    id: str
    question: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    topics: List[str]
    expected_answer_points: List[str]
    follow_up_questions: List[str]

class AnswerSubmission(BaseModel):
    question_id: str
    user_answer: str
    time_taken_seconds: Optional[int] = None

class AnswerFeedback(BaseModel):
    score: float = Field(..., ge=0, le=100)
    strengths: List[str]
    areas_for_improvement: List[str]
    detailed_feedback: str
    suggested_resources: List[str]
    model_answer: str

class MockInterviewRequest(BaseModel):
    role: str
    duration_minutes: int = Field(30, ge=10, le=120)
    question_types: List[QuestionType]
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

class MockInterview(BaseModel):
    interview_id: str
    role: str
    status: InterviewStatus
    questions: List[Question]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class UserProgress(BaseModel):
    user_id: str
    total_questions_attempted: int
    questions_by_type: Dict[QuestionType, int]
    average_score: float
    strengths: List[str]
    weaknesses: List[str]
    improvement_trend: List[float]

# ==================== IN-MEMORY STORAGE ====================
# In production, use a proper database (PostgreSQL, MongoDB, etc.)
interviews_db: Dict[str, Dict] = {}
user_progress_db: Dict[str, Dict] = {}
questions_db: Dict[str, Question] = {}

# ==================== HELPER FUNCTIONS ====================
async def generate_questions_with_gpt(
    role: str,
    question_type: QuestionType,
    difficulty: DifficultyLevel,
    count: int,
    topics: Optional[List[str]] = None
) -> List[Question]:
    """Generate interview questions using GPT"""
    
    topics_str = f"focusing on {', '.join(topics)}" if topics else ""
    
    prompt = f"""Generate {count} {difficulty.value} {question_type.value} interview questions for a {role} position {topics_str}.

For each question, provide:
1. The question itself
2. 3-5 key points that should be in a good answer
3. 2-3 relevant topics/skills tested
4. 2 follow-up questions

Return the response as a JSON array with this structure:
[
  {{
    "question": "...",
    "expected_answer_points": ["point1", "point2", ...],
    "topics": ["topic1", "topic2"],
    "follow_up_questions": ["followup1", "followup2"]
  }}
]"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer and career coach."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        questions_data = json.loads(response.choices[0].message.content)
        
        questions = []
        for q_data in questions_data:
            question = Question(
                id=str(uuid4()),
                question=q_data["question"],
                question_type=question_type,
                difficulty=difficulty,
                topics=q_data["topics"],
                expected_answer_points=q_data["expected_answer_points"],
                follow_up_questions=q_data["follow_up_questions"]
            )
            questions.append(question)
            questions_db[question.id] = question
        
        return questions
    
    except Exception as e:
        # Fallback to template questions if GPT fails
        return generate_fallback_questions(role, question_type, difficulty, count)

def generate_fallback_questions(role: str, question_type: QuestionType, difficulty: DifficultyLevel, count: int) -> List[Question]:
    """Fallback questions when GPT is unavailable"""
    templates = {
        QuestionType.TECHNICAL: [
            "Explain the concept of {topic} and how you've used it in your projects.",
            "How would you optimize {topic} for better performance?",
            "What are the trade-offs of using {topic}?"
        ],
        QuestionType.BEHAVIORAL: [
            "Tell me about a time when you faced a challenging deadline.",
            "Describe a situation where you had to work with a difficult team member.",
            "How do you handle failure or setbacks in your work?"
        ],
        QuestionType.HR: [
            "Why do you want to work for our company?",
            "What are your salary expectations?",
            "Where do you see yourself in 5 years?"
        ]
    }
    
    questions = []
    for i in range(min(count, 3)):
        question = Question(
            id=str(uuid4()),
            question=templates.get(question_type, ["Sample question"])[i % len(templates[question_type])],
            question_type=question_type,
            difficulty=difficulty,
            topics=["general"],
            expected_answer_points=["Provide specific examples", "Show problem-solving skills"],
            follow_up_questions=["Can you elaborate on that?", "What did you learn from this experience?"]
        )
        questions.append(question)
        questions_db[question.id] = question
    
    return questions

async def evaluate_answer_with_gpt(question: Question, user_answer: str) -> AnswerFeedback:
    """Evaluate user's answer using GPT"""
    
    prompt = f"""Evaluate this interview answer:

Question: {question.question}
Expected key points: {', '.join(question.expected_answer_points)}
User's Answer: {user_answer}

Provide a detailed evaluation with:
1. Score (0-100)
2. 2-3 specific strengths
3. 2-3 areas for improvement
4. Detailed feedback paragraph
5. 2-3 suggested learning resources
6. A model answer

Return as JSON:
{{
  "score": 85,
  "strengths": ["...", "..."],
  "areas_for_improvement": ["...", "..."],
  "detailed_feedback": "...",
  "suggested_resources": ["...", "..."],
  "model_answer": "..."
}}"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert interview evaluator providing constructive feedback."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        feedback_data = json.loads(response.choices[0].message.content)
        
        return AnswerFeedback(**feedback_data)
    
    except Exception as e:
        # Fallback evaluation
        return AnswerFeedback(
            score=75.0,
            strengths=["Attempted to answer the question", "Showed relevant knowledge"],
            areas_for_improvement=["Could provide more specific examples", "Consider elaborating on key concepts"],
            detailed_feedback="Your answer addresses the question but could be strengthened with more specific examples and deeper technical details.",
            suggested_resources=["Practice STAR method for behavioral questions", "Review technical fundamentals"],
            model_answer="A comprehensive answer would include specific examples, demonstrate deep understanding, and relate to real-world applications."
        )

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "Interview Preparation API",
        "version": "1.0.0",
        "endpoints": {
            "generate_questions": "/api/questions/generate",
            "submit_answer": "/api/answers/submit",
            "mock_interview": "/api/mock-interview",
            "user_progress": "/api/progress/{user_id}"
        }
    }

@app.post("/api/questions/generate", response_model=List[Question])
async def generate_questions(request: QuestionRequest):
    """Generate interview questions based on role and type"""
    questions = await generate_questions_with_gpt(
        role=request.role,
        question_type=request.question_type,
        difficulty=request.difficulty,
        count=request.count,
        topics=request.topics
    )
    return questions

@app.post("/api/answers/submit", response_model=AnswerFeedback)
async def submit_answer(submission: AnswerSubmission):
    """Submit an answer and get AI-powered feedback"""
    question = questions_db.get(submission.question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    feedback = await evaluate_answer_with_gpt(question, submission.user_answer)
    return feedback

@app.post("/api/mock-interview/start", response_model=MockInterview)
async def start_mock_interview(request: MockInterviewRequest):
    """Start a complete mock interview session"""
    interview_id = str(uuid4())
    
    # Generate questions for each type
    all_questions = []
    questions_per_type = max(2, 10 // len(request.question_types))
    
    for q_type in request.question_types:
        questions = await generate_questions_with_gpt(
            role=request.role,
            question_type=q_type,
            difficulty=request.difficulty,
            count=questions_per_type
        )
        all_questions.extend(questions)
    
    interview = {
        "interview_id": interview_id,
        "role": request.role,
        "status": InterviewStatus.NOT_STARTED,
        "questions": [q.dict() for q in all_questions],
        "start_time": None,
        "end_time": None,
        "answers": {}
    }
    
    interviews_db[interview_id] = interview
    
    return MockInterview(
        interview_id=interview_id,
        role=request.role,
        status=InterviewStatus.NOT_STARTED,
        questions=all_questions,
        start_time=None,
        end_time=None
    )

@app.post("/api/mock-interview/{interview_id}/begin")
async def begin_interview(interview_id: str):
    """Mark interview as started"""
    interview = interviews_db.get(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview["status"] = InterviewStatus.IN_PROGRESS
    interview["start_time"] = datetime.now().isoformat()
    
    return {"message": "Interview started", "interview_id": interview_id}

@app.post("/api/mock-interview/{interview_id}/submit-answer")
async def submit_interview_answer(interview_id: str, submission: AnswerSubmission):
    """Submit answer during mock interview"""
    interview = interviews_db.get(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    question = questions_db.get(submission.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    feedback = await evaluate_answer_with_gpt(question, submission.user_answer)
    
    interview["answers"][submission.question_id] = {
        "answer": submission.user_answer,
        "feedback": feedback.dict(),
        "time_taken": submission.time_taken_seconds
    }
    
    return feedback

@app.post("/api/mock-interview/{interview_id}/complete")
async def complete_interview(interview_id: str):
    """Complete interview and get overall performance"""
    interview = interviews_db.get(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview["status"] = InterviewStatus.COMPLETED
    interview["end_time"] = datetime.now().isoformat()
    
    # Calculate overall performance
    scores = [ans["feedback"]["score"] for ans in interview["answers"].values()]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return {
        "interview_id": interview_id,
        "status": "completed",
        "overall_score": avg_score,
        "questions_answered": len(interview["answers"]),
        "total_questions": len(interview["questions"]),
        "performance_summary": {
            "average_score": avg_score,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0
        }
    }

@app.get("/api/progress/{user_id}", response_model=UserProgress)
async def get_user_progress(user_id: str):
    """Get user's progress and analytics"""
    progress = user_progress_db.get(user_id, {
        "user_id": user_id,
        "total_questions_attempted": 0,
        "questions_by_type": {qt: 0 for qt in QuestionType},
        "average_score": 0.0,
        "strengths": [],
        "weaknesses": [],
        "improvement_trend": []
    })
    
    return UserProgress(**progress)

@app.get("/api/interview-tips/{question_type}")
async def get_interview_tips(question_type: QuestionType):
    """Get AI-generated tips for specific question types"""
    
    prompt = f"""Provide 5 expert tips for answering {question_type.value} interview questions effectively. 
    Make them actionable and specific."""
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a career coach specializing in interview preparation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        tips = response.choices[0].message.content
        
        return {"question_type": question_type, "tips": tips}
    
    except Exception as e:
        return {
            "question_type": question_type,
            "tips": "1. Practice regularly\n2. Use the STAR method\n3. Be specific with examples\n4. Stay calm and confident\n5. Ask clarifying questions"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)