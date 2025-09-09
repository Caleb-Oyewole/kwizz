from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# Define the base for our declarative models
Base = declarative_base()

# --- Database Models ---

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

    # Relationships
    files = relationship("File", back_populates="user")
    quiz_history = relationship("QuizHistory", back_populates="user")

class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String)
    
    # Relationships
    files = relationship("File", back_populates="course")

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id'))
    course_id = Column(Integer, ForeignKey('courses.id'))
    
    # Relationships
    user = relationship("User", back_populates="files")
    course = relationship("Course", back_populates="files")
    quizzes = relationship("Quiz", back_populates="file")
    
class Quiz(Base):
    __tablename__ = 'quizzes'
    id = Column(Integer, primary_key=True, index=True)
    date_generated = Column(DateTime, default=datetime.utcnow)

    # Foreign Key
    file_id = Column(Integer, ForeignKey('files.id'))

    # Relationships
    file = relationship("File", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz")
    quiz_history = relationship("QuizHistory", back_populates="quiz")

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text)

    # Foreign Key
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True, index=True)
    answer_text = Column(Text)
    is_correct = Column(Boolean, default=False)

    # Foreign Key
    question_id = Column(Integer, ForeignKey('questions.id'))

    # Relationships
    question = relationship("Question", back_populates="answers")

class QuizHistory(Base):
    __tablename__ = 'quiz_history'
    id = Column(Integer, primary_key=True, index=True)
    score = Column(Integer)
    date_completed = Column(DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id'))
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    
    # Relationships
    user = relationship("User", back_populates="quiz_history")
    quiz = relationship("Quiz", back_populates="quiz_history")
    
# --- Database Setup ---
DATABASE_URL = "sqlite:///./quiz_app.db"  # Use SQLite for development
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Place this at the end of your models.py file 
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()