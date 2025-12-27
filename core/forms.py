from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import User, UserSkill, Skill, Session, Review, Message, CATEGORY_CHOICES, Profile

User = get_user_model()

# --- 1. KAYIT FORMLARI ---
# views.py hem 'OgrenciKayitFormu' hem de 'CustomUserCreationForm' isimlerini aradığı için ikisini de tanımlıyoruz
class OgrenciKayitFormu(UserCreationForm):
    department = forms.CharField(label="Bölüm", widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label="Telefon Numarası", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    referral_code = forms.CharField(label="Davet Kodu", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "department", "phone_number", "referral_code")

class CustomUserCreationForm(OgrenciKayitFormu):
    """views.py içerisinde bu isimle de çağrıldığı için hata almamak adına ekledik."""
    pass

# --- 2. YETENEK EKLEME FORMU ---
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

# --- 3. DERS TALEP FORMU ---
class DersTalepFormu(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['date', 'duration']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }

# --- 4. MESAJ FORMU ---
class MesajFormu(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Mesajınızı buraya yazın...'})
        }

# --- 5. GÜNCELLEME VE DEĞERLENDİRME FORMLARI ---
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['department']

class DegerlendirmeFormu(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }