from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User # Standart User
from .models import Profile, Skill, UserSkill, Session, Review, Message

# ---------------------------------------------------------
# 1. USER & PROFILE MANAGEMENT
# ---------------------------------------------------------

@admin.action(description='Approve Selected Profiles (Activate)')
def approve_profiles(modeladmin, request, queryset):
    count = 0
    for profile in queryset:
        if profile.status != 'active':
            profile.status = 'active'
            profile.save() 
            count += 1     
    modeladmin.message_user(request, f"{count} profiles successfully activated.")

@admin.action(description='Suspend Selected Profiles')
def suspend_profiles(modeladmin, request, queryset):
    queryset.update(status='suspended')
    modeladmin.message_user(request, "Selected profiles suspended.")

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'status', 'is_rewarded')
    list_editable = ('status',)  
    search_fields = ('user__username', 'user__email', 'referral_code')
    list_filter = ('status', 'is_rewarded')
    actions = [approve_profiles, suspend_profiles]

# Profile'i kaydediyoruz
admin.site.register(Profile, ProfileAdmin)

# DİKKAT: User modelini tekrar register ETMİYORUZ.
# admin.site.register(User, UserAdmin)  <-- BU SATIR SİLİNDİ

# ---------------------------------------------------------
# 2. SKILL MANAGEMENT
# ---------------------------------------------------------

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category') 
    list_filter = ('category',)
    search_fields = ('name',)

# ---------------------------------------------------------
# 3. USER SKILLS (Ads)
# ---------------------------------------------------------

@admin.action(description='Approve Selected Skills')
def approve_skills(modeladmin, request, queryset):
    queryset.update(is_approved=True)
    modeladmin.message_user(request, "Selected skills approved.")

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'location', 'is_approved')
    list_filter = ('is_approved', 'location')
    search_fields = ('user__username', 'skill__name')
    actions = [approve_skills]

# ---------------------------------------------------------
# 4. SESSION MANAGEMENT
# ---------------------------------------------------------

@admin.action(description='Approve for Tutor (Set to Pending Tutor)')
def approve_sessions(modeladmin, request, queryset):
    queryset.update(status='pending_tutor')
    modeladmin.message_user(request, "Selected sessions sent to tutors for approval.")

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'skill', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__username', 'tutor__username', 'skill__name')
    actions = [approve_sessions]

# ---------------------------------------------------------
# 5. OTHERS (Reviews, Messages)
# ---------------------------------------------------------

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('session', 'rating', 'created_at')
    list_filter = ('rating',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'created_at', 'is_read')
    list_filter = ('is_read',)