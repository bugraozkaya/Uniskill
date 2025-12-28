from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

# --- 1. USER MANAGEMENT ---
class User(AbstractUser):
    STATUS_CHOICES = (
        ('pending', 'Pending (Onay Bekliyor)'),
        ('active', 'Active (Onaylandı)'),
        ('banned', 'Banned (Yasaklı)'),
    )
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    balance = models.IntegerField(default=5, help_text="Saat cinsinden bakiye")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    def __str__(self):
        return f"{self.username} ({self.get_status_display()})"
    
    @property
    def average_rating(self):
        total_score = 0
        count = 0
        for session in self.teaching_sessions.all():
            if hasattr(session, 'review'):
                total_score += session.review.rating
                count += 1
        return total_score / count if count > 0 else 0

# --- 2. SKILL INVENTORY ---
CATEGORY_CHOICES = [
    ('engineering', '⚙️ Mühendislik & Teknoloji'),
    ('software', '💻 Yazılım & Kodlama'),
    ('language', '🌍 Yabancı Dil'),
    ('art', '🎨 Sanat & Tasarım'),
    ('music', '🎵 Müzik & Enstrüman'),
    ('math', '📐 Matematik & Fen'),
    ('personal', '🌱 Kişisel Gelişim'),
    ('other', '⚡ Diğer'),
]

class Skill(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Kategori")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

# --- 3. USER SKILLS ---
class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    description = models.TextField(verbose_name="Ders Açıklaması", blank=True)
    certificate = models.FileField(upload_to='certificates/', verbose_name="Sertifika/Belge", null=True)
    is_approved = models.BooleanField(default=False, verbose_name="Onaylandı mı?")
    
    LOCATION_CHOICES = [
        ('online', '🌐 Online'),
        ('tutor_home', '🏠 Kendi Evimde'),
        ('student_home', '🎒 Öğrencinin Evinde'),
        ('campus', '🏫 Kampüs'),
    ]
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='online')

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}"

# --- 4. SESSION ---
class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Admin Onayı Bekliyor'),
        ('pending_tutor', 'Hoca Onayı Bekliyor'),
        ('approved', 'Onaylandı / Aktif'),
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_sessions')
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_sessions')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    date = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Saat cinsinden süre")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    @property
    def is_expired(self):
        if not self.date: return False
        return timezone.now() > (self.date + timedelta(hours=self.duration))

# --- 5. REVIEW ---
class Review(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

# core/models.py

from django.db import models
from django.conf import settings  # <-- 1. BU SATIRI EKLE (User yerine bunu kullanacağız)
# from django.contrib.auth.models import User  <-- BU SATIRI SİL VEYA YORUMA AL

class Profile(models.Model):
    # 2. AŞAĞIDAKİ SATIRI DEĞİŞTİR: 'User' yerine 'settings.AUTH_USER_MODEL' yaz
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    balance = models.IntegerField(default=3)
    department = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending', choices=[('pending', 'Onay Bekliyor'), ('active', 'Aktif')])
    
    referral_code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    used_referral = models.CharField(max_length=10, blank=True, null=True)
    is_rewarded = models.BooleanField(default=False, verbose_name="Referans Ödülü Verildi mi?")

    def __str__(self):
        # user.username hata verebilir, string döndürmek için self.user yeterli olabilir veya self.user.username (eğer custom modelde username varsa)
        return str(self.user)
    
# --- SIGNALS ---
@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()