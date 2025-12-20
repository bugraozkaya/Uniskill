from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import User

@receiver(pre_save, sender=User)
def reward_referral(sender, instance, **kwargs):
    # Eğer kullanıcı veritabanında yeni değilse (güncelleniyorsa)
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            
            # KURAL: Statü 'pending' den 'active' e geçiyorsa VE bir davet eden varsa
            if old_user.status == 'pending' and instance.status == 'active' and instance.invited_by:
                
                # 1. Yeni kullanıcıya hediye
                instance.balance += 1
                
                # 2. Davet edene hediye
                inviter = instance.invited_by
                inviter.balance += 1
                inviter.save()
                
                print(f"REFERANS KAZANCI: {instance.username} ve {inviter.username} +1 saat kazandı!")
                
        except User.DoesNotExist:
            pass