# test_api.py - Comprehensive Test Suite

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class InterviewAPIClient:
    """Client wrapper for Interview Prep API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def generate_questions(
        self, 
        role: str, 
        question_type: str = "technical",
        difficulty: str = "medium",
        count: int = 5,
        topics: list = None
    ) -> list:
        """Generate interview questions"""
        url = f"{self.base_url}/api/questions/generate"
        payload = {
            "role": role,
            "question_type": question_type,
            "difficulty": difficulty,
            "count": count,
            "topics": topics
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def submit_answer(
        self,
        question_id: str,
        user_answer: str,
        time_taken: int = None
    ) -> Dict[str, Any]:
        """Submit answer and get feedback"""
        url = f"{self.base_url}/api/answers/submit"
        payload = {
            "question_id": question_id,
            "user_answer": user_answer,
            "time_taken_seconds": time_taken
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def start_mock_interview(
        self,
        role: str,
        duration_minutes: int = 30,
        question_types: list = None,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """Start a mock interview"""
        url = f"{self.base_url}/api/mock-interview/start"
        payload = {
            "role": role,
            "duration_minutes": duration_minutes,
            "question_types": question_types or ["technical", "behavioral"],
            "difficulty": difficulty
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def begin_interview(self, interview_id: str) -> Dict[str, Any]:
        """Begin the interview"""
        url = f"{self.base_url}/api/mock-interview/{interview_id}/begin"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()
    
    def submit_interview_answer(
        self,
        interview_id: str,
        question_id: str,
        user_answer: str,
        time_taken: int = None
    ) -> Dict[str, Any]:
        """Submit answer during interview"""
        url = f"{self.base_url}/api/mock-interview/{interview_id}/submit-answer"
        payload = {
            "question_id": question_id,
            "user_answer": user_answer,
            "time_taken_seconds": time_taken
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def complete_interview(self, interview_id: str) -> Dict[str, Any]:
        """Complete interview and get results"""
        url = f"{self.base_url}/api/mock-interview/{interview_id}/complete"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()
    
    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user progress"""
        url = f"{self.base_url}/api/progress/{user_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_interview_tips(self, question_type: str) -> Dict[str, Any]:
        """Get interview tips"""
        url = f"{self.base_url}/api/interview-tips/{question_type}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


# ==================== TEST SCENARIOS ====================

def test_basic_question_generation():
    """Test 1: Basic question generation"""
    print("\n=== Test 1: Generate Questions ===")
    client = InterviewAPIClient()
    
    questions = client.generate_questions(
        role="Software Engineer",
        question_type="technical",
        difficulty="medium",
        count=3,
        topics=["Python", "algorithms"]
    )
    
    print(f"Generated {len(questions)} questions")
    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i}:")
        print(f"  {q['question']}")
        print(f"  Topics: {', '.join(q['topics'])}")
        print(f"  Difficulty: {q['difficulty']}")
    
    return questions


def test_answer_submission():
    """Test 2: Answer submission with feedback"""
    print("\n=== Test 2: Submit Answer ===")
    client = InterviewAPIClient()
    
    # First generate a question
    questions = client.generate_questions(
        role="Software Engineer",
        question_type="technical",
        count=1
    )
    
    question = questions[0]
    print(f"Question: {question['question']}")
    
    # Submit an answer
    user_answer = """
    I would approach this problem by first analyzing the requirements and constraints.
    Then I'd design a solution using appropriate data structures, focusing on time
    and space complexity. I'd implement the solution iteratively, testing edge cases
    along the way, and finally optimize based on performance metrics.
    """
    
    feedback = client.submit_answer(
        question_id=question['id'],
        user_answer=user_answer,
        time_taken=180
    )
    
    print(f"\nScore: {feedback['score']}/100")
    print(f"\nStrengths:")
    for strength in feedback['strengths']:
        print(f"  • {strength}")
    
    print(f"\nAreas for Improvement:")
    for area in feedback['areas_for_improvement']:
        print(f"  • {area}")
    
    print(f"\nDetailed Feedback:\n{feedback['detailed_feedback']}")
    
    return feedback


def test_complete_mock_interview():
    """Test 3: Complete mock interview flow"""
    print("\n=== Test 3: Mock Interview Flow ===")
    client = InterviewAPIClient()
    
    # Start interview
    print("Starting mock interview...")
    interview = client.start_mock_interview(
        role="Data Scientist",
        duration_minutes=20,
        question_types=["technical", "behavioral"],
        difficulty="medium"
    )
    
    interview_id = interview['interview_id']
    print(f"Interview ID: {interview_id}")
    print(f"Total questions: {len(interview['questions'])}")
    
    # Begin interview
    client.begin_interview(interview_id)
    print("Interview started!")
    
    # Answer first 2 questions
    for i, question in enumerate(interview['questions'][:2], 1):
        print(f"\n--- Question {i} ---")
        print(question['question'])
        
        sample_answer = f"This is a sample answer for question {i}. " \
                       "I would handle this by analyzing the problem, " \
                       "designing a solution, implementing it, and testing thoroughly."
        
        feedback = client.submit_interview_answer(
            interview_id=interview_id,
            question_id=question['id'],
            user_answer=sample_answer,
            time_taken=120
        )
        
        print(f"Score: {feedback['score']}/100")
    
    # Complete interview
    print("\nCompleting interview...")
    results = client.complete_interview(interview_id)
    
    print(f"\n=== Interview Results ===")
    print(f"Overall Score: {results['overall_score']:.1f}/100")
    print(f"Questions Answered: {results['questions_answered']}/{results['total_questions']}")
    print(f"Performance Summary: {results['performance_summary']}")
    
    return results


