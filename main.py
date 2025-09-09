import json
from .utils import extract_text_from_file, generate_quiz_with_ai
import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import our database models and the dependency
from .models import User, Course, File as DBFile, Quiz, Question, Answer, QuizHistory, get_db, create_tables

# We'll use this library to process files later
# import your_file_processing_library_here

# Initialize the FastAPI app
app = FastAPI()

# Create the database tables on startup
# This is a good practice to ensure the database is ready
@app.on_event("startup")
def on_startup():
    create_tables()

# Pydantic models for request/response bodies
class QuizGenerationRequest(BaseModel):
    file_id: int

class QuizSubmissionRequest(BaseModel):
    quiz_id: int
    user_answers: dict[int, int]  # Maps question_id to answer_id

class StudyChatRequest(BaseModel):
    user_message: str

# --- API Endpoints ---

@app.post("/upload_file/")
async def upload_file(file: UploadFile = File(...), course_name: str = "Uncategorized", db: Session = Depends(get_db)):
    """
    Accepts a file upload and starts a background task to process it.
    """
    # Create a unique filename and file path
    file_location = f"uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    # Save file and course info to the database
    course = db.query(Course).filter_by(course_name=course_name).first()
    if not course:
        course = Course(course_name=course_name)
        db.add(course)
        db.commit()
        db.refresh(course)

    db_file = DBFile(filename=file.filename, filepath=file_location, course_id=course.id)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return {"message": f"File '{file.filename}' uploaded successfully. Processing will begin shortly."}

@app.post("/generate_quiz/")
async def generate_quiz(request: QuizGenerationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_file = db.query(DBFile).filter_by(id=request.file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    background_tasks.add_task(_process_file_and_generate_quiz, db_file.filepath, db_file.id, db)

    return {"message": "Quiz generation started in the background."}

@app.get("/get_quiz/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    """
    Fetches a specific quiz from the database.
    """
    quiz = db.query(Quiz).filter_by(id=quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = []
    for q in quiz.questions:
        answers = [{"id": a.id, "answer_text": a.answer_text} for a in q.answers]
        questions.append({"id": q.id, "question_text": q.question_text, "answers": answers})
    
    return {"quiz_id": quiz.id, "questions": questions}

@app.post("/submit_quiz/")
def submit_quiz(request: QuizSubmissionRequest, db: Session = Depends(get_db)):
    """
    Submits user's answers, calculates the score, and saves the history.
    """
    quiz = db.query(Quiz).filter_by(id=request.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    correct_answers = {q.id: next((a.id for a in q.answers if a.is_correct), None) for q in quiz.questions}
    
    score = 0
    results = {}
    for question_id, user_answer_id in request.user_answers.items():
        is_correct = (user_answer_id == correct_answers.get(question_id))
        if is_correct:
            score += 1
        results[question_id] = {"is_correct": is_correct}

    # Save quiz history (assuming a user is logged in, here we'll use a placeholder user)
    # user = get_current_user_from_token(request) # You would implement this later
    # quiz_history = QuizHistory(user_id=user.id, quiz_id=quiz.id, score=score)
    # db.add(quiz_history)
    # db.commit()

    return {"score": score, "total_questions": len(quiz.questions), "results": results}

@app.get("/quiz_history/{user_id}")
def get_quiz_history(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieves a user's past quiz history and scores.
    """
    history = db.query(QuizHistory).filter_by(user_id=user_id).all()
    if not history:
        raise HTTPException(status_code=404, detail="No quiz history found for this user.")

    history_list = []
    for item in history:
        history_list.append({
            "quiz_id": item.quiz_id,
            "score": item.score,
            "date_completed": item.date_completed
        })
    
    return {"user_id": user_id, "quiz_history": history_list}

@app.post("/study_chat/")
async def study_chat(request: StudyChatRequest):
    """
    Handles interactions with the AI study chat.
    """
    # This function will use an AI library to get a response
    # For now, it's a placeholder
    ai_response = f"This is a placeholder for your AI's response to: {request.user_message}"
    return {"response": ai_response}

@app.post("/predict_questions/")
async def predict_questions(file: UploadFile = File(...)):
    """
    Predicts likely test questions from a file of past questions.
    """
    # This function will process the file content and use AI to predict questions.
    # For now, it's a placeholder
    return {"message": f"Prediction for '{file.filename}' started. Results will be available soon."}

# Placeholder function for background task
async def _process_file_and_generate_quiz(file_path: str, file_id: int, db: Session):
    try:
        # 1. Extract text from the file
        text_content = extract_text_from_file(file_path)
        if not text_content:
            print("Could not extract text from file.")
            return

        # 2. Generate quiz using the AI
        quiz_data = await generate_quiz_with_ai(text_content)

        if "error" in quiz_data:
            print(f"AI failed to generate quiz: {quiz_data['error']}")
            return

        # 3. Save the generated quiz to the database
        new_quiz = Quiz(file_id=file_id)
        db.add(new_quiz)
        db.commit()
        db.refresh(new_quiz)

        for q_data in quiz_data['questions']:
            new_question = Question(question_text=q_data['question_text'], quiz_id=new_quiz.id)
            db.add(new_question)
            db.commit()
            db.refresh(new_question)

            # Assume options are 'A', 'B', 'C', 'D'
            correct_option_text = q_data['options'][ord(q_data['correct_answer'].upper()) - ord('A')]

            for option_text in q_data['options']:
                is_correct = (option_text == correct_option_text)
                new_answer = Answer(answer_text=option_text, is_correct=is_correct, question_id=new_question.id)
                db.add(new_answer)

            db.commit()

        print(f"Quiz generation for file {file_id} complete!")

    except Exception as e:
        print(f"An error occurred during quiz generation: {e}")
        db.rollback()