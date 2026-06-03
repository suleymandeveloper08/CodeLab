from django.contrib import admin

from django import forms
from .models import ContactMessage, Category, Chapter, LearningPlan, QuizQuestion, QuizResult, Question_post, Answer, Profile, Notification, UserChapterProgress


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    search_fields = ('name', 'email')
    list_filter = ('created_at',)

class ChapterAdminForm(forms.ModelForm):
    """
    A custom form for the Chapter model. We add a CSS class to the
    content field so we can easily select it with JavaScript later.
    """
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'tinymce-editor'}))

    class Meta:
        model = Chapter
        fields = '__all__'

class ChapterInline(admin.StackedInline):
    model = Chapter
    extra = 1
    form = ChapterAdminForm
    fields = ('title', 'slug', 'content')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):         #categoryler
    list_display = ('name', 'slug', 'picture')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ChapterInline]

from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import ContactMessage, Category, Chapter, LearningPlan, QuizQuestion, QuizResult, Question_post, Answer, Profile, Notification, UserChapterProgress
from .utils import generate_chapter_content_from_ai, generate_quizzes_for_chapter


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'category', 'content_status')
    prepopulated_fields = {'slug': ('title',)}
    form = ChapterAdminForm
    change_form_template = 'admin/codelab_app/chapter/change_form.html'
    list_filter = ('category',)
    
    actions = ['generate_ai_content', 'bulk_generate_quizzes']

    def content_status(self, obj):
        return "✅ tayyar" if obj.content and len(obj.content) > 50 else "⚠️ tayyar dal"
    content_status.short_description = "Content"

    @admin.action(description='Emeli Aň bilen tema döretmek')
    def generate_ai_content(self, request, queryset):
        success_count = 0
        
        for chapter in queryset:
            if not chapter.category:
                self.message_user(request, f"Skipped '{chapter.title}': No category assigned.", level=messages.WARNING)
                continue

            try:
                generated_html = generate_chapter_content_from_ai(chapter.category.name, chapter.title)
                
                chapter.content = generated_html
                chapter.save()
                success_count += 1
                
            except Exception as e:
                self.message_user(request, f"Error on '{chapter.title}': {str(e)}", level=messages.ERROR)

        self.message_user(request, f"{success_count} sany chapterler ucin content doredildi!", level=messages.SUCCESS)

    def quiz_count(self, obj):
        return obj.quiz_questions.count()
    quiz_count.short_description = "Quizzes"

    @admin.action(description='Emeli aň arkaly şu temalar üçin 3 sany synag soragy döret')
    def bulk_generate_quizzes(self, request, queryset):
        total_created = 0
        
        for chapter in queryset:
            if not chapter.content or len(chapter.content) < 50:
                self.message_user(request, f"Skipped '{chapter.title}': No content to base questions on.", level=messages.WARNING)
                continue

            
            questions_list = generate_quizzes_for_chapter(chapter)
            
            for q_data in questions_list:
                try:
                    
                    QuizQuestion.objects.create(
                        category=chapter.category,
                        chapter=chapter,
                        question_text=q_data['question_text'],
                        choice1=q_data['choice1'],
                        choice2=q_data['choice2'],
                        choice3=q_data['choice3'],
                        choice4=q_data['choice4'],
                        correct_choice=q_data['correct_choice']
                    )
                    total_created += 1
                except Exception as e:
                    self.message_user(request, f"Failed to save a question for {chapter.title}: {e}", level=messages.ERROR)

        self.message_user(request, f"{total_created} sany quiz sorag doredildi!", level=messages.SUCCESS)


@admin.register(UserChapterProgress)
class UserChapterProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'chapter', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'completed_at')
    search_fields = ('user__username', 'chapter__title')
    list_editable = ('is_completed',)
    

@admin.register(LearningPlan)
class LearningPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'start_date', 'is_completed')
    list_filter = ('is_completed', 'start_date', 'category')
    search_fields = ('user__username', 'category__name')
    readonly_fields = ('start_date', 'chapters_per_day')
    fieldsets = (
        (None, {
            'fields': ('user', 'category', 'is_completed', 'current_chapter')
        }),
        ('Plan Details', {
            'fields': ('start_date', 'end_date', 'chapters_per_day')
        }),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'username', 'bio', 'profile_picture', 'last_login_date', 'consecutive_days', 'xp']
    fields = ['user', 'username', 'bio', 'profile_picture', 'last_login_date', 'consecutive_days', 'xp']



class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'category', 'chapter', 'correct_choice')
    list_filter = ('category', 'chapter')
    search_fields = ('question_text',)
    
@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'category', 'chapter']
    list_filter = ['category', 'chapter']
    search_fields = ['question_text']


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['user__username', 'category__name']





@admin.register(Question_post)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'content', 'image', 'created_at', 'slug']
    list_filter = ['title', 'user']
    search_fields = ['title']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'content', 'created_at']
    list_filter = ['question', 'content']
    search_fields = ['user', 'question']


@admin.register(Notification)
class Notification(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at', 'question']
    list_filter = ['user', 'message', 'is_read', 'created_at', 'question']
    search_fields = ['user', 'message']


