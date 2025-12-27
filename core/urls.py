# core/urls.py

from django.urls import path
from . import views  # Aynı klasördeki views.py'ı çağırıyoruz

urlpatterns = [
    # Dashboard (Anasayfa veya panel)
    path('', views.dashboard, name='dashboard'),  # Eğer dashboard view'ın varsa
    
    # Yeni eklediğimiz Review (Değerlendirme) kısmı
    path('add-review/<int:session_id>/', views.add_review, name='add_review'),

    # Diğer view'ların varsa buraya eklemelisin.
    # Örn: path('login/', views.login_view, name='login'),
]