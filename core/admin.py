from django.contrib import admin
from .models import Profile, Category, Skill, UserSkill, Session, Review

# --- 1. PROFİL YÖNETİMİ (Bakiyeleri Buradan Göreceksin) ---
class ProfileAdmin(admin.ModelAdmin):
    # Listede Kullanıcı Adı, Bakiye ve Durum yan yana görünsün
    list_display = ('user', 'balance', 'status')
    # Kullanıcı adına göre arama yapabilesin
    search_fields = ('user__username', 'user__email')
    # Duruma göre filtreleme yapabilesin
    list_filter = ('status',)

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
@admin.action(description='Seçili dersleri ONAYLA (Admin Onayı)')
def approve_sessions(modeladmin, request, queryset):
    queryset.update(status='approved')

class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'skill', 'date', 'status')
    list_filter = ('status', 'date')
    actions = [approve_sessions]

admin.site.register(Session, SessionAdmin)