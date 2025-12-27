from django.contrib import admin
from .models import User, Profile, Skill, UserSkill, Session, Review, Message

from django.contrib.auth.models import User # <--- MAKE SURE TO IMPORT THIS


# --- 1. KULLANICI & PROFİL YÖNETİMİ ---

# core/admin.py

# core/admin.py


@admin.action(description='Approve Selected Profiles (Activate & Give Referral Bonus)')
def approve_profiles(modeladmin, request, queryset):
    count = 0
    for profile in queryset:
        # Only process if the user is NOT already active
        if profile.status != 'active':
            profile.status = 'active'
            
            # --- REFERRAL BONUS LOGIC ---
            if profile.used_referral:
                try:
                    # Logic: The referral code IS the username of the referrer.
                    # We search for the User with that username.
                    referrer_user = User.objects.get(username=profile.used_referral)
                    referrer_profile = referrer_user.profile
                    
                    # 1. Add +1 Hour to the Referrer (Owner of the code)
                    referrer_profile.balance += 1
                    referrer_profile.save()

                    # 2. Add +1 Hour to the New User (The Referee)
                    # New balance will be 3 (default) + 1 (bonus) = 4
                    profile.balance += 1
                    
                except User.DoesNotExist:
                    # If the username entered as a code does not exist
                    pass 
                except Exception as e:
                    # Log other errors silently
                    print(f"Error in referral system: {e}")
            # ---------------------------

            profile.save()
            count += 1
            
    modeladmin.message_user(request, f"{count} profiles successfully activated.")

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