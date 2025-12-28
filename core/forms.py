from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import UserSkill, Skill, Session, Review, Message, CATEGORY_CHOICES, Profile

# Doğru User modelini al
User = get_user_model()

# 1. KAYIT FORMU
class CustomUserCreationForm(UserCreationForm):
    used_referral = forms.CharField(
        label="Davet Kodu (Varsa)", 
        required=False, 
        max_length=10, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Varsa davet kodunu girin'})
    )

    department = forms.CharField(
        label="Bölüm", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Bilgisayar Mühendisliği'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

# 2. YETENEK EKLEME FORMU
class UserSkillForm(forms.ModelForm):
    skill_name = forms.CharField(label="Yetenek Adı", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    category = forms.ChoiceField(label="Kategori", choices=CATEGORY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = UserSkill
        fields = ['certificate', 'location', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
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

# 3. DERS TALEP FORMU
class DersTalepFormu(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'duration']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

# 4. MESAJ FORMU
class MesajFormu(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mesajınızı buraya yazın...'})
        }

# --- EKSİK OLAN KISIMLAR GERİ EKLENDİ ---

# 5. PROFİL GÜNCELLEME FORMLARI
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['department']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }

# 6. DEĞERLENDİRME FORMU
class DegerlendirmeFormu(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }