from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db import models, transaction  # transaction'ı ekledim (aşağıda lazım olacak)
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.cache import cache
from django.utils.dateparse import parse_datetime
from .forms import UserUpdateForm, ProfileUpdateForm
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from .forms import OgrenciKayitFormu, UserUpdateForm, ProfileUpdateForm, UserSkillForm, DersTalepFormu
from .forms import CustomUserCreationForm, UserUpdateForm, ProfileUpdateForm
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404 # get_object_or_404 buraya eklendi
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Session, User, UserSkill
User = get_user_model()
# --- FORMLAR ---
from .forms import (
    CustomUserCreationForm, 
    DersTalepFormu, 
    DegerlendirmeFormu, 
    MesajFormu,
    OgrenciKayitFormu, 
    UserUpdateForm, 
    ProfileUpdateForm, 
    UserSkillForm,      # Yetenek ekleme hatasını çözer
    
    
)

# --- MODELLER ---
from .models import (
    User, 
    Skill, 
    UserSkill, 
    Session, 
    Review, 
    Message, 
    Profile,
    CATEGORY_CHOICES
)


# Ana Sayfa (Dashboard)
# core/views.py içinde dashboard fonksiyonunun YENİ HALİ

# core/views.py

# core/views.py

# core/views.py dosyasındaki dashboard fonksiyonunun DOĞRU HALİ

# core/views.py

# En üste bu importun olduğundan emin ol:
from django.db.models import Avg, Q

@login_required
def dashboard(request):
    # Profil yoksa oluştur
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # 1. Dersleri Çek
    all_sessions = Session.objects.filter(
        Q(student=request.user) | Q(tutor=request.user)
    ).order_by('date')

    my_sessions = []
    past_sessions = []

    for session in all_sessions:
        if session.status in ['cancelled', 'completed'] or session.is_expired:
            past_sessions.append(session)
        else:
            my_sessions.append(session)
    
    past_sessions.reverse() 

    my_skills = UserSkill.objects.filter(user=request.user)

    # --- GEÇMİŞ DERSLER İÇİN YORUM KONTROLÜ ---
    for session in past_sessions:
        check_review = Review.objects.filter(session=session).exists()
        session.is_rated = check_review

    # --- YENİ EKLENEN İSTATİSTİKLER (ADIM 1) ---
    
    # 1. Hoca olarak verip tamamladığı ders sayısı
    lessons_given_count = Session.objects.filter(tutor=request.user, status='completed').count()
    
    # 2. Hoca olarak aldığı yorumların ortalaması
    my_rating = Review.objects.filter(session__tutor=request.user).aggregate(Avg('rating'))['rating__avg']
    
    # -------------------------------------------

    context = {
        'profile': profile,
        'my_sessions': my_sessions,     # Düzeltildi (Çift tanımlama silindi)
        'past_sessions': past_sessions,
        'my_skills': my_skills,
        
        # Yeni verileri HTML'e gönderiyoruz:
        'lessons_given_count': lessons_given_count,
        'my_rating': my_rating,
    }
    
    return render(request, 'core/dashboard.html', context)

# core/views.py

from .forms import CustomUserCreationForm # Sadece bunu kullanacağız

from django.db import transaction

from django.db import transaction

