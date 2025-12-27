from django.contrib import admin
from .models import Profile, Category, Skill, UserSkill, Session, Review

# --- 1. PROFIL YÖNETİMİ (GÜNCELLENDİ) ---

# Toplu Onaylama Fonksiyonu (Action)
@admin.action(description='Seçili Profilleri ONAYLA (Aktif Yap)')
def approve_profiles(modeladmin, request, queryset):
    queryset.update(status='active')
    modeladmin.message_user(request, "Seçilen profiller başarıyla onaylandı/aktif edildi.")

@admin.action(description='Seçili Profilleri ASKIYA AL')
def suspend_profiles(modeladmin, request, queryset):
    queryset.update(status='suspended')

class ProfileAdmin(admin.ModelAdmin):
    # Listede görünecek sütunlar
    list_display = ('user', 'balance', 'status')
    
    # *** İŞTE SİHİRLİ SATIR BURASI ***
    # Bu satır sayesinde listedeyken durumu değiştirebileceksin:
    list_editable = ('status',) 
    
    search_fields = ('user__username', 'user__email')
    list_filter = ('status',)
    
    # Toplu işlem butonlarını ekle
    actions = [approve_profiles, suspend_profiles]

admin.site.register(Profile, ProfileAdmin)


# --- 2. DİĞER MODELLER ---

admin.site.register(Category)
admin.site.register(Skill)

class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill')
    search_fields = ('user__username', 'skill__name')

admin.site.register(UserSkill, UserSkillAdmin)

admin.site.register(Review)


# --- 3. DERS ONAY SİSTEMİ ---
@admin.action(description='Seçili dersleri HOCAYA GÖNDER (Pending Tutor)')
def approve_sessions(modeladmin, request, queryset):
    queryset.update(status='pending_tutor')

class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'skill', 'date', 'status')
    list_filter = ('status', 'date')
    actions = [approve_sessions]

admin.site.register(Session, SessionAdmin)