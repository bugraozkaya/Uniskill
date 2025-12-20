from django.contrib import admin
from django.urls import path

# Tek ve düzenli import bloğu (Tüm fonksiyonlar burada)
from core.views import (
    dashboard, register, logout_view, add_skill, 
    search_skills, request_session, complete_session, 
    add_review, admin_stats, inbox, send_message,
    CustomLoginView # <-- YENİ GÜVENLİK ÖZELLİĞİ
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- 1. GİRİŞ VE ANA SAYFA ---
    # Artık siteye girince direkt güvenli giriş ekranı açılacak
    path('', CustomLoginView.as_view(), name='login'),
    
    # Giriş yaptıktan sonra yönlendirilecek sayfa
    path('dashboard/', dashboard, name='dashboard'),

    # --- 2. HESAP İŞLEMLERİ ---
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),

    # --- 3. YETENEK & PAZAR YERİ ---
    path('add-skill/', add_skill, name='add_skill'),
    path('search/', search_skills, name='search_skills'),

    # --- 4. DERS YÖNETİMİ ---
    path('request-session/<int:skill_id>/', request_session, name='request_session'),
    path('complete/<int:session_id>/', complete_session, name='complete_session'),
    path('review/<int:session_id>/', add_review, name='add_review'),

    # --- 5. EKSTRA ÖZELLİKLER ---
    path('admin-stats/', admin_stats, name='admin_stats'), # İstatistikler
    path('inbox/', inbox, name='inbox'),                   # Gelen Kutusu
    path('send-message/<int:recipient_id>/', send_message, name='send_message'), # Mesaj Gönder
]