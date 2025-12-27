from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# View fonksiyonlarını çağırıyoruz
from core.views import (
    dashboard, register, logout_view, add_skill, 
    search_skills, request_session, complete_session, 
    add_review, admin_stats, inbox, send_message,
    CustomLoginView, approve_session_tutor, reject_session_tutor,
    meeting_room, cancel_session,
    new_chat, chat_detail
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # ---------------------------------------------------------
    # 1. KRİTİK DÜZELTME: Giriş ve Ana Sayfa Ayrımı
    # ---------------------------------------------------------
    
    # Ana Sayfa (Siteye girince direkt Dashboard açılsın)
    path('', dashboard, name='dashboard'),

    # Giriş Sayfası (Mutlaka 'login/' olmalı, boş bırakma!)
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # ---------------------------------------------------------

    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Yetenek İşlemleri
    path('add-skill/', add_skill, name='add_skill'),
    path('search/', search_skills, name='search_skills'),
    
    # Ders/Session İşlemleri
    path('request-session/<int:skill_id>/', request_session, name='request_session'),
    path('complete/<int:session_id>/', complete_session, name='complete_session'),
    
    # Review (Yorum) İşlemi - Tek bir tane tanımladık
    path('add-review/<int:session_id>/', add_review, name='add_review'),

    # Onaylama/Reddetme/İptal
    path('approve-session/<int:session_id>/', approve_session_tutor, name='approve_session_tutor'),
    path('reject-session/<int:session_id>/', reject_session_tutor, name='reject_session_tutor'),
    path('cancel-session/<int:session_id>/', cancel_session, name='cancel_session'),
    
    # Toplantı Odası
    path('meeting/<int:session_id>/', meeting_room, name='meeting_room'),
    
    # Admin İstatistikleri
    path('admin-stats/', admin_stats, name='admin_stats'),

    # --- MESAJLAŞMA SİSTEMİ ---
    path('inbox/', inbox, name='inbox'),
    path('send-message/<int:recipient_id>/', send_message, name='send_message'),
    path('chat/<int:user_id>/', chat_detail, name='chat_detail'), 
    path('new-chat/', new_chat, name='new_chat'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)