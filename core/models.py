from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# ---------------------------------------------------------
# 1. GLOBAL CHOICES (Used in multiple models)
# ---------------------------------------------------------

CATEGORY_CHOICES = [
    ('engineering', 'Engineering & Tech'),
    ('software', 'Software & Coding'),
    ('language', 'Foreign Languages'),
    ('art', 'Art & Design'),
    ('music', 'Music & Instruments'),
    ('math', 'Mathematics & Science'),
    ('personal', 'Personal Development'),
    ('other', 'Other'),
]

# ---------------------------------------------------------
# 2. PROFILE MODEL (Extends User with Balance & Status)
# ---------------------------------------------------------

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    
    balance = models.IntegerField(default=3, help_text="Balance in hours")
    department = models.CharField(max_length=100, blank=True, null=True)
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended')
    ]
    status = models.CharField(max_length=20, default='pending', choices=STATUS_CHOICES)
    
    # Referral System Fields
    referral_code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    used_referral = models.CharField(max_length=10, blank=True, null=True)
    is_rewarded = models.BooleanField(default=False, verbose_name="Referral Reward Given?")

    def __str__(self):
        return str(self.user)

# ---------------------------------------------------------
# 3. SKILL INVENTORY
# ---------------------------------------------------------

class Skill(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Category")
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

# ---------------------------------------------------------
# 4. USER SKILLS (Ads Posted by Users)
# ---------------------------------------------------------

class UserSkill(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    description = models.TextField(verbose_name="Description", blank=True)
    certificate = models.FileField(upload_to='certificates/', verbose_name="Certificate/Document", null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name="Is Approved?")
    
    LOCATION_CHOICES = [
        ('online', 'Online'),
        ('campus', 'On Campus'),
        ('library', 'Library'),
        ('other', 'Other'),
    ]
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='online')

    def __str__(self):
        return f"{self.user} - {self.skill.name}"

# ---------------------------------------------------------
# 5. SESSION (Classes/Meetings)
# ---------------------------------------------------------

class Session(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Waiting for Admin'),
        ('pending_tutor', 'Waiting for Tutor'),
        ('approved', 'Approved / Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='joined_sessions')
    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='given_sessions')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    date = models.DateTimeField()
    duration = models.PositiveIntegerField(help_text="Duration in hours")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self):
        if not self.date: return False
        return timezone.now() > (self.date + timedelta(hours=self.duration))

    def __str__(self):
        return f"{self.student} -> {self.tutor} ({self.skill.name})"

# ---------------------------------------------------------
# 6. REVIEWS & MESSAGES
# ---------------------------------------------------------

class Review(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating: {self.rating} for Session {self.session.id}"

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.recipient}"