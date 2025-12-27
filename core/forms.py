from django import forms
from django.contrib.auth.forms import UserCreationForm
# Modelleri import et (Review modelini eklemeyi unutma!)
from .models import User, UserSkill, Skill, Category, Session, Review 
from .models import Message
from django import forms
from .models import UserSkill

class OgrenciKayitFormu(UserCreationForm):
    # ... (Buradaki eski kodların aynen kalsın) ...
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'phone_number']
    department = forms.CharField(label="Bölüm", widget=forms.TextInput(attrs={'class': 'form-control'}))
    referral_code = forms.CharField(
        label="Davet Kodu (Opsiyonel)", 
        required=False, 
        help_text="Sizi davet eden arkadaşınızın kullanıcı adı.",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: burak'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'department', 'phone_number']

    department = forms.CharField(label="Bölüm", widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Temizleme (Validation) işlemi: Girilen kod gerçekten var mı?
    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if code:
            if not User.objects.filter(username=code).exists():
                raise forms.ValidationError("Böyle bir kullanıcı bulunamadı!")
            return code
        return None

class YetenekEkleFormu(forms.ModelForm):
    # ... (Buradaki eski kodların aynen kalsın) ...
    category = forms.ModelChoiceField(queryset=Category.objects.all(), label="Kategori Seçin", widget=forms.Select(attrs={'class': 'form-select'}))
    skill_name = forms.CharField(label="Yetenek Adı (Örn: Python, Gitar)", widget=forms.TextInput(attrs={'class': 'form-control'}))
    description = forms.CharField(label="Açıklama (Opsiyonel)", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    class Meta:
        model = UserSkill
        fields = []

class DersTalepFormu(forms.ModelForm):
    # ... (Buradaki eski kodların aynen kalsın) ...
    class Meta:
        model = Session
        fields = ['date', 'duration']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
        }
        labels = {
            'date': 'Ders Tarihi ve Saati',
            'duration': 'Süre (Saat)',
        }

# --- EKSİK OLAN KISIM BURASI, BUNU EN ALTA YAPIŞTIR ---
class DegerlendirmeFormu(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} Yıldız') for i in range(5, 0, -1)], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Hoca nasıldı? Dersten memnun kaldın mı?'}),
        }
        labels = {
            'rating': 'Puanınız',
            'comment': 'Yorumunuz',
        }

class MesajFormu(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Merhaba, ders hakkında sormak istediğim...'})
        }
        labels = {
            'body': 'Mesajınız'
        }



# core/forms.py

class UserSkillForm(forms.ModelForm):
    class Meta:
        model = UserSkill
        # Fields listesine 'location'ı eklemeyi UNUTMA!
        fields = ['skill', 'location', 'certificate'] 
        widgets = {
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}), # <-- Yeni Stil
            'certificate': forms.FileInput(attrs={'class': 'form-control'})
        }