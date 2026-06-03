from django import forms
from .models import Answer, ContactMessage, Question_post, Profile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adyňyz'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email adresiňiz'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Habarýňyz', 'rows': 5}),
        }



class RegisterForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254, widget=forms.EmailInput(attrs={'placeholder': 'Emailiňizi ýazyň'}))
    password = forms.CharField(label='Kod', min_length=8, widget=forms.PasswordInput(attrs={'placeholder': 'Kodyňyzy ýazyň'}))

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Bu email ulgama eýýäm hasaba alyndy.")
        return email


class LoginForm(forms.Form):
    username = forms.CharField(label="Ulanyjy ady ýa-da email", max_length=150)
    password = forms.CharField(label="Açar söz", widget=forms.PasswordInput)


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label='Açar söz', widget=forms.PasswordInput)
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ['email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu email eýýäm ulanylýar.')
        return email

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Ulanyjy ady ýa-da email')


class LearningPlanForm(forms.Form):
    # This form will be used to get the days of the week from the user
    DAYS_OF_WEEK = (
        ('dusenbe', 'Düşenbe'),
        ('sisenbe', 'Sişenbe'),
        ('carsenbe', 'Çarşenbe'),
        ('penshenbe', 'Penşenbe'),
        ('anna', 'Anna'),
        ('shenbe', 'Şenbe'),
        ('yeksenbe', 'Ýekşenbe'),
    )
    days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture','bio']



class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question_post
        fields = ['title', 'content', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soragyň ady'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Soragyňyz barada giňişleýin maglumat', 'rows': 5}),
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Jogabyňyzy ýazyň', 'rows': 3}),
        }
