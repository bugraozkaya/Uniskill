from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone
from django.conf import settings


# 1. USER MANAGEMENT (Kullanıcı ve Güvenlik)
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
    
    # Referral System
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
        
        if count > 0:
            return total_score / count
        return 0

# --- 2. SKILL INVENTORY (GÜNCELLENDİ) ---
# Kategori tablosunu kaldırdık, seçenekleri buraya ekledik.
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
    # Kategori artık bir yazı alanı ve seçenekli
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Kategori")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

# 3. USER SKILLS
class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    description = models.TextField(verbose_name="Ders Açıklaması", blank=True, help_text="Bu derste neler anlatacaksın? Yöntemin nedir?")

    certificate = models.FileField(upload_to='certificates/', verbose_name="Sertifika/Belge", blank=False, null=True)
    is_approved = models.BooleanField(default=False, verbose_name="Onaylandı mı?")
    LOCATION_CHOICES = [
        ('online', '🌐 Online (Zoom / Google Meet)'),
        ('tutor_home', '🏠 Kendi Evimde'),
        ('student_home', '🎒 Öğrencinin Evinde'),
        ('campus', '🏫 Kampüs / Ortak Alan'),
    ]
    
    location = models.CharField(
        max_length=20, 
        choices=LOCATION_CHOICES, 
        default='online', 
        verbose_name="Dersin İşleneceği Yer"
    )

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}"

# 4. SESSION / TRANSACTION
class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Admin Onayı Bekliyor'),
        ('pending_tutor', 'Hoca Onayı Bekliyor'),
        ('approved', 'Onaylandı / Aktif'),
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
        if self.student_id is None:
            return
        if self.status == 'scheduled' and self.student.balance < self.duration:
             raise ValidationError("Öğrencinin bakiyesi yetersiz!")
    
    @property
    def has_review(self):
        """
        Bu derse ait bir yorum var mı kontrol eder.
        Review modelinde session alanının related_name'i yoksa varsayılan 'review_set' kullanılır.
        """
        # Eğer Review modelinde OneToOneField kullandıysan:
        return hasattr(self, 'review') 
        
        # Eğer Review modelinde ForeignKey kullandıysan (Genel kullanım):
        # return self.review_set.exists()
    
    def __str__(self):
        return f"{self.student.username} -> {self.tutor.username} ({self.skill.name})"
    
    @property
    def is_expired(self):
        end_time = self.date + timedelta(hours=self.duration)
        return timezone.now() > end_time
    @property
    def is_expired(self):
        """Dersin süresi dolmuş mu kontrol eder."""
        if not self.date:
            return False
        # Bitiş zamanı = Ders Başlangıcı + Süresi (Saat)
        end_time = self.date + timedelta(hours=self.duration)
        return timezone.now() > end_time

# 5. REVIEW
class Review(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()

    def __str__(self):
        return f"Rating: {self.rating} for Session {self.session.id}"

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
    balance = models.IntegerField(default=3)
    status = models.CharField(
        max_length=20, 
        default='pending',
        choices=[
            ('pending', 'Onay Bekliyor'),
            ('active', 'Onaylı / Aktif'),
            ('suspended', 'Askıya Alındı')
        ]
    )
    referral_code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    used_referral = models.CharField(max_length=10, blank=True, null=True)
    is_rewarded = models.BooleanField(default=False, verbose_name="Referans Ödülü Verildi mi?")
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