from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Profile  # User yerine Profile modelini çağırıyoruz
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile
@receiver(pre_save, sender=Profile)  # DİKKAT: Artık Profile tablosunu dinliyoruz
def reward_referral(sender, instance, **kwargs):
    # Eğer bu yeni bir kayıt değilse (güncelleme yapılıyorsa)
    if instance.pk:
        try:
            # Veritabanındaki eski halini çekiyoruz
            old_profile = Profile.objects.get(pk=instance.pk)
            
            # KURAL: Eskiden 'active' DEĞİLSE ve şimdi 'active' OLUYORSA
            if old_profile.status != 'active' and instance.status == 'active':
                
                # Bu profilin bağlı olduğu kullanıcıyı al
                user = instance.user
                
                # Bu kullanıcıyı davet eden biri var mı?
                if user.invited_by:
                    # 1. Yeni üyeye (şu anki profile) +1 Saat ekle
                    instance.balance += 1
                    
                    # 2. Davet edeni bul
                    inviter = user.invited_by
                    
                    # Davet edenin profili var mı diye kontrol et (Hata almamak için)
                    if hasattr(inviter, 'profile'):
                        inviter.profile.balance += 1
                        inviter.profile.save() # Davet edeni hemen kaydet
                        
                        print(f"✅ REFERANS KAZANCI: {inviter.username} ve {user.username} +1 saat kazandı!")
                        
        except Profile.DoesNotExist:
            pass

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Yeni kullanıcı oluşunca profilini ve benzersiz kodunu oluştur
        Profile.objects.create(user=instance, referral_code=instance.username)