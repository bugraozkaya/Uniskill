from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import OgrenciKayitFormu
from .forms import OgrenciKayitFormu, YetenekEkleFormu # <-- YetenekEkleFormu'nu ekledik
from .models import Skill # <-- Skill modelini de ekle
from .models import UserSkill
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib import messages # Hata mesajı göstermek için
from .forms import DersTalepFormu
from .models import Session, UserSkill # Session ve UserSkill modellerini import et
from .models import Review
from .forms import DegerlendirmeFormu
from .models import User, UserSkill, Session, Review
from django.db.models import Count, Sum
from .models import Message
from .forms import MesajFormu
from django.contrib.auth.views import LoginView
from django.core.cache import cache # Hafıza (RAM) işlemleri için
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Session, UserSkill
from django.db import models  # <-- Bunu dosyanın en tepesine ekle!

# Ana Sayfa (Dashboard)
@login_required
def dashboard(request):
    now = timezone.now()
    
    # 1. Kullanıcının ÖĞRENCİ veya HOCA olduğu GELECEK dersler
    # (Hem onaylanmışları hem de onay bekleyenleri getiriyoruz)
    my_sessions = Session.objects.filter(
        # Ya öğrenciyim ya hocayım
        (models.Q(student=request.user) | models.Q(tutor=request.user)),
        # Ders tarihi geçmemiş (Gelecek)
        date__gte=now
    ).exclude(
        status='cancelled'  # İptal edilenleri gösterme
    ).order_by('date')      # Tarihe göre sırala (en yakın en üstte)

    # 2. Geçmiş Dersler (Tarihi geçmiş veya tamamlanmış)
    past_sessions = Session.objects.filter(
        (models.Q(student=request.user) | models.Q(tutor=request.user)),
        date__lt=now # Tarihi eskide kalmış
    ).order_by('-date')

    # 3. Öğretebileceğim yetenekler listesi
    my_skills = UserSkill.objects.filter(user=request.user)

    # Kullanıcının bakiyesini al (Profile'dan)
    # (Hata almamak için güvenli erişim)
    try:
        balance = request.user.profile.balance
    except:
        balance = 0

    context = {
        'my_sessions': my_sessions,
        'past_sessions': past_sessions,
        'my_skills': my_skills,
        'bakiye': balance,
        'bolum': 'Bilgisayar Mühendisliği' # Burayı dinamik yapabilirsin
    }
    
    return render(request, 'core/dashboard.html', context)

def register(request):
    if request.method == 'POST':
        form = OgrenciKayitFormu(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # --- REFERANS SİSTEMİ EKLENTİSİ ---
            ref_code = form.cleaned_data.get('referral_code')
            if ref_code:
                # Davet eden kullanıcıyı bul ve kaydet
                inviter = User.objects.get(username=ref_code)
                user.invited_by = inviter
            # ----------------------------------
            
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = OgrenciKayitFormu()
    return render(request, 'core/register.html', {'form': form})

# ÇIKIŞ YAPMA FONKSİYONU
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def add_skill(request):
    if request.method == 'POST':
        form = YetenekEkleFormu(request.POST)
        if form.is_valid():
            # 1. Formdan verileri al
            kategori = form.cleaned_data['category']
            yetenek_adi = form.cleaned_data['skill_name']
            aciklama = form.cleaned_data['description']

            # 2. Önce bu isimde bir yetenek var mı diye bak (Yetenek Havuzu)
            # Varsa onu al, yoksa yeni oluştur.
            skill_obj, created = Skill.objects.get_or_create(
                name=yetenek_adi,
                category=kategori,
                defaults={'description': aciklama}
            )

            # 3. Bu yeteneği, giriş yapan kullanıcıya bağla (UserSkill Tablosu)
            UserSkill.objects.create(
                user=request.user,
                skill=skill_obj
            )
            
            return redirect('dashboard')
    else:
        form = YetenekEkleFormu()

    return render(request, 'core/add_skill.html', {'form': form})


@login_required
def search_skills(request):
    # 1. Varsayılan olarak: Kendi ilanlarım HARİÇ tüm ilanları getir
    skills = UserSkill.objects.exclude(user=request.user)
    
    # 2. Arama yapıldı mı? (Kullanıcı arama kutusuna bir şey yazdı mı?)
    query = request.GET.get('q') # URL'den 'q' parametresini al
    if query:
        # Hem yetenek adında hem de açıklamasında ara
        skills = skills.filter(
            Q(skill__name__icontains=query) | 
            Q(skill__description__icontains=query) |
            Q(skill__category__name__icontains=query)
        )
    
    return render(request, 'core/search_skills.html', {'skills': skills})


# core/views.py içindeki request_session fonksiyonunun EN GÜNCEL HALİ:

# core/views.py içindeki request_session fonksiyonu

@login_required
def request_session(request, skill_id):
    # Bu 'skill' değişkeni aslında bir İLAN (UserSkill)
    skill = get_object_or_404(UserSkill, id=skill_id)
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        duration = request.POST.get('duration')

        from django.utils.dateparse import parse_datetime
        date_obj = parse_datetime(date_str)

        new_session = Session(
            student=request.user,
            tutor=skill.user,
            
            # --- HATAYI ÇÖZEN SATIR BURASI ---
            # skill=skill YERİNE skill=skill.skill YAZIYORUZ
            skill=skill.skill, 
            # ---------------------------------
            
            date=date_obj,
            duration=duration,
            status='pending'
        )
        new_session.save()
        
        messages.success(request, "Ders talebiniz alındı! Admin onayından sonra dersiniz başlayacaktır.")
        return redirect('dashboard')
    
    return render(request, 'core/session_request.html', {'skill': skill})

@login_required
def complete_session(request, session_id):
    # Sadece dersin Hocası veya Öğrencisi dersi "Tamamlandı" işaretleyebilir
    session = get_object_or_404(Session, id=session_id)
    
    if request.user == session.student or request.user == session.tutor:
        session.status = 'completed'
        session.save()
        messages.success(request, "Ders tamamlandı olarak işaretlendi.")
    
    return redirect('dashboard')

@login_required
def add_review(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    # GÜVENLİK KONTROLÜ:
    # 1. Sadece dersi alan öğrenci yorum yapabilir.
    if request.user != session.student:
        messages.error(request, "Sadece dersi alan öğrenci yorum yapabilir.")
        return redirect('dashboard')
        
    # 2. Sadece tamamlanmış derslere yorum yapılabilir.
    if session.status != 'completed':
        messages.error(request, "Henüz tamamlanmamış bir derse yorum yapamazsınız.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = DegerlendirmeFormu(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.session = session # Yorumu derse bağla (Weak Entity İlişkisi)
            review.save()
            messages.success(request, "Değerlendirmeniz kaydedildi! Teşekkürler.")
            return redirect('dashboard')
    else:
        form = DegerlendirmeFormu()

    return render(request, 'core/add_review.html', {'form': form, 'session': session})


@login_required
def search_skills(request):
    # 1. Başlangıç: Kendi ilanlarım HARİÇ hepsini getir
    skills = UserSkill.objects.exclude(user=request.user)
    
    # 2. Kelime Arama (Database tarafında yapılır)
    query = request.GET.get('q')
    if query:
        skills = skills.filter(
            Q(skill__name__icontains=query) | 
            Q(skill__description__icontains=query) |
            Q(skill__category__name__icontains=query)
        )
    
    # --- YENİ KISIM: PUAN FİLTRELEME ---
    # Not: average_rating veritabanında olmadığı için Python tarafında filtreliyoruz
    rating_filter = request.GET.get('rating')
    
    if rating_filter:
        try:
            min_rating = int(rating_filter)
            # Python List Comprehension ile filtrele:
            # "Eğer hocanın puanı seçilen puandan büyükse listeye al"
            skills = [s for s in skills if s.user.average_rating >= min_rating]
        except ValueError:
            pass # Eğer url ile oynayıp harf yazarlarsa hata vermesin, geçsin.
            
    return render(request, 'core/search_skills.html', {'skills': skills})


@login_required
def admin_stats(request):
    # GÜVENLİK: Sadece Admin (Superuser) girebilir
    if not request.user.is_superuser:
        messages.error(request, "Bu sayfaya sadece yöneticiler girebilir!")
        return redirect('dashboard')

    # 1. GENEL KART VERİLERİ
    total_users = User.objects.count()
    total_skills = UserSkill.objects.count()
    # Tamamlanan derslerin toplam saati (None gelirse 0 yap)
    total_hours = Session.objects.filter(status='completed').aggregate(Sum('duration'))['duration__sum'] or 0
    total_sessions_count = Session.objects.filter(status='completed').count()

    # 2. PASTA GRAFİK (PIE CHART): Hangi kategoride kaç ders talep edilmiş?
    # Session -> Skill -> Category ilişkisini takip ediyoruz
    cat_data = Session.objects.values('skill__category__name').annotate(total=Count('id')).order_by('-total')
    
    cat_labels = [item['skill__category__name'] for item in cat_data] # İsimler (Yazılım, Müzik vs)
    cat_counts = [item['total'] for item in cat_data]                 # Sayılar (5, 3, 1...)

    # 3. ÇUBUK GRAFİK (BAR CHART): En Çok Ders Alan İlk 5 Öğrenci
    student_data = Session.objects.filter(status='completed').values('student__username').annotate(total=Count('id')).order_by('-total')[:5]
    
    student_labels = [item['student__username'] for item in student_data]
    student_counts = [item['total'] for item in student_data]

    context = {
        'total_users': total_users,
        'total_skills': total_skills,
        'total_hours': total_hours,
        'total_sessions_count': total_sessions_count,
        'cat_labels': cat_labels,
        'cat_counts': cat_counts,
        'student_labels': student_labels,
        'student_counts': student_counts,
    }

    return render(request, 'core/admin_stats.html', context)

@login_required
def inbox(request):
    # Bana gelen mesajları al, en yeniden eskiye sırala
    messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Okunmamışları 'okundu' yap (İsteğe bağlı, basitlik için hepsini okundu sayabiliriz sayfayı açınca)
    # messages.filter(is_read=False).update(is_read=True) 
    
    return render(request, 'core/inbox.html', {'messages': messages})

@login_required
def send_message(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)
    
    if request.method == 'POST':
        form = MesajFormu(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.recipient = recipient
            msg.save()
            messages.success(request, "Mesajınız gönderildi!")
            return redirect('dashboard')
    else:
        form = MesajFormu()
        
    return render(request, 'core/send_message.html', {'form': form, 'recipient': recipient})
# core/views.py dosyasındaki CustomLoginView sınıfının GÜNCEL HALİ

# core/views.py
import time  # <-- EN ÜSTE BUNU EKLEMEYİ UNUTMA
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.contrib import messages

# core/views.py

from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.core.cache import cache
import time

class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    # --- YARDIMCI FONKSİYON: IP ADRESİNİ BUL ---
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    # --- 1. GET: SAYFA YÜKLENİRKEN ENGEL KONTROLÜ ---
    def get(self, request, *args, **kwargs):
        ip = self.get_client_ip(request)
        expiry_time = cache.get(f'blocked_{ip}')
        
        if expiry_time:
            remaining = int(expiry_time - time.time())
            if remaining > 0:
                context = self.get_context_data()
                context['wait_time'] = remaining
                messages.error(request, f"⛔ Çok fazla deneme yaptınız. {remaining} saniye bekleyin.")
                return self.render_to_response(context)
        
        return super().get(request, *args, **kwargs)

    # --- 2. POST: FORM GÖNDERİLİNCE ---
    def post(self, request, *args, **kwargs):
        ip = self.get_client_ip(request)
        
        # Eğer IP zaten engelliyse işlemi reddet
        if cache.get(f'blocked_{ip}'):
            return self.render_to_response(self.get_context_data())

        return super().post(request, *args, **kwargs)

    # --- 3. BAŞARISIZ GİRİŞ (ŞİFRE YANLIŞSA) ---
    def form_invalid(self, form):
        ip = self.get_client_ip(self.request)
        fail_key = f'login_fail_v2_{ip}'
        
        current_count = cache.get(fail_key, 0)
        new_count = current_count + 1
        
        print(f"👀 [DEBUG] IP: {ip} | Yeni Sayaç: {new_count}")

        cache.set(fail_key, new_count, 60) # Sayaç 60 saniye hafızada kalsın
        
        remaining = 3 - new_count
        context = self.get_context_data(form=form)
        
        if new_count >= 3:
            # LİMİT AŞILDI (30 Saniye Ban)
            expiry_time = time.time() + 30
            cache.set(f'blocked_{ip}', expiry_time, 30)
            context['wait_time'] = 30 
            messages.error(self.request, f"⛔ {new_count}. hatalı deneme! 30 saniye engellendiniz.")
        else:
            # UYARI
            messages.warning(self.request, f"⚠️ Hatalı şifre! ({new_count}. Deneme) - Kalan hakkınız: {remaining}")
            
        return self.render_to_response(context)

    # --- 4. BAŞARILI GİRİŞ (ŞİFRE DOĞRUYSA) ---
    def form_valid(self, form):
        user = form.get_user()
        ip = self.get_client_ip(self.request)

        # A) ADMIN ONAYI KONTROLÜ
        if not hasattr(user, 'profile') or user.profile.status != 'active':
            messages.error(self.request, "Hesabınız henüz Admin tarafından onaylanmadı. Lütfen bekleyiniz.")
            # Şifre doğru olsa bile girişi engelle (Sayaç artmasın ama giriş de yapmasın)
            return self.render_to_response(self.get_context_data(form=form))

        # B) HER ŞEY TAMAMSA SAYAÇLARI SIFIRLA VE GİRİŞ YAP
        cache.delete(f'login_fail_v2_{ip}') 
        cache.delete(f'blocked_{ip}')
        return super().form_valid(form)
    
@login_required
def approve_session_tutor(request, session_id):
    # Sadece o dersin HOCASI onaylayabilir
    session = get_object_or_404(Session, id=session_id, tutor=request.user)
    
    if session.status == 'pending_tutor':
        session.status = 'approved' # Son onay verildi!
        session.save()
        messages.success(request, "Dersi onayladınız! Ders artık aktif.")
    
    return redirect('dashboard')

@login_required
def reject_session_tutor(request, session_id):
    # Sadece o dersin HOCASI reddedebilir
    session = get_object_or_404(Session, id=session_id, tutor=request.user)
    
    if session.status == 'pending_tutor':
        session.status = 'cancelled'
        session.save()
        messages.warning(request, "Ders talebini reddettiniz.")
    
    return redirect('dashboard')
# core/views.py dosyasının EN ALTI

@login_required
def cancel_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    # Sadece dersin sahibi (öğrenci) veya hocası iptal edebilir
    if request.user == session.student or request.user == session.tutor:
        # Ders zaten bitmiş veya iptal edilmişse işlem yapma
        if session.status not in ['completed', 'cancelled']:
            session.status = 'cancelled'
            session.save()
            messages.info(request, "Ders iptal edildi.")
            
    return redirect('dashboard')