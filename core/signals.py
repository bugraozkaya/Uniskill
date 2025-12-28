from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Profile
from django.db.models import Q

# 1. SİNYAL: KULLANICI ONAYLANDIĞINDA PUAN VERME
@receiver(post_save, sender=Profile)
def reward_referral(sender, instance, created, **kwargs):
    # Sadece durum 'active' ise VE daha önce ödül verilmediyse çalış
    if instance.status == 'active' and not instance.is_rewarded:
        
        print(f"--- 🚀 ÖDÜL SİSTEMİ TETİKLENDİ: {instance.user.username} ---")
        
        # A) Yeni üyeye +1 Saat
        instance.balance += 1
        instance.is_rewarded = True 
        instance.save(update_fields=['balance', 'is_rewarded'])
        print(f"✅ Yeni Üye ({instance.user.username}) hesabına +1 Saat eklendi.")

        # B) Davet Edeni Bulma (GÜÇLENDİRİLMİŞ MANTIK)
        raw_code = instance.used_referral
        
        if raw_code:
            clean_code = raw_code.strip()
            print(f"🔍 Aranan Kod/Kullanıcı: '{clean_code}'")

            # YÖNTEM 1: Önce Referans Koduna Bak (Büyük/Küçük harf duyarsız)
            referrer_profile = Profile.objects.filter(referral_code__iexact=clean_code).first()

            # YÖNTEM 2: Eğer Kodla Bulamazsan, KULLANICI ADINA Bak (Fallback)
            if not referrer_profile:
                print(f"⚠️ Kod ile bulunamadı, Kullanıcı Adı olarak aranıyor...")
                # Kullanıcı tablosundan username'i 'clean_code' olanı bul, sonra onun profilini al
                # settings.AUTH_USER_MODEL'e göre filtreleme yapıyoruz
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                try:
                    found_user = User.objects.get(username__iexact=clean_code)
                    referrer_profile = found_user.profile
                except User.DoesNotExist:
                    referrer_profile = None

            # SONUÇ: Referans Kişisi Bulunduysa Puanı Ver
            if referrer_profile:
                # Kendini davet etmeyi engelle
                if referrer_profile.user != instance.user:
                    referrer_profile.balance += 1
                    referrer_profile.save()
                    print(f"🎉 BAŞARILI! Davet Eden ({referrer_profile.user.username}) +1 Saat kazandı. Yeni Bakiye: {referrer_profile.balance}")
                    
                    # Eğer eski kullanıcının referans kodu boşsa, onu da dolduralım ki bir dahakine kolay bulunsun
                    if not referrer_profile.referral_code:
                        referrer_profile.referral_code = referrer_profile.user.username
                        referrer_profile.save(update_fields=['referral_code'])
                        print(f"ℹ️ Bilgi: {referrer_profile.user.username} kullanıcısının eksik referans kodu tamamlandı.")
                else:
                    print("⛔ Kişi kendi kodunu kullanmış, ödül verilmedi.")
            else:
                print(f"❌ HATA: '{clean_code}' isminde ne bir kod ne de bir kullanıcı bulunamadı!")
        else:
            print("ℹ️ Bu kullanıcı kayıt olurken herhangi bir kod girmemiş.")


# 2. SİNYAL: PROFİL OLUŞTURMA
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        ref_code = getattr(instance, 'username', instance.pk)
        Profile.objects.get_or_create(
            user=instance, 
            defaults={'referral_code': str(ref_code)}
        )