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

# Ana Sayfa (Dashboard)
@login_required
def dashboard(request):
    if request.user.status == 'pending':
        return render(request, 'core/pending.html')

    # 1. Benim yeteneklerim
    my_skills = UserSkill.objects.filter(user=request.user)
    
    # 2. GELECEK DERSLER (Scheduled)
    my_sessions = Session.objects.filter(
        Q(student=request.user) | Q(tutor=request.user),
        status='scheduled'
    ).order_by('date')

    # 3. GEÇMİŞ / TAMAMLANAN DERSLER (EKSİK OLAN KISIM BURASIYDI)
    past_sessions = Session.objects.filter(
        Q(student=request.user) | Q(tutor=request.user),
        status='completed'
    ).order_by('-date')

    context = {
        'ad': request.user.first_name,
        'soyad': request.user.last_name,
        'bakiye': request.user.balance,
        'status': request.user.get_status_display(),
        'bolum': request.user.department,
        'my_skills': my_skills,
        'my_sessions': my_sessions,
        'past_sessions': past_sessions,  # <-- HTML'e bu veriyi göndermiyorduk
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


@login_required
def request_session(request, skill_id):
    # 1. Hangi yetenek isteniyor onu bul (UserSkill tablosundan)
    target_skill = get_object_or_404(UserSkill, id=skill_id)
    tutor = target_skill.user # Dersi verecek hoca
    student = request.user    # Dersi alacak öğrenci

    if request.method == 'POST':
        form = DersTalepFormu(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.student = student
            session.tutor = tutor
            session.skill = target_skill.skill
            
            # --- KURAL 1: Kendi kendine ders alamazsın ---
            if student == tutor:
                messages.error(request, "Kendinden ders alamazsın!")
                return redirect('search_skills')

            # --- KURAL 2: Bakiye Yetersizse ---
            if student.balance < session.duration:
                messages.error(request, f"Yetersiz Bakiye! {session.duration} saat için kredin yok.")
                return render(request, 'core/request_session.html', {'form': form, 'target_skill': target_skill})

            # --- KURAL 3: TRANSFER İŞLEMİ (TRANSACTION) ---
            # Öğrenciden düş, hocaya ekle
            student.balance -= session.duration
            tutor.balance += session.duration
            
            # Veritabanına kaydet (Atomik işlem gibi)
            student.save()
            tutor.save()
            session.save()
            
            messages.success(request, f"Ders başarıyla ayarlandı! {session.duration} saat bakiyenizden düştü.")
            return redirect('dashboard')
    else:
        form = DersTalepFormu()

    return render(request, 'core/request_session.html', {'form': form, 'target_skill': target_skill})


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

class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def dispatch(self, request, *args, **kwargs):
        # 1. BLOK KONTROLÜ (Sayfa açılırken)
        ip = self.get_client_ip(request)
        block_expiry = cache.get(f'blocked_{ip}') # Artık burada "Bitiş Zamanı" (timestamp) var
        
        if block_expiry:
            # Kalan süreyi hesapla
            remaining = int(block_expiry - time.time())
            
            if remaining > 0:
                # Kullanıcıya kalan süreyi gönderiyoruz (wait_time)
                return render(request, self.template_name, {
                    'form': self.get_form(),
                    'wait_time': remaining  # <-- HTML'e giden saniye bilgisi
                })
            
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        ip = self.get_client_ip(self.request)
        
        # DİKKAT: Anahtar ismini değiştirdik (v2 yaptık). 
        # Bu sayede eski hafıza silinmiş gibi tertemiz başlayacak.
        fail_key = f'login_fail_v2_{ip}' 
        
        current_count = cache.get(fail_key, 0)
        new_count = current_count + 1
        
        # --- AJAN KODU: Terminale Bak ---
        print(f"👀 [DEBUG] IP: {ip} | Yeni Sayaç: {new_count}")
        # -------------------------------

        cache.set(fail_key, new_count, 60) 
        
        remaining = 3 - new_count
        context = self.get_context_data(form=form)
        
        if new_count >= 3:
            # LİMİT AŞILDI
            expiry_time = time.time() + 30
            cache.set(f'blocked_{ip}', expiry_time, 30)
            context['wait_time'] = 30 
            messages.error(self.request, f"⛔ {new_count}. hatalı deneme! 30 saniye engellendiniz.")
        else:
            # UYARI
            messages.warning(self.request, f"⚠️ Hatalı şifre! ({new_count}. Deneme) - Kalan hakkınız: {remaining}")
            
        return self.render_to_response(context)

    def form_valid(self, form):
        ip = self.get_client_ip(self.request)
        # Buradaki anahtarı da v2 yapıyoruz ki başarılı girince sıfırlansın
        cache.delete(f'login_fail_v2_{ip}') 
        cache.delete(f'blocked_{ip}')
        return super().form_valid(form)