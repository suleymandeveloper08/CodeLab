from datetime import date
import math
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import AnswerForm, ContactForm, LearningPlanForm, QuestionForm, UserUpdateForm, ProfileUpdateForm, RegisterForm, LoginForm
from .models import Answer, Category, Chapter, LearningPlan, Notification, Question_post, QuizQuestion, QuizResult, UserChapterProgress, Profile
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth import login as auth_login
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape 
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape
from django.db.models import F, Sum
from datetime import date, timedelta


def custom_page_not_found_view(request, exception):
    return render(request, '404.html', status=404)

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" # API açaryňyzy bu ýere giriziň
CHAT_MODEL = 'gemini-2.5-flash-preview-05-20'
SYSTEM_PROMPT = """Sen CodeLab AI atly Türkmen dilinde programmirleme we kodlama boýunça ýöriteleşen kömekçisi. 
**Düzgünler:**
1. Diňe sorag **kodlama we programmirleme** bilen bagly bolsa jogap ber. Mysal üçin, Python, Django, JavaScript ýa-da HTML soraglaryna jogap ber.
2. Jogaplary Türkmen dilinde, sada we düşnükli et. Kod mysallaryny bereniňde, olary dogry formatla (kod bloklaryny ulanyp).
3. Eger sorag kodlama bilen bagly däl bolsa (mysal üçin, taryh, geografiýa ýa-da umumy soraglar), ýönekeý tekst bilen jogap ber: **'CodeLab AI diňe kodlama we programmirleme bilen bagly soraglar üçin işleýär. Başga tema boýunça kömek edip bilmeýärin.'**"""


# bas sahypa
def index(request):
    categories = Category.objects.all()
    if request.user.is_authenticated:
        check_daily_login_xp(request.user)
        user_plans = LearningPlan.objects.filter(user=request.user)
        plan_categories = {plan.category.slug for plan in user_plans}
        for category in categories:
            category.has_plan = category.slug in plan_categories
        unread_notifications_count = Notification.objects.filter(user=request.user, is_read=False).count()
    else:
        for category in categories:
            category.has_plan = False
        
        unread_notifications_count = 0
    return render(request, 'index.html', {'categories': categories, 'unread_notifications_count': unread_notifications_count})


#kategorinin ici
def category_detail(request, category_slug):                        #indexdaky categorylerin birine basylanda
    category = get_object_or_404(Category, slug=category_slug)
    chapters = category.chapters.all()
    chapters_with_status = []
    
    if request.user.is_authenticated:
        completed_chapter_ids = UserChapterProgress.objects.filter(
            user=request.user, 
            chapter__category=category,
            is_completed=True
        ).values_list('chapter_id', flat=True)
        
        for chapter in chapters:
            chapters_with_status.append({
                'chapter': chapter,
                'is_completed': chapter.id in completed_chapter_ids
            })
    else:
        for chapter in chapters:
            chapters_with_status.append({
                'chapter': chapter,
                'is_completed': False
            })


    return render(request, 'category_detail.html', {           #bu sol kategoriyadaky bar chapterleri ugratya
        'category': category,
        'chapters': chapters_with_status,
            })


#chapterlerin ici content
# @login_required
# def chapter_detail(request, category_slug, chapter_slug):
#     """Displays the content of a single chapter, ensuring it belongs to the category."""
#     chapter = get_object_or_404(Chapter, slug=chapter_slug)
#     category = get_object_or_404(Category, slug=category_slug)
#     learning_plan = LearningPlan.objects.filter(user=request.user, category=category).first()
#     # Check if the user has completed this chapter
#     progress = UserChapterProgress.objects.filter(user=request.user, chapter=chapter).first()
    
#     is_completed = progress.is_completed if progress else False
    
    
#     return render(request, 'chapter_detail.html', {
#         'chapter': chapter,
#         'is_completed': is_completed,
#         'category' : category,
#         'learningplan': learning_plan
#     })

#chapterlerin ici content
def chapter_detail(request, category_slug, chapter_slug):
    """Displays the content of a single chapter, ensuring it belongs to the category."""
    chapter = get_object_or_404(Chapter, slug=chapter_slug)
    category = get_object_or_404(Category, slug=category_slug)

    if request.user.is_authenticated:
        learning_plan = LearningPlan.objects.filter(user=request.user, category=category).first()
        progress = UserChapterProgress.objects.filter(user=request.user, chapter=chapter).first()
        is_completed = progress.is_completed if progress else False
    else:
        learning_plan = None
        progress = None
        is_completed = False

    return render(request, 'chapter_detail.html', {
        'chapter': chapter,
        'is_completed': is_completed,
        'category': category,
        'learningplan': learning_plan
    })



@login_required
def mark_chapter_complete(request, category_slug, chapter_slug):
    """Marks a chapter as complete or incomplete for the logged-in user."""
    category = get_object_or_404(Category, slug=category_slug)
    if request.method == 'POST':
        chapter = get_object_or_404(Chapter, slug=chapter_slug)
        
        progress, created = UserChapterProgress.objects.get_or_create(
            user=request.user,
            chapter=chapter
        )
        
        progress.is_completed = not progress.is_completed
        progress.save()

        return redirect('chapter_detail', category_slug=category_slug, chapter_slug=chapter_slug)
    
    return redirect('chapter_detail', category_slug=category_slug, chapter_slug=chapter_slug)


