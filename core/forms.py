from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserSkill, Skill, Session, Review, Message, CATEGORY_CHOICES, Profile

# Get the correct User model
User = get_user_model()

# 1. REGISTRATION FORM
class CustomUserCreationForm(UserCreationForm):
    used_referral = forms.CharField(
        label="Referral Code (Optional)", 
        required=False, 
        max_length=10, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter referral code if you have one'})
    )

    department = forms.CharField(
        label="Department", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Engineering'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

# 2. ADD SKILL FORM
class UserSkillForm(forms.ModelForm):
    skill_name = forms.CharField(label="Skill Name", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Guitar, Calculus'}))
    category = forms.ChoiceField(label="Category", choices=CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = UserSkill
        fields = ['certificate', 'location', 'description']
        labels = {
            'certificate': 'Certificate / Proof (Optional)',
            'location': 'Preferred Location',
            'description': 'Description'
        }
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your experience...'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'certificate': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        input_name = self.cleaned_data['skill_name'].strip().title()
        input_category = self.cleaned_data['category']
        skill_obj, _ = Skill.objects.get_or_create(name=input_name, defaults={'category': input_category})
        instance.skill = skill_obj
        if commit:
            instance.save()
        return instance

# 3. SESSION REQUEST FORM
class DersTalepFormu(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'duration']
        labels = {
            'date': 'Date & Time',
            'duration': 'Duration (Hours)'
        }
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

# 4. MESSAGE FORM
class MesajFormu(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        labels = {
            'body': '' # No label for chat input
        }
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Type your message here...'})
        }

# 5. PROFILE UPDATE FORMS
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address'
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # --- BURASI DEĞİŞTİ: Avatar alanı eklendi ---
        fields = ['department', 'avatar']
        labels = {
            'department': 'Department',
            'avatar': 'Profile Picture'
        }
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}), # Dosya yükleme butonu
        }

# 6. REVIEW FORM
class DegerlendirmeFormu(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Rating',
            'comment': 'Comment'
        }
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'How was the session?'}),
        }

# 7. CONTACT FORM (YENİ EKLENEN)
class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'})
    )
    subject = forms.CharField(
        max_length=200, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your Message'})
    )