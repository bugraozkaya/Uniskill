from django.contrib import admin
from .models import (
    Profile, 
    Skill, 
    UserSkill, 
    Session, 
    Review, 
    Message, 
    Notification,
    BlogPost, 
    Comment
)

# 1. PROFILE ADMIN
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'balance', 'status', 'get_rank_info_display')
    list_filter = ('status', 'department')
    search_fields = ('user__username', 'user__email', 'department')
    
    # Modeldeki property'yi admin panelinde göstermek için yardımcı metod
    def get_rank_info_display(self, obj):
        return obj.get_rank_info['title']
    get_rank_info_display.short_description = 'Rank'

# 2. SKILL ADMIN
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

# 3. USER SKILL ADMIN
@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'location', 'is_approved')
    list_filter = ('is_approved', 'location')
    search_fields = ('user__username', 'skill__name')
    actions = ['approve_skills']

    def approve_skills(self, request, queryset):
        queryset.update(is_approved=True)
    approve_skills.short_description = "Approve selected skills"

# 4. SESSION ADMIN
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'tutor', 'skill', 'date', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__username', 'tutor__username', 'skill__name')

# 5. REVIEW ADMIN
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('session', 'rating', 'created_at')
    list_filter = ('rating',)

# 6. MESSAGE ADMIN
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'created_at', 'is_read')
    list_filter = ('is_read',)

# 7. NOTIFICATION ADMIN
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at')

# --- YENİ EKLENEN: BLOG & COMMUNITY ADMIN ---

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'created_at', 'count_likes')
    list_filter = ('category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    # Slug alanını başlığa göre otomatik doldur
    prepopulated_fields = {'slug': ('title',)} 
    date_hierarchy = 'created_at'

    def count_likes(self, obj):
        return obj.likes.count()
    count_likes.short_description = 'Likes'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'short_body', 'created_at', 'parent')
    list_filter = ('created_at',)
    search_fields = ('body', 'author__username', 'post__title')

    # Yorumun tamamını değil, ilk 50 karakterini göster
    def short_body(self, obj):
        return obj.body[:50] + "..." if len(obj.body) > 50 else obj.body
    short_body.short_description = 'Comment'