#atiyaclyk!!!
def learning_plan(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    chapters = category.chapters.all()
    return render(request, 'personal_course.html', {           #bu sol kategoriyadaky bar chapterleri ugratya
        'category': category,
        'chapters': chapters
            })

# Okuw meýilnamasyny döretmek we täzelemek
@login_required
def personal_course(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    chapters = Chapter.objects.filter(category=category).order_by('id')
    
    plan, created = LearningPlan.objects.get_or_create(
        user=request.user, 
        category=category,
        defaults={
            'days': 'dushenbe,sişenbe,charshenbe,penshenbe,anna,shenbe,yeksenbe',  
            'chapters_per_day': 1, 
            'daily_chapters': {}, 
        }
    )

    if request.method == 'POST':
        
        preferred_days = request.POST.getlist('days')
        try:
            chapters_per_day = int(request.POST.get('chapters_per_day', 1))
        except ValueError:
            chapters_per_day = 1

        # hepdan gunleri
        DAY_NAMES = {
            'dushenbe': 'Duşenbe', 
            'sişenbe': 'Sişenbe', 
            'charshenbe': 'Çarşenbe', 
            'penshenbe': 'Penşenbe', 
            'anna': 'Anna', 
            'shenbe': 'Şenbe', 
            'yeksenbe': 'Ýekşenbe'
        }

        preferred_days_full = [DAY_NAMES.get(d, d) for d in preferred_days]
        
        daily_chapters_structure = {}
        chapter_index = 0
        total_chapters = len(chapters)
        
        slots_per_week = len(preferred_days_full) * chapters_per_day
        
        if total_chapters == 0 or slots_per_week == 0:
            plan.days = ','.join(preferred_days)
            plan.chapters_per_day = chapters_per_day
            plan.daily_chapters = {}
            plan.save()
            return redirect('view_learning_plan', category_slug=category.slug)

        week = 1
        while chapter_index < total_chapters:
            for day_name in preferred_days_full:
                if chapter_index >= total_chapters:
                    break 
                    
                
                day_key = f"{week}. Hepde - {day_name}" 
                
                
                end_index = min(chapter_index + chapters_per_day, total_chapters)
                
                assigned_chapters_qs = chapters[chapter_index:end_index]
                
                assigned_chapters_data = [{
                    'id': c.id, 
                    'title': c.title, 
                    'slug': c.slug
                } for c in assigned_chapters_qs]
                
                if assigned_chapters_data:
                    daily_chapters_structure[day_key] = assigned_chapters_data
                
                chapter_index = end_index
            
            week += 1
        
        plan.days = ','.join(preferred_days)
        plan.chapters_per_day = chapters_per_day
        plan.daily_chapters = daily_chapters_structure 
        plan.save()
        
        return redirect('view_learning_plan', category_slug=category.slug)

    else:
        pass 

    daily_chapters_display = plan.daily_chapters if plan.daily_chapters else {}
    
    context = {
        'category': category,
        'plan': plan,
        'daily_chapters': daily_chapters_display, 
        'chapter_count': len(chapters),
        'selected_days_list': plan.days.split(',') 
    }
    return render(request, 'learning_plan.html', context)


# Okuw meýilnamasyny görmek
@login_required
def view_learning_plan(request, category_slug):
    """
    Displays the user's generated learning plan for a specific category.
    This plan may have been created manually (via personal_course) or automatically (via quiz_results).
    """
    category = get_object_or_404(Category, slug=category_slug)
    
    try:
        learning_plan = LearningPlan.objects.get(user=request.user, category=category)
    except LearningPlan.DoesNotExist:
        return redirect('personal_course', category_slug=category_slug)

    plan_chapters = learning_plan.daily_chapters

    completed_chapter_ids = UserChapterProgress.objects.filter(
        user=request.user,
        chapter__category=category,
        is_completed=True
    ).values_list('chapter_id', flat=True)

    annotated_plan_chapters = {}
    all_chapters_in_plan = [] 
    
    for day_key, chapters_list in plan_chapters.items():
        updated_chapters_list = []
        for chapter_data in chapters_list:
            chapter_id = chapter_data['id']
            is_completed = chapter_id in completed_chapter_ids
            
            chapter_data['is_completed'] = is_completed
            updated_chapters_list.append(chapter_data)
            
            all_chapters_in_plan.append(is_completed)
            
        annotated_plan_chapters[day_key] = updated_chapters_list
    
    if not all_chapters_in_plan:
        all_plan_chapters_completed = True
    else:
        all_plan_chapters_completed = all(all_chapters_in_plan)

    context = {
        'category': category,
        'learning_plan': learning_plan,
        'daily_chapters': annotated_plan_chapters, 
        'all_plan_chapters_completed': all_plan_chapters_completed, 
    }
    
    return render(request, 'view_learning_plan.html', context)

def complete_learning_plan_quiz(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    try:
        learning_plan = LearningPlan.objects.get(user=request.user, category=category)
    except LearningPlan.DoesNotExist:
        return redirect('personal_course', category_slug=category_slug)

    all_questions = QuizQuestion.objects.filter(category=category)
    
    if request.method != 'POST':
        return render(request, 'quiz_start.html', {
            'category': category, 
            'questions': all_questions, 
            'is_final_quiz': True,
            'learning_plan': learning_plan,
        })


    
    total_score = 0
    total_questions = len(all_questions)
    
    for question in all_questions:
        submitted_answer = request.POST.get(f'question_{question.id}')
        
        is_correct = (submitted_answer == question.correct_choice)
        
        if is_correct:
            total_score += 1
            
    percentage = (total_score / total_questions) * 100 if total_questions > 0 else 0

    plan_completed = False
    
    if percentage >= 70:
        learning_plan.quiz_score = percentage
        learning_plan.is_completed = True
        learning_plan.save()
        plan_completed = True
        
    context = {
        'category': category,
        'total_score': total_score,
        'total_questions': total_questions,
        'percentage': round(percentage, 2),
        'plan_completed': plan_completed,
        'learning_plan': learning_plan,
    }

    return render(request, 'final_quiz_results.html', context)

@login_required
def certificate_form_view(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    try:
        learning_plan = LearningPlan.objects.get(
            user=request.user, 
            category=category, 
            is_completed=True
        )
    except LearningPlan.DoesNotExist:
        return redirect('view_learning_plan', category_slug=category_slug)

    initial_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username

    if request.method == 'POST':
        certificate_name = request.POST.get('certificate_name')
        if certificate_name and len(certificate_name.strip()) > 3:
            request.session['certificate_name'] = certificate_name
            return redirect('generate_certificate', category_slug=category.slug)
        else:
            context = {
                'category': category,
                'error_message': 'Adyňyzy dogry giriziň.',
                'initial_name': certificate_name or initial_name,
            }
            return render(request, 'certificate_name_form.html', context)
    
    context = {
        'category': category,
        'initial_name': initial_name,
    }
    return render(request, 'certificate_name_form.html', context)


LOGO_PATH = 'media/profile_pics/1.png'
LOGO_WIDTH = 1.0 * inch  # Logo width
LOGO_HEIGHT = 1.0 * inch  # Logo height

@login_required
def generate_certificate(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    try:
        learning_plan = LearningPlan.objects.get(
            user=request.user, 
            category=category, 
            is_completed=True
        )
    except LearningPlan.DoesNotExist:
        return redirect('view_learning_plan', category_slug=category_slug)

    certificate_name = request.session.pop('certificate_name', None)
    
    if not certificate_name:
        return redirect('certificate_form_view', category_slug=category.slug)

    course_name = category.name
    score = learning_plan.quiz_score 
    date_completed = date.today().strftime('%Y/%m/%d')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificate_{category_slug}_{request.user.username}.pdf"'
    
    # LANDSCAPE ORIENTATION
    p = canvas.Canvas(response, pagesize=landscape(letter))
    
    width, height = landscape(letter) 
    
    # --- DESIGN COLORS ---
    NAVY_BLUE = HexColor("#001F3F")
    ACCENT_GOLD = HexColor("#FFBF00")
    DARK_GRAY = HexColor("#4D4D4D")
    BACKGROUND_GRAY = HexColor("#F1F1F1")

    # --- General Positioning Constants ---
    LINE_SPACING = 0.5 * inch

    # --- DRAW THE BORDER ---
    p.setStrokeColor(NAVY_BLUE)
    p.setLineWidth(5)
    p.rect(0.2*inch, 0.2*inch, width - 0.4*inch, height - 0.4*inch, stroke=1, fill=0) 

    # --- LOGO --- Dynamically position the logo
    LOGO_X_POS = (width / 2) - (LOGO_WIDTH / 2)
    LOGO_Y_POS = height - 1.3 * inch  # Just below the top edge
    
    try:
        # Check if the logo exists and draw it
        p.drawImage(
            LOGO_PATH, 
            LOGO_X_POS, 
            LOGO_Y_POS, 
            width=LOGO_WIDTH, 
            height=LOGO_HEIGHT,
            mask='auto'  
        )
        Y_POS = LOGO_Y_POS - (LOGO_HEIGHT + 0.2 * inch)
    except FileNotFoundError:
        Y_POS = height - 2 * inch 

    p.setFont("Helvetica", 20)
    p.setFillColor(NAVY_BLUE)
    p.drawCentredString(width / 2, Y_POS, "Codelab Bilim Platformasy")
    Y_POS -= LINE_SPACING * 1.2  # Spacing after platform name
    
    # --- Certificate Title (Centered, Large Text) ---
    p.setFont("Times-Bold", 42)
    p.setFillColor(NAVY_BLUE)
    p.drawCentredString(width / 2, Y_POS, "ÜSTÜNLIK SERTIFIKATY")
    Y_POS -= LINE_SPACING * 1.2

    # --- Introduction Text (Smaller Text) ---
    p.setFont("Helvetica", 18)  # Slightly larger font for better readability
    p.setFillColor(DARK_GRAY)  # Use dark gray for better contrast
    p.drawCentredString(width / 2, Y_POS, "Bu sertifikat buýsanç bilen berildi:")
    Y_POS -= LINE_SPACING * 1.5  # Adjust line spacing a bit for better visual balance

    # --- Recipient's Name (Biggest Font) ---
    p.setFont("Helvetica-Bold",50)
    LIGHT_GRAY = (0.8, 0.8, 0.8)  # Light Gray
    p.setFillColorRGB(0, 0, 0)  # Black
    p.drawCentredString(width / 2, Y_POS, certificate_name)
    Y_POS -= LINE_SPACING * 1.2  # Extra space for name

    # --- Course Completion Statement ---
    p.setFont("Helvetica", 22)
    p.setFillColor(NAVY_BLUE)
    p.drawCentredString(width / 2, Y_POS, f"**{course_name}** kursuny doly we üstünlikli tamamlandygy üçin")
    Y_POS -= LINE_SPACING * 2.8  # Space for signatures

    # --- Signature Lines (Dynamic Adjustment Based on Content) ---
    SIGN_Y = Y_POS
    LINE_LENGTH = 3.5 * inch

    p.setStrokeColor(HexColor("#808080"))  # Gray for the signature lines
    p.setLineWidth(0.5)

    # Left signature (Codelab Team)
    p.line(width / 2 - LINE_LENGTH - 0.5 * inch, SIGN_Y, width / 2 - 0.5 * inch, SIGN_Y)
    p.setFont("Helvetica", 14)
    p.drawCentredString(width / 2 - LINE_LENGTH / 2 - 0.5 * inch, SIGN_Y - 0.25 * inch, "Codelab Dolandyryjy Topary")

    # Right signature (Exam Invigilator)
    p.line(width / 2 + 0.5 * inch, SIGN_Y, width / 2 + LINE_LENGTH + 0.5 * inch, SIGN_Y)
    p.drawCentredString(width / 2 + LINE_LENGTH / 2 + 0.5 * inch, SIGN_Y - 0.25 * inch, "Synag Barlagçysy")

    # --- Additional Information (Score & Date) ---
    Y_POS = SIGN_Y - 1.5 * inch  # Adjust to create enough space

    # Debugging point: Print Y_POS to ensure it's correct
    print(f"Y_POS for score/date: {Y_POS}")

    p.setFont("Helvetica-Bold", 15)
    p.setFillColor(NAVY_BLUE)

    # Display the final exam score
    p.drawString(width / 2 - 3.5 * inch, Y_POS, f"Final Synag Skory: {score}%")

    # Display the completion date
    p.drawString(width / 2 + 1.5 * inch, Y_POS, f"Tamamlanan Senesi: {date_completed}")

    # Debugging point: Check if the strings are being written to the PDF
    print("Rendering the final score and date in PDF")

    p.showPage()  # Finish the current page
    p.save()  # Save the PDF

    return response















# def generate_certificate(request, category_slug):
#     category = get_object_or_404(Category, slug=category_slug)
    
#     try:
#         learning_plan = LearningPlan.objects.get(
#             user=request.user, 
#             category=category, 
#             is_completed=True
#         )
#     except LearningPlan.DoesNotExist:
#         return redirect('view_learning_plan', category_slug=category_slug)

#     certificate_name = request.session.pop('certificate_name', None)
    
#     if not certificate_name:
#         return redirect('certificate_form_view', category_slug=category.slug)

#     course_name = category.name
#     score = learning_plan.quiz_score 
#     date_completed = date.today().strftime('%Y/%m/%d')

#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="Certificate_{category_slug}_{request.user.username}.pdf"'
    
#     # LANDSCAPE (ALBOM) GÖRNÜŞI
#     p = canvas.Canvas(response, pagesize=landscape(letter))
    
#     width, height = landscape(letter) 
    
#     # --- DESIGN: Täze Reňk Kesgitlemeler ---
#     NAVY_BLUE = (0/255, 31/255, 63/255)       # Esasy Reňk (Goýy Gök)
#     ACCENT_GOLD = (255/255, 191/255, 0/255)   # Aksent Reňk (Altyn)
#     DARK_GRAY = (0.3, 0.3, 0.3)               # Giriş Teksti Üçin Çal
    
#     # Tekst aralyklarynyň esasy nokatlary
#     Y_POS = height - 1.5 * inch
#     LINE_SPACING = 0.5 * inch 

#     # --- Dizaýn Çägi (NAVY BLUE) ---
#     p.setStrokeColorRGB(*NAVY_BLUE)
#     p.setLineWidth(5)
#     p.rect(0.2*inch, 0.2*inch, width - 0.4*inch, height - 0.4*inch, stroke=1, fill=0) 
    
#     # --- 1. Platforma Ady (TÄZE REŇK WE ŞRIFT) ---
#     p.setFont("Helvetica", 16) 
#     p.setFillColorRGB(*NAVY_BLUE)
#     p.drawCentredString(width/2, Y_POS, "Codelab Bilim Platformasy")
#     Y_POS -= LINE_SPACING 

#     # --- 2. Esasy At (TÄZE ŞRIFT: TIMES BOLD) ---
#     Y_POS -= 0.3 * inch 
#     p.setFont("Times-Bold", 48) # Times Bold
#     p.setFillColorRGB(*NAVY_BLUE)
#     p.drawCentredString(width/2, Y_POS, "ÜSTÜNLIK SERTIFIKATY")
#     Y_POS -= LINE_SPACING * 1.5 

#     # --- 3. Giriş Teksti ---
#     p.setFont("Helvetica-Oblique", 16) 
#     p.setFillColorRGB(*DARK_GRAY) 
#     p.drawCentredString(width/2, Y_POS, "Bu sertifikat aşakdaky adama buýsanç bilen berildi:")
#     Y_POS -= LINE_SPACING * 1.5 

#     # --- 4. Alyjynyň Ady (TÄZE REŇK: ALTYN WE ŞRIFT: HELVETICA BOLD) ---
#     p.setFont("Helvetica-Bold", 65) # Helvetica Bold
#     p.setFillColorRGB(*ACCENT_GOLD) 
#     p.drawCentredString(width/2, Y_POS, certificate_name)
#     Y_POS -= LINE_SPACING * 1.8 

#     # --- 5. Kursy Tamamlamak ---
#     p.setFont("Helvetica", 22) 
#     p.setFillColorRGB(0, 0, 0) # Gara reňk
#     p.drawCentredString(width/2, Y_POS, f"**{course_name}** kursuny doly we üstünlikli tamamladygy üçin")
#     Y_POS -= LINE_SPACING * 2.8 

    
#     # --- 6. Gol Çyzyklary we Adlar ---
#     SIGN_Y = Y_POS
#     LINE_LENGTH = 3.5 * inch
    
#     p.setStrokeColorRGB(0.5, 0.5, 0.5) # Çyzyklar üçin açyk çal
#     p.setLineWidth(0.5)
    
#     # Çep Gol
#     p.line(width/2 - LINE_LENGTH - 0.5*inch, SIGN_Y, width/2 - 0.5*inch, SIGN_Y)
#     p.setFont("Helvetica", 14) 
#     p.drawCentredString(width/2 - LINE_LENGTH/2 - 0.5*inch, SIGN_Y - 0.25*inch, "Codelab Dolandyryjy Topary")
    
#     # Sag Gol
#     p.line(width/2 + 0.5*inch, SIGN_Y, width/2 + LINE_LENGTH + 0.5*inch, SIGN_Y)
#     p.drawCentredString(width/2 + LINE_LENGTH/2 + 0.5*inch, SIGN_Y - 0.25*inch, "Synag Barlagçysy")
    
    
#     # --- 7. Aşaky Maglumatlar (TÄZE REŇK) ---
#     Y_POS = SIGN_Y - 1.2 * inch 

#     p.setFont("Helvetica-Bold", 15) 
#     p.setFillColorRGB(*NAVY_BLUE) # NAVY BLUE
    
#     # Skor
#     p.drawString(width/2 - 3.5*inch, Y_POS, f"Final Synag Skory: {score}%")
    
#     # Senesi
#     p.drawString(width/2 + 1.5*inch, Y_POS, f"Tamamlanan Senesi: {date_completed}")
    
#     p.showPage()
#     p.save()

#     return response

# plany pozmak ucin algoritm
@login_required
def delete_learning_plan(request, plan_id):
    learning_plan = get_object_or_404(LearningPlan, id=plan_id, user=request.user)
    category_slug = learning_plan.category.slug
    learning_plan.delete()
    return redirect('category_detail', category_slug=category_slug)


# quiz almak ucin algoritm
@login_required
def quiz_view(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    questions = QuizQuestion.objects.filter(category=category)
    if not questions:
        return redirect('category_detail', category_slug=category_slug)
    
    return render(request, 'quiz_start.html', {'category': category, 'questions': questions})

# alnan quizin netijesi
@login_required
def quiz_results(request, category_slug):
    if request.method != 'POST':
        return redirect('quiz_view', category_slug=category_slug)

    category = get_object_or_404(Category, slug=category_slug)
    all_questions = QuizQuestion.objects.filter(category=category).select_related('chapter').order_by('chapter', 'id')
    
    chapter_results = defaultdict(lambda: {'correct_count': 0, 'questions_count': 0, 'chapter_obj': None})
    total_score = 0
    total_questions = len(all_questions)
    
    for question in all_questions:
        submitted_answer = request.POST.get(f'question_{question.id}')
        
        is_correct = (submitted_answer == question.correct_choice)
        
        chapter_id = question.chapter.id
        chapter_results[chapter_id]['questions_count'] += 1
        chapter_results[chapter_id]['chapter_obj'] = question.chapter
        
        if is_correct:
            chapter_results[chapter_id]['correct_count'] += 1
            total_score += 1
            
    chapters_to_add = []
    
    for chapter_id, data in chapter_results.items():
        if data['correct_count'] < 2:
            chapters_to_add.append(data['chapter_obj'])
            
    chapters_to_add.sort(key=lambda c: c.id)

    default_days = 'dushenbe,sişenbe,charshenbe,penshenbe,anna'
    default_chapters_per_day = 1
    
    
    daily_chapters_structure = {}
    chapter_index = 0
    total_chapters_needed = len(chapters_to_add)
    
    preferred_days = default_days.split(',')
    
    DAY_NAMES = {
        'dushenbe': 'Duşenbe', 
        'sişenbe': 'Sişenbe', 
        'charshenbe': 'Çarşenbe', 
        'penshenbe': 'Penşenbe', 
        'anna': 'Anna', 
        'shenbe': 'Şenbe', 
        'yeksenbe': 'Ýekşenbe'
    }
    preferred_days_full = [DAY_NAMES.get(d, d) for d in preferred_days]
    
    week = 1
    
    while chapter_index < total_chapters_needed:
        for day_name in preferred_days_full:
            if chapter_index >= total_chapters_needed:
                break 
                
            day_key = f"{week}. Hepde - {day_name}" 
            end_index = min(chapter_index + default_chapters_per_day, total_chapters_needed)
            
            assigned_chapters_qs = chapters_to_add[chapter_index:end_index]
            
            assigned_chapters_data = [{
                'id': c.id, 
                'title': c.title, 
                'slug': c.slug
            } for c in assigned_chapters_qs]
            
            if assigned_chapters_data:
                daily_chapters_structure[day_key] = assigned_chapters_data
            
            chapter_index = end_index
        
        week += 1


    plan, created = LearningPlan.objects.get_or_create(
        user=request.user,
        category=category,
        defaults={
            'days': default_days,
            'chapters_per_day': default_chapters_per_day,
        }
    )
    
    plan.days = default_days
    plan.chapters_per_day = default_chapters_per_day
    plan.daily_chapters = daily_chapters_structure
    plan.save()

    percentage = (total_score / total_questions) * 100 if total_questions > 0 else 0
    
    chapter_statuses = {}
    for chapter_id, data in chapter_results.items():
        chapter_statuses[chapter_id] = {
            'chapter': data['chapter_obj'],
            'correct': data['correct_count'],
            'total': data['questions_count'],
            'status': 'needs_review' if data['correct_count'] < 2 else 'mastered'
        }

    context = {
        'category': category,
        'total_score': total_score,
        'total_questions': total_questions,
        'percentage': round(percentage, 2),
        'chapters_needed': chapters_to_add, # Chapters added to the plan
        'chapter_statuses': chapter_statuses, # Detailed results for all chapters
        'plan_created': True,
    }


    return render(request, 'quiz_results.html', context) 


# habarlasmak
def contact(request):                      #habarlasmak
    return render(request, "contact.html")



def contact_view(request):              #habarlasmak - btn basylanda acylyar
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()  # Admin panel üçin maglumat bazasyna ýazýar
            return redirect('contact_success')  # Success sahypa
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})

# habar ugradyldy
def contact_success_view(request):
    return render(request, 'success.html')



# Registrasiya
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split('@')[0]

            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            login(request, user)  # awtomatik giriş edýär

            if user.is_staff or user.is_superuser:
                return redirect('/admin/')
            else:
                return redirect('index')
        else:
            error = form.errors.as_text()
            return render(request, 'register.html', {'form': form, 'error': error})
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


# giris
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')  # Eýýäm giren bolsa baş sahypa

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = LoginForm(request)
    return render(request, 'login.html', {'form': form})



# registrasia sahypa
def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')  # Eýýäm giren bolsa baş sahypa

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Registrasiýadan soň girizmäge ugrukdyr
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


# cykys ucin sahypa
def logout_view(request):
    logout(request)
    return redirect('index')

# registrasia ucin sahhpa
def register_view(request):
    error = None
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Unikal username döretmek
            username_base = email.split('@')[0] if '@' in email else email
            username = username_base
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1

            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            auth_login(request, user)

            
            if user.is_staff or user.is_superuser:
                return redirect('/admin/')
            else:
                return redirect('index')
        else:
            error = form.errors.as_text()
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form, 'error': error})

# cykys ustunlikli
@login_required
def logout_done_view(request):
    logout(request)
    return render(request, 'logout_done.html')



# XP gosulyan algoritm
def add_xp(username, amount, reason):
    if amount <= 0:
        return
        
    try:
        user = User.objects.get(username=username)
        
        user.profile.xp = F('xp') + amount
        user.profile.save()
        user.profile.refresh_from_db()
        
        # notification atmaly
        message = f"Gutlyýarys! Siz '{reason}' üçin **+{amount} XP** gazandyňyz. Täze XP ballyňyz: {user.profile.xp}."
        
        Notification.objects.create(
            user=user,
            message=message

        )
        
        print(f"XP we Bildiriş üstünlikli goşuldy: {username} -> +{amount} XP.")
        
    except User.DoesNotExist:
        print(f"Ýalňyşlyk: '{username}' atly ulanyjy tapylmady.")
    except Exception as e:
        print(f"XP goşulanda ýa-da bildiriş ýollananda ýalňyşlyk ýüze çykdy: {e}")


# daily bonusy alyan algoritm
def check_daily_login_xp(user):
    profile = user.profile
    today = date.today()
    
    # Eger ulanyjy eýýäm bugün giren bolsa, hiç zat etme
    if profile.last_login_date == today:
        return

    yesterday = today - timedelta(days=1)
    
    # Yzygiderli Giriş
    if profile.last_login_date == yesterday:
        profile.consecutive_days += 1
        profile.save(update_fields=['consecutive_days'])
        profile.refresh_from_db() 
        
    elif profile.last_login_date < yesterday:
        profile.consecutive_days = 1
        
    else:
        profile.consecutive_days = 1
        
    base_xp = 5
    bonus = profile.consecutive_days
    xp_to_add = base_xp * bonus
    
    reason_text = f"Gündelik giriş"
    add_xp(user.username, xp_to_add, reason_text)
    
    profile.last_login_date = today
    profile.save(update_fields=['last_login_date'])
    
    print(f"Gündelik Giriş XP berildi: {user.username} - +{xp_to_add} XP.")

@login_required
def daily_rewards_view(request):
    """
    Ulanyjynyň yzygiderli giriş gün sanyny we geljekki XP sowgatlaryny görkezýän sahypany taýýarlaýar.
    """
    
    profile = request.user.profile
    current_consecutive_days = profile.consecutive_days
    
    BASE_XP = 5
    
    rewards_list = []
    
    for i in range(1, 8):
        day_number = current_consecutive_days * i
        
        xp_reward = BASE_XP + (day_number - 1) 
        
        cumulative_xp = profile.xp + xp_reward 
        
        rewards_list.append({
            'day': day_number,
            'xp_amount': xp_reward,
            'is_today': i == 1 and profile.last_login_date == date.today(),
            'is_next': i == 1 and profile.last_login_date < date.today(),
            'cumulative_xp': cumulative_xp
        })
        
    context = {
        'current_xp': profile.xp,
        'consecutive_days': current_consecutive_days,
        'rewards_list': rewards_list,
    }
    
    return render(request, 'daily_login_rewards.html', context)


# userlar reytingi
@login_required
def leaderboard_view(request):
    all_profiles = Profile.objects.select_related('user').all().order_by('-xp')
    
    leaderboard = []
    
    previous_xp = -1
    rank = 0
    xp_rank_group = 0 # Deň XP-li ulanyjylar üçin

    for index, profile in enumerate(all_profiles):
        current_xp = profile.xp
        
        if current_xp != previous_xp:
            rank = index + 1
            xp_rank_group = rank
        else:
            rank = xp_rank_group
        
        leaderboard.append({
            'rank': rank,
            'username': profile.user.username,
            'xp': current_xp,
            'is_current_user': profile.user == request.user, # Häzirki ulanyjyny bellemek üçin
        })
        
        previous_xp = current_xp # XP-ni täzele
        
    context = {
        'leaderboard': leaderboard,
        'my_xp': request.user.profile.xp,
    }
    
    return render(request, 'leaderboard.html', context)


# userin profilini. gormek ucin
def profile_view(request, username):
    if request.user.username==username:
        user = get_object_or_404(User, username=username)
        learning_plans = LearningPlan.objects.filter(user=user)
        questions = Question_post.objects.filter(user=user)
        return render(request, 'profile.html', {'profile_user': user,'learning_plans': learning_plans, 'questions': questions})
    else:
        return redirect('index')




# profili onarmak
@login_required
def edit_profile(request, username):
    if request.user.username != username:
        return redirect('profile_view', username=username)  # profili onarmak

    user = get_object_or_404(User, username=username)
    profile = user.profile

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            login(request, user)
            return redirect('profile_view', username=user.username)
    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=profile)

    return render(request, 'edit_profile.html', {
        'u_form': u_form,
        'p_form': p_form
    })

# biz hakda sahypa
def about_view(request):
    return render(request, 'about.html')


# sorag-joghap bolumi, soraglar sahypasy

def question_list(request):
    """
    Displays a list of all questions.
    """
    questions = Question_post.objects.all().order_by('-created_at')
    return render(request, 'question_list.html', {'questions': questions})


# sorag-jogap ucin sorag gosmak
@login_required
def create_question(request):
    """
    Allows a logged-in user to create a new question.
    """
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            new_question = form.save(commit=False)
            new_question.user = request.user
            new_question.save()
            return redirect('question_list')
    else:
        form = QuestionForm()
    return render(request, 'create_question.html', {'form': form})

# sorag-jogap daky bir soraga basyalnda
def question_detail(request, slug):
    """
    Displays a single question and its answers.
    Also handles the submission of a new answer.
    """
    question = get_object_or_404(Question_post, slug=slug)
    answers = Answer.objects.filter(question=question).order_by('created_at')
    
    if request.method == 'POST':
        answer_form = AnswerForm(request.POST)
        if request.user.is_authenticated and answer_form.is_valid():
            new_answer = answer_form.save(commit=False)
            new_answer.user = request.user
            new_answer.question = question
            new_answer.save()

            if request.user != question.user:
                Notification.objects.create(
                    user=question.user,
                    message=f"Sizin '{question.title}' soragynyza {request.user.username} jogap yazdy.",
                    question=question
                )
            return redirect('question_detail', slug=question.slug)
    else:
        answer_form = AnswerForm()
    
    context = {
        'question': question,
        'answers': answers,
        'answer_form': answer_form
    }
    return render(request, 'question_detail.html', context)


# bildirim


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Mark all unread notifications as read when the user views the page
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    user = request.user
    
    
    return render(request, 'notifications.html', {'notifications': notifications, 'user':user})



import json
import logging
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse

from google import genai
from google.genai import types 
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = "AIzaSyBATarIWosYT26jAUdJIzHruTiqAWdFLQY"
#AIzaSyDb-51Tn0RnlAzdaye5tgJxi1uC9LMMXLQ

def get_gemini_client():
    """Gemini Client-i inizializasiýa edýän kömekçi funksiýa."""
    try:
        if not GEMINI_API_KEY or not GEMINI_API_KEY.startswith('AIza'):
             logger.error("API açary ýok ýa-da formaty nädogry.")
             return None
             
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Gemini Client inizializasiýa ýalňyşlygy: {e}")
        return None

def codelab_main_view(request):
    """
    Brauzerden gelýän GET talaplaryny dolandyrýar.
    Diňe 'codelab_ai.html' şablonyny ýükleýär.
    """
    client = get_gemini_client()
    
    if not client:
        return HttpResponse("API açary ýa-da gurşaw sazlamasy dogry däl. 'views.py'-i barlaň.", status=503)

    return render(request, 'codelab_ai.html', {})
def chat_api(request):
    """
    JavaScript-den gelýän POST talaplaryny dolandyrýar.
    Gemini API-ny çagyrýar we jogaby yzyna gaýtaryp berýär.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Diňe POST talaplaryna rugsat berilýär."}, status=405)

    client = get_gemini_client()
    if not client:
        return JsonResponse({"error": "API Client sazlanmady. Ýa-da API açary nädogry. 'views.py'-i barlaň."}, status=500)

    try:
        data = json.loads(request.body)
        query = data.get('query')
        chat_history = data.get('chat_history', [])

        if not query:
            return JsonResponse({"error": "Sorag (query) hökmany."}, status=400)
        
        formatted_history = chat_history

        config = types.GenerateContentConfig(
            system_instruction="Sen Codelab platformasy ucin AI chatbot we adyn 'Codelab AI', Codelab platformasy Turkmenistandaky yas programmistlere komek boljak mumkincilikler doredyar, bu platforma 2025-nji yylda Mary welayatynyn yoritelesdirilen welayat mekdebinin yas programmistleri tarapyndan guruldy. We eger gurujylary kim diyip soralsa (eger yorite kimler diyip soralmadyk yagdayynda aytma!), Yakup Kadyrow - dolylygyna back-end tarapyny we Suleyman Nurmuhammedow - dolylygyna front-end tarapyny islap duzdi. Seni hem (Yagny, 'Codelab AI') olar döretdiler. Sen programmirleme dilleri boýunça iň uly türkmençe bilermen. Jogaplaryňy gysga, düşnükli we dogry ber.", 
        )

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=formatted_history, 
                config=config, 
            )
        except Exception as e:
             logger.error(f"İçki API Çagyryş Ýalňyşlygy: {e}")
             return JsonResponse({"error": f"API Çagyryş Ýalňyşlygy.Internet baglanysygynyzy kontrol edin. Açaryň yzyna beren habary: {e}"}, status=500)


        ai_response_text = response.text

        return JsonResponse({
            "response": ai_response_text
        })

    except APIError as e:
        logger.error(f"Gemini API Ýalňyşlygy: {e}")
        return JsonResponse({"error": f"API Ýalňyşlygy: Açaryňyz şowsuz boldy (status kod 4xx/5xx). API açaryňyzy barlaň."}, status=500)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Nädogry JSON formaty. Bu JavaScript kodyndaky näsazlyk bolup biler."}, status=400)
    except Exception as e:
        logger.error(f"Näbelli Serwer Ýalňyşlygy: {e}")
        return JsonResponse({"error": f"Näbelli serwer näsazlygy: {e}"}, status=500)



import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def run_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            language = data.get('language', 'python')

            payload = {
                "language": language,
                "version": "*", 
                "files": [
                    {
                        "content": code
                    }
                ]
            }

            # Send code to the execution API
            response = requests.post('https://emkc.org/api/v2/piston/execute', json=payload)
            result = response.json()
            
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=400)