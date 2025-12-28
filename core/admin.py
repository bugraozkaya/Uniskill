from django.contrib import admin
from .models import Profile, Skill, UserSkill, Session, Review, Message

# 1. Profil Yönetimi
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'balance', 'status') # Listede görünecek sütunlar
    list_filter = ('status', 'department') # Sağ tarafta filtreleme kutusu
    search_fields = ('user__username', 'user__email') # Arama çubuğu

# 2. Yetenekler (Skills)
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

# 3. Kullanıcı Yetenekleri
@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'location', 'is_approved')
    list_filter = ('is_approved', 'location')
    actions = ['approve_skills']

    # Toplu onaylama aksiyonu
    def approve_skills(self, request, queryset):
        queryset.update(is_approved=True)
    approve_skills.short_description = "Seçilen yetenekleri onayla"

# 4. Ders Oturumları (Session)
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'skill', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__username', 'tutor__username')

# 5. Değerlendirmeler (Review)
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('session', 'rating', 'created_at')

# 6. Mesajlar
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'created_at', 'is_read')