def test_interview_tips():
    """Test 4: Get interview tips"""
    print("\n=== Test 4: Interview Tips ===")
    client = InterviewAPIClient()
    
    for q_type in ["technical", "behavioral", "hr"]:
        tips = client.get_interview_tips(q_type)
        print(f"\n{q_type.upper()} Interview Tips:")
        print(tips['tips'])


def test_different_roles_and_types():
    """Test 5: Test various roles and question types"""
    print("\n=== Test 5: Various Roles & Types ===")
    client = InterviewAPIClient()
    
    test_cases = [
        ("Frontend Developer", "technical", ["React", "JavaScript"]),
        ("Product Manager", "behavioral", ["leadership", "communication"]),
        ("DevOps Engineer", "technical", ["Docker", "Kubernetes"]),
        ("Data Analyst", "technical", ["SQL", "Python"]),
    ]
    
    for role, q_type, topics in test_cases:
        print(f"\n{role} - {q_type}")
        questions = client.generate_questions(
            role=role,
            question_type=q_type,
            count=2,
            topics=topics
        )
        print(f"  Generated {len(questions)} questions")
        if questions:
            print(f"  Sample: {questions[0]['question'][:100]}...")


# ==================== INTEGRATION EXAMPLE ====================

def example_edtech_platform_integration():
    """
    Example: How an EdTech platform would integrate this API
    """
    print("\n=== EdTech Platform Integration Example ===")
    client = InterviewAPIClient()
    
    # Step 1: User selects their preparation path
    user_role = "Full Stack Developer"
    user_level = "medium"
    
    print(f"User Profile: {user_role} (Level: {user_level})")
    
    # Step 2: Generate personalized practice questions
    print("\nGenerating personalized questions...")
    questions = client.generate_questions(
        role=user_role,
        question_type="technical",
        difficulty=user_level,
        count=5,
        topics=["React", "Node.js", "databases"]
    )
    
    # Step 3: User practices with a question
    practice_question = questions[0]
    print(f"\nPractice Question: {practice_question['question']}")
    
    # Step 4: User submits answer
    user_answer = "Sample answer demonstrating knowledge..."
    feedback = client.submit_answer(
        question_id=practice_question['id'],
        user_answer=user_answer
    )
    
    # Step 5: Show feedback and progress
    print(f"\nYour Score: {feedback['score']}/100")
    print("Keep practicing to improve!")
    
    # Step 6: Schedule mock interview
    print("\n--- Ready for Mock Interview? ---")
    mock = client.start_mock_interview(
        role=user_role,
        duration_minutes=45,
        question_types=["technical", "behavioral", "hr"]
    )
    
    print(f"Mock interview created with {len(mock['questions'])} questions")
    print("Good luck!")


# ==================== PERFORMANCE TESTS ====================

def test_api_performance():
    """Test API response times"""
    import time
    
    print("\n=== Performance Tests ===")
    client = InterviewAPIClient()
    
    # Test question generation speed
    start = time.time()
    questions = client.generate_questions(
        role="Software Engineer",
        question_type="technical",
        count=5
    )
    duration = time.time() - start
    print(f"Question generation: {duration:.2f}s for 5 questions")
    
    # Test answer evaluation speed
    if questions:
        start = time.time()
        feedback = client.submit_answer(
            question_id=questions[0]['id'],
            user_answer="Test answer"
        )
        duration = time.time() - start
        print(f"Answer evaluation: {duration:.2f}s")


# ==================== RUN ALL TESTS ====================

if __name__ == "__main__":
    print("=" * 60)
    print("Interview Preparation API - Test Suite")
    print("=" * 60)
    
    try:
        # Check API health
        response = requests.get(f"{BASE_URL}/health")
        print(f"\n✓ API is healthy: {response.json()}")
        
        # Run tests
        test_basic_question_generation()
        test_answer_submission()
        test_complete_mock_interview()
        test_interview_tips()
        test_different_roles_and_types()
        
        # Integration example
        example_edtech_platform_integration()
        
        # Performance tests
        test_api_performance()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Cannot connect to API")
        print("Make sure the API is running: python main.py")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()