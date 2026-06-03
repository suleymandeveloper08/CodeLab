from django.db import models
from django.forms import JSONField
from django.utils.text import slugify
import uuid
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date



# Create your models here.
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email}"
    

class Category(models.Model):                   #category: python, java, sql, ...
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=500, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    picture = models.ImageField(upload_to='category_pics/',null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Chapter(models.Model):                        #categorinin icindaki chapterler, bolumler meselem: category:python; chapter:giris
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class UserChapterProgress(models.Model):
    """A model to track a user's completion of a chapter."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chapter_progress')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='user_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures that a user can only have one progress entry per chapter
        unique_together = ('user', 'chapter')
        verbose_name_plural = "User Chapter Progress"

    def __str__(self):
        return f"{self.user.username} - {self.chapter.title}"

class LearningPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_plans')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    chapters_per_day = models.JSONField() # Stores a dictionary of {'day_of_week': [chapter_ids]}
    current_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    quiz_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    days = models.CharField(max_length=100, default='')
    daily_chapters = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username}'s plan for {self.category.name}"

    # A custom property to check if the plan has started
    @property
    def has_started(self):
        return self.current_chapter is not None


from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):               #taze user goshulsa auto ozi profile object yasaya username zadam alya
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username =  models.SlugField(unique=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True, default='profile_pics/default.png')
    bio = models.TextField(max_length=500, blank=True)
    xp = models.IntegerField(default=0)
    last_login_date = models.DateField(default=date(2000, 1, 1))
    consecutive_days = models.IntegerField(default=0) 

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = slugify(self.user)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.user.username}'s profile"
    

class QuizQuestion(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='quiz_questions')
    chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, blank=True, related_name='quiz_questions')
    question_text = models.TextField()
    choice1 = models.CharField(max_length=255)
    choice2 = models.CharField(max_length=255)
    choice3 = models.CharField(max_length=255)
    choice4 = models.CharField(max_length=255)
    correct_choice = models.CharField(max_length=1, choices=[('1', 'Choice 1'), ('2', 'Choice 2'), ('3', 'Choice 3'), ('4', 'Choice 4')])

    def __str__(self):
        return f"Quiz for {self.category.name}: {self.question_text[:50]}..."

class QuizResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    incorrect_chapters = models.ManyToManyField(Chapter, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quiz Result for {self.user.username} in {self.category.name}"

class Question_post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='questions/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Answer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question_post, on_delete=models.CASCADE, related_name='answers')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer by {self.user.username} to {self.question.title}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    question = models.ForeignKey(Question_post, on_delete=models.CASCADE, null=True, blank=True)


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}..."
