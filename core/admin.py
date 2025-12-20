from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, Skill, UserSkill, Session, Review

# Kullanıcı Paneli Özelleştirmesi (Gatekeeper Görünümü)
class CustomUserAdmin(UserAdmin):
    # Listede görünecek sütunlar
    list_display = ('username', 'email', 'department', 'balance', 'status')
    # Yan tarafta filtreleme kutusu (Hoca buna bayılır)
    list_filter = ('status', 'department', 'is_staff')
    
    # Detay sayfasına yeni alanlarımızı ekleyelim
    fieldsets = UserAdmin.fieldsets + (
        ('UniSkill Bilgileri', {'fields': ('phone_number', 'department', 'balance', 'status', 'invited_by')}),
    )

# Diğer tabloları basitçe kaydedelim
admin.site.register(User, CustomUserAdmin)
admin.site.register(Category)
admin.site.register(Skill)
admin.site.register(UserSkill)
admin.site.register(Session)
admin.site.register(Review)