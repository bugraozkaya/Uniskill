from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

# 1. USER MANAGEMENT (Kullanıcı ve Güvenlik)
class User(AbstractUser):
    STATUS_CHOICES = (
        ('pending', 'Pending (Onay Bekliyor)'),
        ('active', 'Active (Onaylandı)'),
        ('banned', 'Banned (Yasaklı)'),
    )
    
    # Standart alanlar (username, email, password) zaten AbstractUser'dan gelir.
    # Biz ekstra alanları ekliyoruz:
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    balance = models.IntegerField(default=5, help_text="Saat cinsinden bakiye")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Referral System (Recursive Relationship - Kendine Referans)
    invited_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    def __str__(self):
        return f"{self.username} ({self.get_status_display()})"
    @property
    def average_rating(self):
        # Bu kullanıcının verdiği dersleri (teaching_sessions) bul
        # Sadece yorum yapılmış olanların puanlarını topla
        total_score = 0
        count = 0
        
        # teaching_sessions: Session modelindeki related_name='teaching_sessions' sayesinde erişiyoruz
        for session in self.teaching_sessions.all():
            if hasattr(session, 'review'): # Eğer derse yorum yapılmışsa
                total_score += session.review.rating
                count += 1
        
        if count > 0:
            return total_score / count
        return 0 # Hiç yorum yoksa 0 döndür

# 2. SKILL INVENTORY (Yetenek Envanteri)
class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Skill(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# 3. USER SKILLS (Hangi kullanıcı hangi dersi veriyor - M:N Ara Tablosu)
# core/models.py içinde

class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    # --- YENİ EKLENEN ALANLAR ---
    # Kullanıcıdan belge istiyoruz (Zorunlu)
    certificate = models.FileField(upload_to='certificates/', verbose_name="Sertifika/Belge", blank=False, null=True)
    
    # Admin onayı gerekiyor (Varsayılan: Onaysız)
    is_approved = models.BooleanField(default=False, verbose_name="Onaylandı mı?")

    LOCATION_CHOICES = [
        ('online', '🌐 Online (Zoom / Google Meet)'),
        ('tutor_home', '🏠 Kendi Evimde'),
        ('student_home', '🎒 Öğrencinin Evinde'),
        ('campus', '🏫 Kampüs / Ortak Alan'),
    ]
    
    # default='online' dedik ki eski kayıtlar bozulmasın
    location = models.CharField(
        max_length=20, 
        choices=LOCATION_CHOICES, 
        default='online', 
        verbose_name="Dersin İşleneceği Yer"
    )

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}"

# 4. SESSION / TRANSACTION (Zaman Bankası İşlemleri)
class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Admin Onayı Bekliyor'),       # İlk Aşama
        ('pending_tutor', 'Hoca Onayı Bekliyor'),  # İkinci Aşama (YENİ)
        ('approved', 'Onaylandı / Aktif'),         # Son Aşama
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_sessions')
    tutor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_sessions')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    date = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Saat cinsinden süre")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    def clean(self):
        # DÜZELTME: Eğer form validasyonu sırasındaysak ve öğrenci henüz atanmamışsa kontrolü atla
        if self.student_id is None:
            return

        # Database Dersi Kuralı: Bakiye Yetersizse İşlem Yapma
        if self.status == 'scheduled' and self.student.balance < self.duration:
             raise ValidationError("Öğrencinin bakiyesi yetersiz!")
    @property
    def has_review(self):
        # Bu dersin bir incelemesi (review) var mı kontrol eder
        return hasattr(self, 'review')
    
    def __str__(self):
        return f"{self.student.username} -> {self.tutor.username} ({self.skill.name})"
    @property
    def is_expired(self):
        # Bitiş Zamanı = Başlangıç Zamanı + Süre (Saat)
        end_time = self.date + timedelta(hours=self.duration)
        # Şu anki zaman, bitiş zamanını geçti mi?
        return timezone.now() > end_time
    
    
    
# 5. REVIEW (Değerlendirme - Weak Entity)
class Review(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)]) # 1-5 arası puan
    comment = models.TextField()

    def __str__(self):
        return f"Rating: {self.rating} for Session {self.session.id}"
    
# core/models.py en altına ekle

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField(verbose_name="Mesaj İçeriği")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} -> {self.recipient}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.IntegerField(default=3)  # Varsayılan 3 saat
    status = models.CharField(
        max_length=20, 
        default='pending',  # <--- BURASI 'pending' OLMALI (active DEĞİL)
        choices=[
            ('pending', 'Onay Bekliyor'),
            ('active', 'Onaylı / Aktif'),
            ('suspended', 'Askıya Alındı')
        ]
    )
    referral_code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    used_referral = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profili"
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)