from django.db import transaction

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid():
            try:
                # 1. Kullanıcıyı kaydet (Signals burada profili otomatik oluşturur)
                user = form.save()
                
                # 2. HATA ALMAMAK İÇİN: Yeni profil OLUŞTURMA, var olanı GETİR
                profile = user.profile 
                profile.department = form.cleaned_data.get('department')
                
                # 3. Referans Mantığı: Puanı Ekle
                ref_code = form.cleaned_data.get('used_referral')
                if ref_code:
                    # Kodu paylaşan kişiyi bul
                    referrer = Profile.objects.filter(referral_code=ref_code.strip()).first()
                    if referrer:
                        referrer.balance += 1 # +1 Saat Puan
                        referrer.save() # Veritabanına kesin yaz
                        profile.used_referral = ref_code # Kiminle geldiğini kaydet
                
                # 4. Profildeki değişiklikleri (bölüm vb.) kaydet
                profile.save() 
                
                messages.success(request, 'Kayıt başarılı! Şimdi giriş yapabilirsiniz.')
                return redirect('login') # BAŞARILI OLUNCA GİRİŞE YÖNLENDİRİR
                
            except Exception as e:
                # Eğer hala IntegrityError alırsan hatayı burada yakalarız
                messages.error(request, f"Kayıt sırasında bir sorun oluştu: {e}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})
    
# ÇIKIŞ YAPMA FONKSİYONU
def logout_view(request):
    logout(request)
    return redirect('login')


# core/views.py içindeki add_skill fonksiyonu

@login_required
def add_skill(request):
    if request.method == 'POST':
        form = UserSkillForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Kaydı oluştur ama henüz DB'ye yazma (skill ve description burada otomatik set edilir)
            user_skill = form.save(commit=False)
            
            # 2. Eksik olan kullanıcıyı ekle
            user_skill.user = request.user
            
            # 3. Şimdi her şey tamamsa kaydet
            user_skill.save()
            
            messages.success(request, f"'{user_skill.skill.name}' yeteneği başarıyla eklendi! Admin onayı bekleniyor.")
            return redirect('dashboard')
    else:
        form = UserSkillForm()

    return render(request, 'core/add_skill.html', {'form': form})
# core/views.py içindeki search_skills fonksiyonu

# core/views.py içindeki search_skills fonksiyonunun FİNAL HALİ

# Gerekli importları en tepeye eklediğinden emin ol:
# from .models import UserSkill, CATEGORY_CHOICES
# from django.db.models import Q

# core/views.py

from django.shortcuts import render
from .models import UserSkill, CATEGORY_CHOICES
# Q'nun yanına Avg (Average/Ortalama) fonksiyonunu eklemeyi UNUTMA
from django.db.models import Q, Avg 

def search_skills(request):
    # 1. ADIM: Onaylı yetenekleri çek VE her biri için Ortalamayı Hesapla (Annotate)
    # 'session__review__rating': Bu ilişki zincirini takip ederek puanları bulur.
    skills = UserSkill.objects.filter(is_approved=True).annotate(
        average_rating=Avg('user__given_sessions__review__rating')
    )

    query = request.GET.get('q')
    category_code = request.GET.get('category')
    min_rating = request.GET.get('rating') # YENİ: URL'den puan parametresini alıyoruz

    # 2. ADIM: Kelime Arama
    if query:
        skills = skills.filter(
            Q(skill__name__icontains=query) | 
            Q(skill__description__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query)
        )

    # 3. ADIM: Kategori Filtreleme
    if category_code and category_code != 'all':
        skills = skills.filter(skill__category=category_code)

    # 4. ADIM: PUAN FİLTRELEME (YENİ KISIM)
    if min_rating:
        # average_rating (hesapladığımız alan) >= seçilen puan
        skills = skills.filter(average_rating__gte=int(min_rating))

    # SIRALAMA: En yüksek puanlılar en üstte görünsün, puanı olmayanlar altta kalsın
    skills = skills.order_by('-average_rating', '-id')

    context = {
        'skills': skills,
        'categories': CATEGORY_CHOICES,
        # Formda kullanıcının seçtiği değerler kaybolmasın diye geri gönderiyoruz:
        'selected_category': category_code,
        'selected_rating': min_rating,
        'query': query
    }
    return render(request, 'core/search_skills.html', context)

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
    # Yazım hatası düzeltildi
    session = get_object_or_404(Session, id=session_id)
    
    if session.status == 'approved':
        # 1. Ders durumunu kapat
        session.status = 'completed'
        session.save()
        
        # 2. Bakiye transferi (Profile modeli üzerinden)
        # Öğrencinin profilini al ve düşüş yap
        student_profile = session.student.profile
        student_profile.balance -= session.duration
        student_profile.save()
        
        # Hocanın profilini al ve ekleme yap
        tutor_profile = session.tutor.profile
        tutor_profile.balance += session.duration
        tutor_profile.save()
        
        messages.success(request, f"Ders tamamlandı. {session.duration} saat transfer edildi.")
    
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
    session = get_object_or_404(Session, id=session_id)
    
    # Sadece dersin hocası onaylayabilir
    if request.user == session.tutor:
        session.status = 'approved'
        session.save()
        messages.success(request, "Ders talebini onayladınız!")
    
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



# core/views.py dosyasına ekle

# core/views.py dosyasındaki meeting_room fonksiyonunun YENİ HALİ

@login_required
def meeting_room(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    # --- DÜZELTME BAŞLANGIÇ ---
    # Konum bilgisi 'Skill' modelinde değil, 'UserSkill' modelinde.
    # Bu yüzden hocanın (tutor) ve yeteneğin (skill) eşleştiği kaydı buluyoruz.
    user_skill = UserSkill.objects.filter(user=session.tutor, skill=session.skill).first()

    # Eğer hoca bu yeteneği silmişse veya kayıt yoksa varsayılan 'online' olsun (Hata vermesin)
    location = user_skill.location if user_skill else 'online'
    # --- DÜZELTME BİTİŞ ---

    # Güvenlik: Sadece o dersin hocası veya öğrencisi girebilir
    if request.user != session.student and request.user != session.tutor:
        messages.error(request, "Bu toplantıya katılma yetkiniz yok.")
        return redirect('dashboard')
        
    # ARTIK KONTROLÜ 'location' DEĞİŞKENİ İLE YAPIYORUZ
    if location != 'online' or session.status != 'approved':
        messages.error(request, "Bu ders için aktif bir online görüşme bulunmuyor.")
        return redirect('dashboard')

    # Oda ismini benzersiz yapıyoruz
    room_name = f"uniskill_session_{session.id}"
    if session.is_expired:
        messages.error(request, "Bu dersin süresi dolduğu için katılamazsınız.")
        return redirect('dashboard')
    
    context = {
        'room_name': room_name,
        'session': session,
        'user_display_name': request.user.get_full_name() or request.user.username
    }
    return render(request, 'core/meeting_room.html', context)


@login_required
def new_chat(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        
        try:
            # Kullanıcıyı veritabanında ara
            recipient = User.objects.get(username=username)
            
            # Kendine mesaj atmasını engelle
            if recipient == request.user:
                messages.warning(request, "Kendinize mesaj atamazsınız.")
                return redirect('inbox')
                
            # Bulursa direkt sohbet sayfasına yönlendir
            return redirect('chat_detail', user_id=recipient.id)
            
        except User.DoesNotExist:
            # Bulamazsa hata ver
            messages.error(request, "Bu kullanıcı adına sahip kimse bulunamadı.")
            return redirect('inbox')
            
    return redirect('inbox')


# --- MESAJLAŞMA SİSTEMİ ---

@login_required
def inbox(request):
    # Kullanıcının dahil olduğu mesajları al
    messages_qs = Message.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).order_by('-created_at')

    conversations = []
    seen_users = set()

    for msg in messages_qs:
        other_user = msg.recipient if msg.sender == request.user else msg.sender
        if other_user not in seen_users:
            conversations.append({
                'user': other_user,
                'last_message': msg
            })
            seen_users.add(other_user)

    return render(request, 'core/inbox.html', {'conversations': conversations})

@login_required
def chat_detail(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # İki kişi arasındaki tüm mesajları çek
    messages_qs = Message.objects.filter(
        (Q(sender=request.user) & Q(recipient=other_user)) |
        (Q(sender=other_user) & Q(recipient=request.user))
    ).order_by('created_at')

    # Okundu olarak işaretle
    unread = messages_qs.filter(recipient=request.user, is_read=False)
    unread.update(is_read=True)

    if request.method == 'POST':
        form = MesajFormu(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.recipient = other_user
            msg.save()
            return redirect('chat_detail', user_id=user_id)
    else:
        form = MesajFormu()

    context = {
        'other_user': other_user,
        'messages': messages_qs,
        'form': form
    }
    return render(request, 'core/chat.html', context)

@login_required
def send_message(request, recipient_id):
    # Ders Ara sayfasından gelen istekleri chat'e yönlendir
    return redirect('chat_detail', user_id=recipient_id)

@login_required
def new_chat(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            recipient = User.objects.get(username=username)
            if recipient == request.user:
                messages.warning(request, "Kendinize mesaj atamazsınız.")
                return redirect('inbox')
            return redirect('chat_detail', user_id=recipient.id)
        except User.DoesNotExist:
            messages.error(request, "Kullanıcı bulunamadı.")
            return redirect('inbox')
    return redirect('inbox')

# core/views.py

def public_profile(request, user_id):
    # 1. Hocayı (Kullanıcıyı) buluyoruz
    tutor = get_object_or_404(User, id=user_id)
    
    # 2. Hocanın profil detaylarını al (Bölüm vs. için)
    # Eğer profil yoksa hata vermemesi için get_or_create veya try-except kullanılabilir
    # Ama senin sisteminde dashboard'a girince oluşuyor, biz yine de güvenli gidelim.
    try:
        profile = tutor.profile
    except:
        profile = None

    # 3. Hocanın verdiği onaylı dersleri çek
    skills = UserSkill.objects.filter(user=tutor, is_approved=True)

    # 4. YORUMLARI ÇEKME (KRİTİK KISIM)
    # Session tablosu üzerinden Tutor'u bu kişi olan derslerin yorumlarını buluyoruz.
    reviews = Review.objects.filter(session__tutor=tutor).order_by('-created_at')

    # 5. İstatistikler
    total_sessions = Session.objects.filter(tutor=tutor, status='completed').count()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    context = {
        'tutor': tutor,
        'profile': profile,
        'skills': skills,
        'reviews': reviews,
        'total_sessions': total_sessions,
        'average_rating': average_rating
    }
    return render(request, 'core/public_profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('dashboard')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'core/edit_profile.html', {'u_form': u_form, 'p_form': p_form})