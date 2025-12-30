from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db.models import Q
from django.urls import reverse # <-- YENİ EKLENDİ (Link oluşturmak için)

# Tüm modelleri buraya ekledik
from .models import Profile, Session, Notification, Message 

# ---------------------------------------------------------
# 1. MEVCUT SİNYAL: REWARD SYSTEM (REFERRAL)
# ---------------------------------------------------------
@receiver(post_save, sender=Profile)
def reward_referral(sender, instance, created, **kwargs):
    # Run only if status is 'active' AND reward hasn't been given yet
    if instance.status == 'active' and not instance.is_rewarded:
        
        print(f"--- 🚀 REWARD SYSTEM TRIGGERED: {instance.user.username} ---")
        
        # A) +1 Hour to New Member
        instance.balance += 1
        instance.is_rewarded = True 
        instance.save(update_fields=['balance', 'is_rewarded'])
        print(f"✅ New Member ({instance.user.username}) gained +1 Hour.")

        # B) Find Referrer (ENHANCED LOGIC)
        raw_code = instance.used_referral
        
        if raw_code:
            clean_code = raw_code.strip()
            print(f"🔍 Searching Code/User: '{clean_code}'")

            # METHOD 1: Check Referral Code first (Case-insensitive)
            referrer_profile = Profile.objects.filter(referral_code__iexact=clean_code).first()

            # METHOD 2: If not found by Code, check USERNAME (Fallback)
            if not referrer_profile:
                print(f"⚠️ Not found by code, searching as Username...")
                # Search for username in User table, then get the profile
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    found_user = User.objects.get(username__iexact=clean_code)
                    referrer_profile = found_user.profile
                except User.DoesNotExist:
                    referrer_profile = None

            # RESULT: If Referrer Found, Give Reward
            if referrer_profile:
                # Prevent self-referral
                if referrer_profile.user != instance.user:
                    referrer_profile.balance += 1
                    referrer_profile.save()
                    print(f"🎉 SUCCESS! Referrer ({referrer_profile.user.username}) gained +1 Hour. New Balance: {referrer_profile.balance}")
                    
                    # If old user has missing referral code, fill it now for future ease
                    if not referrer_profile.referral_code:
                        referrer_profile.referral_code = referrer_profile.user.username
                        referrer_profile.save(update_fields=['referral_code'])
                        print(f"ℹ️ Info: Missing referral code populated for user {referrer_profile.user.username}.")
                else:
                    print("⛔ User used their own code, no reward given.")
            else:
                print(f"❌ ERROR: No code or user found with name '{clean_code}'!")
        else:
            print("ℹ️ This user did not enter any code during registration.")


# ---------------------------------------------------------
# 2. MEVCUT SİNYAL: CREATE PROFILE
# ---------------------------------------------------------
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        ref_code = getattr(instance, 'username', instance.pk)
        # Prevent duplicates using get_or_create
        Profile.objects.get_or_create(
            user=instance, 
            defaults={'referral_code': str(ref_code)}
        )

# ---------------------------------------------------------
# 3. YENİ SİNYAL: SESSION NOTIFICATIONS (Ders Talepleri)
# ---------------------------------------------------------
@receiver(post_save, sender=Session)
def create_session_notification(sender, instance, created, **kwargs):
    if created:
        # Yeni talep oluşturulduğunda -> EĞİTMENE BİLDİRİM
        Notification.objects.create(
            recipient=instance.tutor,
            message=f"New request: {instance.student.first_name} wants to learn {instance.skill.name}!",
            link=reverse('dashboard')
        )
        print(f"🔔 Notification sent to Tutor: {instance.tutor.username}")
    else:
        # Var olan talep güncellendiğinde (Onay/Ret)
        if instance.status == 'approved':
            # Onaylandı -> ÖĞRENCİYE BİLDİRİM
            Notification.objects.create(
                recipient=instance.student,
                message=f"Great news! Your session for {instance.skill.name} is APPROVED.",
                link=reverse('dashboard')
            )
            print(f"🔔 Notification sent to Student: {instance.student.username} (Approved)")
            
        elif instance.status == 'cancelled':
            # İptal edildi -> İLGİLİ KİŞİYE BİLDİRİM
            # (Basitlik adına: İptal durumunda her iki tarafa da iptal bilgisi düşülebilir, 
            # şimdilik öğrenciye haber verelim)
            Notification.objects.create(
                recipient=instance.student,
                message=f"Session for {instance.skill.name} has been cancelled.",
                link=reverse('dashboard')
            )

# ---------------------------------------------------------
# 4. YENİ SİNYAL: MESSAGE NOTIFICATIONS (Yeni Mesajlar)
# ---------------------------------------------------------
@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.recipient,
            message=f"New message from {instance.sender.first_name}",
            link=reverse('chat_detail', args=[instance.sender.id])
        )
        print(f"🔔 Message Notification sent to: {instance.recipient.username}")