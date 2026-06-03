from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('home', views.index, name="index"),
    path('contact', views.contact_view, name='contact'),
    path('success', views.contact_success_view, name='contact_success'),
    
    
    # Learning Planynkylar
    path('category/<slug:category_slug>/plan/complete/', views.complete_learning_plan_quiz, name='complete_learning_plan_quiz'),
    path('category/<slug:category_slug>/certificate/name/', views.certificate_form_view, name='certificate_form_view'),
    path('category/<slug:category_slug>/certificate/generate/', views.generate_certificate, name='generate_certificate'),
    path('category/<slug:category_slug>/plan/create/', views.personal_course, name='create_learning_plan'),
    path('category/<slug:category_slug>/plan/', views.view_learning_plan, name='view_learning_plan'), # THIS PATH IS NOW CORRECTLY FIRST
    
    # Quiz
    path('category/<slug:category_slug>/quiz/results/', views.quiz_results, name='quiz_results'),
    path('category/<slug:category_slug>/quiz/', views.quiz_view, name='quiz_view'),

    # bolumler
    path('chapter/<slug:category_slug>/<slug:chapter_slug>/complete/', views.mark_chapter_complete, name='mark_chapter_complete'),
    path('category/<slug:category_slug>/<slug:chapter_slug>/', views.chapter_detail, name='chapter_detail'),
    
    # 2. kategoriya
    path('category/<slug:category_slug>/', views.category_detail, name='category_detail'),
    
    # 3. galanlar
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/done/', views.logout_done_view, name='logout_done'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
    path('about/', views.about_view, name='about'),
    path('plan/delete/<int:plan_id>/', views.delete_learning_plan, name='delete_learning_plan'),
    path('questions/ask/', views.create_question, name='create_question'),
    path('questions/<slug:slug>/', views.question_detail, name='question_detail'),
    path('questions/', views.question_list, name='question_list'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('rewards/', views.daily_rewards_view, name='daily_rewards'),
    path('reyting/', views.leaderboard_view, name='leaderboard'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('ai/', views.codelab_main_view, name='ai'), 
]