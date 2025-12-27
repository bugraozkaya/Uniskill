from django.contrib import admin
from .models import User, Profile, Skill, UserSkill, Session, Review, Message

# --- 1. KULLANICI & PROFİL YÖNETİMİ ---

@admin.action(description='Seçili Profilleri ONAYLA (Aktif Yap)')
def approve_profiles(modeladmin, request, queryset):
    queryset.update(status='active')
    modeladmin.message_user(request, "Seçilen profiller başarıyla onaylandı.")

@admin.action(description='Seçili Profilleri ASKIYA AL')
def suspend_profiles(modeladmin, request, queryset):
    queryset.update(status='suspended')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'status')
    list_editable = ('status',)  
    search_fields = ('user__username', 'user__email')
    list_filter = ('status',)
    actions = [approve_profiles, suspend_profiles]

admin.site.register(Profile, ProfileAdmin)
admin.site.register(User)

# --- 2. YETENEK YÖNETİMİ (Category Yok Artık) ---

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category') 
    list_filter = ('category',)
    search_fields = ('name',)

# --- 3. KULLANICI YETENEKLERİ ---

@admin.action(description='Seçili yetenekleri ONAYLA')
def approve_skills(modeladmin, request, queryset):
    queryset.update(is_approved=True)

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'location', 'is_approved', 'certificate')
    list_filter = ('is_approved', 'location')
    search_fields = ('user__username', 'skill__name')
    actions = [approve_skills]

# --- 4. DERS YÖNETİMİ ---

@admin.action(description='Seçili dersleri HOCAYA GÖNDER (Pending Tutor)')
def approve_sessions(modeladmin, request, queryset):
    queryset.update(status='pending_tutor')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'skill', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__username', 'tutor__username', 'skill__name')
    actions = [approve_sessions]

# --- 5. DİĞERLERİ ---
admin.site.register(Review)
admin.site.register(Message)