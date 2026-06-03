import google.genai as genai
from google.genai import types
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = "AIzaSyAZQg-QcHao5trFlCSxvnfP_Mnc2NR0qn0"
# Atiyaclyk:
# AIzaSyBATarIWosYT26jAUdJIzHruTiqAWdFLQY
# AIzaSyDb-51Tn0RnlAzdaye5tgJxi1uC9LMMXLQ
# AIzaSyD8jWkBOuX48W8YSHELBMCmCLiUwKcpgP4
# AIzaSyAZQg-QcHao5trFlCSxvnfP_Mnc2NR0qn0

def generate_chapter_content_from_ai(category_name, chapter_title):
    """
    Generates HTML content for a programming chapter using Gemini.
    """
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        You are an expert programming instructor for the 'CodeLab' platform.
        
        Task: Write a detailed tutorial for a chapter titled "{chapter_title}" for the programming language "{category_name} in proper turkmen language".
        
        Requirements:
        1. **Format:** valid HTML. Do NOT use Markdown backticks (```html). Just return the raw HTML tags.
        2. **Structure:**
           - Start with an <h2>Introduction</h2>.
           - Explain the concept clearly with examples.
           - Include code blocks wrapped exactly like this: <pre><code class="language-{category_name.lower()}"> ... code here ... </code></pre>
           - End with a <h2>Summary</h2>.
        3. **Tone:** Ruthless but helpful mentor. Clear, concise, bulletproof.
        4. **Images:** Do not generate images, but you can use emojis where appropriate.
        """

        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3, 
            )
        )
        
        return response.text

    except Exception as e:
        logger.error(f"AI Generation failed: {e}")
        return f"<p style='color:red'>Error generating content: {str(e)}</p>"


import json
import google.genai as genai
from google.genai import types
from .models import QuizQuestion

def generate_quizzes_for_chapter(chapter_obj):
    """
    Reads chapter content and returns a list of 3 quiz question dictionaries.
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    You are an educational content creator. Based on the following programming tutorial content, 
    generate EXACTLY 3 multiple-choice questions in turkmen language.
    
    CONTENT:
    {chapter_obj.content}
    
    CATEGORY: {chapter_obj.category.name}
    CHAPTER: {chapter_obj.title}
    
    RETURN ONLY A JSON LIST with this structure:
    [
      {{
        "question_text": "The question here?",
        "choice1": "Option A",
        "choice2": "Option B",
        "choice3": "Option C",
        "choice4": "Option D",
        "correct_choice": "1" 
      }}
    ]
    Note: 'correct_choice' MUST be a string: "1", "2", "3", or "4".
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                
                response_mime_type='application/json',
                temperature=0.2
            )
        )
        
        
        questions_data = json.loads(response.text)
        return questions_data

    except Exception as e:
        print(f"Error in AI Quiz Generation: {e}")
        return []