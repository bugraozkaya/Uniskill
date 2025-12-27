from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserSkill, Skill, Session, Review, Message, CATEGORY_CHOICES  
from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django import forms
# --- 1. KAYIT FORMU ---
class OgrenciKayitFormu(UserCreationForm):
    department = forms.CharField(label="Bölüm", widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone_number = forms.CharField(label="Telefon Numarası", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    referral_code = forms.CharField(
        label="Davet Kodu (Opsiyonel)", 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: burak'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'phone_number']

    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if code:
            if not User.objects.filter(username=code).exists():
                raise forms.ValidationError("Böyle bir kullanıcı bulunamadı!")
            return code
        return None

# --- 2. YETENEK EKLEME FORMU (DÜZELTİLDİ) ---
class UserSkillForm(forms.ModelForm):
    skill_name = forms.CharField(
        label="Yetenek Adı",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Python, Gitar...'})
    )
    
    category = forms.ChoiceField(
        label="Kategori",
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    description = forms.CharField(
        label="Ders Hakkında Açıklama",
        required=False, 
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 4, 
            'placeholder': 'Örn: Başlangıç seviyesinden alıp ileri seviyeye kadar öğretiyorum.'
        })
    )

    class Meta:
        model = UserSkill
        fields = ['certificate', 'location', 'description'] 
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select'}),
            'certificate': forms.FileInput(attrs={'class': 'form-control'}),
        }

    # *** İŞTE BU METOD SİLİNDİĞİ İÇİN HATA ALIYORDUN ***
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Formdan gelen yetenek ismini ve kategoriyi al
        input_name = self.cleaned_data['skill_name'].strip().title()
        input_category = self.cleaned_data['category']

        # Yeteneği bul veya oluştur
        skill_obj, created = Skill.objects.get_or_create(
            name=input_name,
            defaults={'category': input_category}
        )

        # Oluşan yeteneği kayda bağla
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

# --- 4. DEĞERLENDİRME FORMU ---
class DegerlendirmeFormu(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select', 
                'style': 'height: 50px;'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Ders ve eğitmen hakkındaki düşüncelerin...',
                'rows': 4
            }),
        }
        labels = {
            'rating': 'Puan',
            'comment': 'Yorum'
        }

# --- 5. MESAJ FORMU ---
class MesajFormu(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['department']