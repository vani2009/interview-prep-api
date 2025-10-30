# database_models.py - SQLAlchemy Database Models

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

# ==================== ENUMS ====================

class QuestionType(enum.Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    HR = "hr"
    SYSTEM_DESIGN = "system_design"

class DifficultyLevel(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class InterviewStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SubscriptionTier(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# ==================== MODELS ====================

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    subscription_tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    progress = relationship("UserProgress", back_populates="user", uselist=False)
    interviews = relationship("Interview", back_populates="user")
    answers = relationship("Answer", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    total_questions_attempted = Column(Integer, default=0)
    total_time_spent_minutes = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    questions_by_type = Column(JSON, default={})  # {"technical": 50, "behavioral": 30}
    strengths = Column(JSON, default=[])  # ["algorithms", "system design"]
    weaknesses = Column(JSON, default=[])  # ["communication", "time management"]
    improvement_trend = Column(JSON, default=[])  # [65, 70, 75, 78, 82]
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="progress")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(SQLEnum(QuestionType), nullable=False)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False)
    role = Column(String, nullable=False)  # "Software Engineer", "Data Scientist"
    topics = Column(JSON, nullable=False)  # ["Python", "algorithms"]
    expected_answer_points = Column(JSON, nullable=False)
    follow_up_questions = Column(JSON, default=[])
    model_answer = Column(Text)
    usage_count = Column(Integer, default=0)
    average_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)  # "system" or "custom"
    is_active = Column(Boolean, default=True)
    
    # Relationships
    answers = relationship("Answer", back_populates="question")
    interview_questions = relationship("InterviewQuestion", back_populates="question")


class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    role = Column(String, nullable=False)
    status = Column(SQLEnum(InterviewStatus), default=InterviewStatus.NOT_STARTED)
    duration_minutes = Column(Integer)
    difficulty = Column(SQLEnum(DifficultyLevel))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    overall_score = Column(Float)
    performance_summary = Column(JSON)  # Detailed stats
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="interviews")
    interview_questions = relationship("InterviewQuestion", back_populates="interview")


class InterviewQuestion(Base):
    """Junction table for interviews and questions"""
    __tablename__ = "interview_questions"
    
    id = Column(Integer, primary_key=True)
    interview_id = Column(String, ForeignKey("interviews.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    order = Column(Integer)  # Question order in interview
    
    # Relationships
    interview = relationship("Interview", back_populates="interview_questions")
    question = relationship("Question", back_populates="interview_questions")
    answer = relationship("Answer", back_populates="interview_question", uselist=False)


class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    interview_question_id = Column(Integer, ForeignKey("interview_questions.id"))
    answer_text = Column(Text, nullable=False)
    score = Column(Float)
    time_taken_seconds = Column(Integer)
    strengths = Column(JSON, default=[])
    areas_for_improvement = Column(JSON, default=[])
    detailed_feedback = Column(Text)
    suggested_resources = Column(JSON, default=[])
    submitted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    interview_question = relationship("InterviewQuestion", back_populates="answer")


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    key_hash = Column(String, unique=True, nullable=False)
    name = Column(String)  # "Production API", "Development"
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # Requests per hour
    requests_used = Column(Integer, default=0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class QuestionBank(Base):
    """Pre-generated questions for faster responses"""
    __tablename__ = "question_bank"
    
    id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False, index=True)
    question_type = Column(SQLEnum(QuestionType), nullable=False, index=True)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False, index=True)
    topic = Column(String, index=True)
    question_data = Column(JSON, nullable=False)  # Complete question object
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)


class Analytics(Base):
    """API usage and performance analytics"""
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    endpoint = Column(String, nullable=False)
    response_time_ms = Column(Integer)
    status_code = Column(Integer)
    error_message = Column(Text)
    metadata = Column(JSON)  # Additional tracking data
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# ==================== DATABASE SETUP ====================

def init_database(database_url: str = "postgresql://user:password@localhost/interview_prep"):
    """Initialize database with all tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get database session"""
    Session = sessionmaker(bind=engine)
    return Session()


# ==================== ADVANCED FEATURES ====================

"""
FEATURE 1: SMART QUESTION CACHING
- Pre-generate common questions
- Store in question_bank table
- Serve instantly without GPT call
- Regenerate periodically

FEATURE 2: ADAPTIVE DIFFICULTY
- Track user performance
- Automatically adjust question difficulty
- Start easy, increase as user improves

FEATURE 3: SPACED REPETITION
- Track questions answered
- Re-surface weak areas
- Optimize learning retention

FEATURE 4: PEER COMPARISON
- Anonymous performance benchmarks
- "You scored better than 75% of users"
- Role-specific leaderboards

FEATURE 5: INTERVIEW SIMULATION MODES
- Timed mode: Strict time limits
- Practice mode: Unlimited time
- Expert mode: Follow-up questions required
- Group interview: Multiple candidates

FEATURE 6: VIDEO/AUDIO SUPPORT
- Record video answers
- AI analyzes body language (future)
- Speech-to-text for verbal answers
- Pronunciation feedback

FEATURE 7: COMPANY-SPECIFIC PREP
- Google interview style
- Amazon leadership principles
- Meta/Facebook focus areas
- Startup culture fit

FEATURE 8: COLLABORATIVE FEATURES
- Pair programming interviews
- Team interview simulations
- Mentor feedback system
- Study group creation

FEATURE 9: GAMIFICATION
- Points and badges
- Streak tracking
- Daily challenges
- Achievement system

FEATURE 10: INTEGRATION APIS
- Slack notifications
- Calendar integration
- LinkedIn profile import
- Resume parser for custom questions
"""

# ==================== EXAMPLE QUERIES ====================

def example_advanced_queries():
    """Example database queries for advanced features"""
    
    # Query 1: Get user's weak areas
    weak_areas_query = """
    SELECT topic, AVG(a.score) as avg_score
    FROM answers a
    JOIN questions q ON a.question_id = q.id
    CROSS JOIN LATERAL unnest(q.topics) as topic
    WHERE a.user_id = :user_id
    GROUP BY topic
    HAVING AVG(a.score) < 70
    ORDER BY avg_score ASC
    LIMIT 5;
    """
    
    # Query 2: Get recommended practice questions
    recommended_questions_query = """
    SELECT q.*
    FROM questions q
    WHERE q.role = :user_role
    AND q.difficulty = :difficulty
    AND q.id NOT IN (
        SELECT question_id 
        FROM answers 
        WHERE user_id = :user_id
        AND submitted_at > NOW() - INTERVAL '7 days'
    )
    AND EXISTS (
        SELECT 1 FROM unnest(q.topics) as topic
        WHERE topic IN :weak_topics
    )
    ORDER BY q.usage_count ASC, RANDOM()
    LIMIT 10;
    """
    
    # Query 3: Calculate improvement trend
    improvement_trend_query = """
    WITH weekly_scores AS (
        SELECT 
            DATE_TRUNC('week', submitted_at) as week,
            AVG(score) as avg_score
        FROM answers
        WHERE user_id = :user_id
        GROUP BY week
        ORDER BY week
    )
    SELECT week, avg_score,
           LAG(avg_score) OVER (ORDER BY week) as previous_week,
           avg_score - LAG(avg_score) OVER (ORDER BY week) as improvement
    FROM weekly_scores;
    """
    
    # Query 4: Peer comparison
    peer_comparison_query = """
    WITH user_avg AS (
        SELECT AVG(score) as user_score
        FROM answers
        WHERE user_id = :user_id
    ),
    all_users AS (
        SELECT user_id, AVG(score) as avg_score
        FROM answers
        GROUP BY user_id
    )
    SELECT 
        (SELECT user_score FROM user_avg) as your_score,
        AVG(avg_score) as average_score,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_score) as median_score,
        COUNT(CASE WHEN avg_score < (SELECT user_score FROM user_avg) THEN 1 END) * 100.0 / COUNT(*) as better_than_percentage
    FROM all_users;
    """
    
    return {
        "weak_areas": weak_areas_query,
        "recommended": recommended_questions_query,
        "improvement": improvement_trend_query,
        "peer_comparison": peer_comparison_query
    }


# ==================== MIGRATION SCRIPT ====================

migration_script = """
-- Migration: Add new features to existing database

-- Add video answer support
ALTER TABLE answers ADD COLUMN video_url TEXT;
ALTER TABLE answers ADD COLUMN audio_url TEXT;
ALTER TABLE answers ADD COLUMN transcription TEXT;

-- Add streak tracking
ALTER TABLE user_progress ADD COLUMN current_streak INTEGER DEFAULT 0;
ALTER TABLE user_progress ADD COLUMN longest_streak INTEGER DEFAULT 0;
ALTER TABLE user_progress ADD COLUMN last_activity_date DATE;

-- Add company-specific preparation
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    interview_style JSON,
    focus_areas JSON,
    difficulty_preference VARCHAR(50)
);

CREATE TABLE user_target_companies (
    user_id VARCHAR REFERENCES users(id),
    company_id INTEGER REFERENCES companies(id),
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, company_id)
);

-- Add gamification
CREATE TABLE achievements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url TEXT,
    points INTEGER,
    criteria JSON
);

CREATE TABLE user_achievements (
    user_id VARCHAR REFERENCES users(id),
    achievement_id INTEGER REFERENCES achievements(id),
    earned_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, achievement_id)
);

-- Add indexes for performance
CREATE INDEX idx_answers_user_date ON answers(user_id, submitted_at);
CREATE INDEX idx_questions_role_type ON questions(role, question_type, difficulty);
CREATE INDEX idx_interviews_user_status ON interviews(user_id, status);
"""

print("Database schema and advanced features documented.")
print("See migration_script variable for SQL migrations.")