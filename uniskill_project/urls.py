from django.contrib import admin
from django.urls import path
from core.views import (
    dashboard, register, logout_view, add_skill, 
    search_skills, request_session, complete_session, 
    add_review, admin_stats, inbox, send_message,
    CustomLoginView, approve_session_tutor, reject_session_tutor,
    cancel_session  # <--- YENİ EKLENEN
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', CustomLoginView.as_view(), name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    path('add-skill/', add_skill, name='add_skill'),
    path('search/', search_skills, name='search_skills'),
    path('request-session/<int:skill_id>/', request_session, name='request_session'),
    path('complete/<int:session_id>/', complete_session, name='complete_session'),
    path('review/<int:session_id>/', add_review, name='add_review'),
    path('admin-stats/', admin_stats, name='admin_stats'),
    path('inbox/', inbox, name='inbox'),
    path('send-message/<int:recipient_id>/', send_message, name='send_message'),
    path('approve-session/<int:session_id>/', approve_session_tutor, name='approve_session_tutor'),
    path('reject-session/<int:session_id>/', reject_session_tutor, name='reject_session_tutor'),
    
    # --- YENİ İPTAL LİNKİ ---
    path('cancel-session/<int:session_id>/', cancel_session, name='cancel_session'),
]