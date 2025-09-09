import os
import openai
from pathlib import Path

# File Processing Libraries (You'll need to install these)
from PyPDF2 import PdfReader
from docx import Document
import pytesseract  # For OCR
from PIL import Image

# Set up your OpenAI API key
# Make sure you have the key stored securely, e.g., in an environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Section 1: File Processing Functions ---

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text content from various file types.
    """
    file_extension = Path(file_path).suffix.lower()
    text = ""

    if file_extension == ".pdf":
        text = _extract_text_from_pdf(file_path)
    elif file_extension == ".docx":
        text = _extract_text_from_docx(file_path)
    elif file_extension in [".jpg", ".jpeg", ".png"]:
        text = _extract_text_from_image(file_path)
    elif file_extension == ".txt":
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        # Handle unsupported file types gracefully
        raise ValueError(f"Unsupported file type: {file_extension}")

    return text

def _extract_text_from_pdf(file_path: str) -> str:
    """
    Helper function to extract text from a PDF file.
    """
    text = ""
    try:
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
    return text

def _extract_text_from_docx(file_path: str) -> str:
    """
    Helper function to extract text from a DOCX file.
    """
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
    return text

def _extract_text_from_image(file_path: str) -> str:
    """
    Helper function to extract text from an image using OCR.
    """
    try:
        # Pytesseract needs the Tesseract OCR engine to be installed
        # and its path to be configured if not in PATH.
        text = pytesseract.image_to_string(Image.open(file_path))
    except Exception as e:
        print(f"Error extracting text from image with OCR: {e}")
        text = ""
    return text

# --- Section 2: AI Interaction Functions ---

async def generate_quiz_with_ai(text_content: str) -> dict:
    """
    Generates a quiz from text content using an AI model.
    """
    prompt = f"""
    Based on the following text, create a multiple-choice quiz.
    Provide 10 questions. For each question, provide four options (A, B, C, D) and indicate the correct answer.
    Format the response as a JSON object with a list of questions, where each question has 'question_text', 'options' (a list of strings), and 'correct_answer' (the correct option, e.g., 'A').
    
    Text:
    {text_content}
    
    JSON Output:
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or a more advanced model like "gpt-4"
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates quizzes."},
                {"role": "user", "content": prompt}
            ]
        )
        # Assuming the AI returns a valid JSON string
        quiz_data_str = response.choices[0].message['content'].strip()
        quiz_data = json.loads(quiz_data_str)
        return quiz_data
    except Exception as e:
        print(f"Error calling OpenAI API for quiz generation: {e}")
        return {"error": "Failed to generate quiz."}


async def generate_summary_with_ai(text_content: str) -> str:
    """
    Generates a summary of the provided text.
    """
    prompt = f"Summarize the following text in a concise and clear manner:\n\n{text_content}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error calling OpenAI API for summarization: {e}")
        return "Failed to generate summary."


async def study_chat_with_ai(user_message: str) -> str:
    """
    Provides an AI-powered study chat response.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI study partner for university students. Keep your responses concise and focused on the topic."},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error calling OpenAI API for study chat: {e}")
        return "Sorry, I'm having trouble responding right now."


async def predict_questions_with_ai(past_questions_text: str) -> str:
    """
    Predicts likely test questions based on past questions.
    """
    prompt = f"Based on the following past exam questions, predict 5 to 10 likely questions for a future test. Explain the reasoning behind your predictions:\n\n{past_questions_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that predicts test questions for students."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error calling OpenAI API for question prediction: {e}")
        return "Failed to predict questions."