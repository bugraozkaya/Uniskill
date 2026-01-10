from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
# 'render' fonksiyonu gerekli
from django.shortcuts import redirect, render 
from django.contrib.auth import views as auth_views 

from core import views

# View fonksiyonlarını import ediyoruz
from core.views import (
    landing_page, leaderboard,
    dashboard, register, logout_view, add_skill, 
    search_skills, request_session, complete_session, 
    add_review, admin_stats, 
    messaging, 
    CustomLoginView, approve_session_tutor, reject_session_tutor,
    meeting_room, cancel_session,
    public_profile, edit_profile,
    mark_notification_as_read,
    activate,
    contact_us,
    # --- BLOG VIEWLARI ---
    blog_list, blog_detail, blog_create,
    vote_comment, 
    # --- YENİ EKLENEN: SİLME VE DÜZENLEME ---
    delete_comment, edit_comment
)

urlpatterns = [
    # --- GÜVENLİK ---
    path('uniskill-yonetim-2025/', admin.site.urls),
    path('admin/', lambda request: redirect('/')),

    # Ana Sayfa & Dashboard
    path('', landing_page, name='landing_page'),
    path('dashboard/', dashboard, name='dashboard'),

    # Leaderboard
    path('leaderboard/', leaderboard, name='leaderboard'),

    # Kimlik Doğrulama
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # E-POSTA AKTİVASYON YOLU
    path('activate/<uidb64>/<token>/', activate, name='activate'),

    # --- ŞİFRE SIFIRLAMA YOLLARI ---
    path('reset_password/', 
         auth_views.PasswordResetView.as_view(template_name="core/password_reset.html"), 
         name="reset_password"),

    path('reset_password_sent/', 
         auth_views.PasswordResetDoneView.as_view(template_name="core/password_reset_sent.html"), 
         name="password_reset_done"),

    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name="core/password_reset_form.html"), 
         name="password_reset_confirm"),

    path('reset_password_complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name="core/password_reset_done.html"), 
         name="password_reset_complete"),
    # ----------------------------------------------------

    # Yetenek İşlemleri
    path('add-skill/', add_skill, name='add_skill'),
    path('search/', search_skills, name='search_skills'),
    
    # Profil Sayfaları
    path('profile/<int:user_id>/', public_profile, name='public_profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),

    # Ders/Oturum İşlemleri
    path('request-session/<int:skill_id>/', request_session, name='request_session'),
    path('complete/<int:session_id>/', complete_session, name='complete_session'),
    path('add-review/<int:session_id>/', add_review, name='add_review'),

    # Onay / Red / İptal
    path('approve-session/<int:session_id>/', approve_session_tutor, name='approve_session_tutor'),
    path('reject-session/<int:session_id>/', reject_session_tutor, name='reject_session_tutor'),
    path('cancel-session/<int:session_id>/', cancel_session, name='cancel_session'),
    
    # Toplantı Odası
    path('meeting/<int:session_id>/', meeting_room, name='meeting_room'),
    
    # Admin İstatistikleri
    path('admin-stats/', admin_stats, name='admin_stats'),

    # --- MESAJLAŞMA SİSTEMİ ---
    path('messages/', messaging, name='messaging_home'),
    path('messages/<int:user_id>/', messaging, name='messaging'),

    # Bildirim Sistemi
    path('notification/read/<int:notification_id>/', mark_notification_as_read, name='mark_notification_as_read'),

    # İletişim Sayfası
    path('contact/', contact_us, name='contact'),

    # --- BLOG & COMMUNITY SİSTEMİ ---
    path('community/', blog_list, name='blog_list'),
    path('community/write/', blog_create, name='blog_create'),
    path('community/<slug:slug>/', blog_detail, name='blog_detail'),
    
    # --- YORUM İŞLEMLERİ (OYLAMA / SİLME / DÜZENLEME) ---
    path('comment/<int:comment_id>/vote/<str:vote_type>/', vote_comment, name='vote_comment'),
    path('comment/delete/<int:comment_id>/', delete_comment, name='delete_comment'), # <-- YENİ
    path('comment/edit/<int:comment_id>/', edit_comment, name='edit_comment'),     # <-- YENİ
    # ---------------------------------------

    # --- GEÇİCİ 404 TEST LİNKİ ---
    path('test-404/', lambda request: render(request, 'core/404.html')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)