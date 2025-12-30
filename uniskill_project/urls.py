from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core import views

# View fonksiyonlarını import ediyoruz
from core.views import (
    landing_page, leaderboard, # <--- LEADERBOARD EKLENDİ
    dashboard, register, logout_view, add_skill, 
    search_skills, request_session, complete_session, 
    add_review, admin_stats, inbox, send_message,
    CustomLoginView, approve_session_tutor, reject_session_tutor,
    meeting_room, cancel_session,
    new_chat, chat_detail,
    public_profile, edit_profile,
    mark_notification_as_read
)

urlpatterns = [
    # --- GÜVENLİK ---
    path('uniskill-yonetim-2025/', admin.site.urls),
    path('admin/', lambda request: redirect('/')),

    # Ana Sayfa & Dashboard
    path('', landing_page, name='landing_page'),
    path('dashboard/', dashboard, name='dashboard'),

    # --- YENİ EKLENEN: LEADERBOARD ---
    path('leaderboard/', leaderboard, name='leaderboard'),
    # ---------------------------------

    # Kimlik Doğrulama
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    
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

    # Mesajlaşma Sistemi
    path('inbox/', inbox, name='inbox'),
    path('send-message/<int:recipient_id>/', send_message, name='send_message'),
    path('chat/<int:user_id>/', chat_detail, name='chat_detail'), 
    path('new-chat/', new_chat, name='new_chat'),

    # Bildirim Sistemi
    path('notification/read/<int:notification_id>/', mark_notification_as_read, name='mark_notification_as_read'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)