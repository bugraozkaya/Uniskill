import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.cache import cache
from django.utils.dateparse import parse_datetime
from django.conf import settings # Ayarlardan mail bilgilerini almak için

# --- YENİ IMPORTLAR (MAİL VE AKTİVASYON İÇİN) ---
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
# ------------------------------------------------

# --- MODELS ---
from .models import (
    Skill, 
    UserSkill, 
    Session, 
    Review, 
    Message, 
    Profile,
    Notification,
    CATEGORY_CHOICES
)

# --- FORMS ---
from .forms import (
    CustomUserCreationForm, 
    UserSkillForm, 
    DersTalepFormu, 
    MesajFormu, 
    UserUpdateForm, 
    ProfileUpdateForm, 
    DegerlendirmeFormu
)

User = get_user_model()

# ---------------------------------------------------------
# 1. USER OPERATIONS (Login, Register, Logout, Profile)
# ---------------------------------------------------------

class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request, *args, **kwargs):
        ip = self.get_client_ip(request)
        
        # 1. Check if IP is blocked (On initial page load)
        blocked_expiry = cache.get(f'user_blocked_{ip}')
        
        if blocked_expiry:
            remaining = int(blocked_expiry - time.time())
            if remaining > 0:
                return render(request, 'core/login_blocked.html', {
                    'remaining': remaining,
                    'next_url': '/login/' 
                })
        
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        ip = self.get_client_ip(self.request)
        fail_key = f'user_fail_{ip}'
        
        # Increment failed login count
        count = cache.get(fail_key, 0) + 1
        cache.set(fail_key, count, 300) # Keep attempts in memory for 5 minutes
        
        remaining_attempts = 3 - count

        # If 3 attempts reached, block
        if count >= 3:
            expiry_time = time.time() + 30
            cache.set(f'user_blocked_{ip}', expiry_time, 30)
            cache.delete(fail_key)
            
            return render(self.request, 'core/login_blocked.html', {
                'remaining': 30,
                'next_url': '/login/'
            })

        if remaining_attempts > 0:
            messages.error(self.request, f"⚠️ Incorrect password! (Attempt {count}) - Remaining attempts: {remaining_attempts}")

        return super().form_invalid(form)

    def form_valid(self, form):
        ip = self.get_client_ip(self.request)
        cache.delete(f'user_fail_{ip}')
        cache.delete(f'user_blocked_{ip}')
        
        user = form.get_user()
        if hasattr(user, 'profile') and user.profile.status != 'active':
             messages.error(self.request, "Your account has not been approved by the Admin yet.")
             return self.render_to_response(self.get_context_data(form=form))

        return super().form_valid(form) 

# --- GÜNCELLENEN REGISTER FONKSİYONU (AKTİVASYON MAİLİ İLE) ---
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST) 
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # HESABI PASİF OLARAK KAYDET
            user.save()

            # Profil oluşturma
            profile, created = Profile.objects.get_or_create(user=user)
            profile.department = form.cleaned_data.get('department')
            ref_code = form.cleaned_data.get('used_referral')
            if ref_code:
                profile.used_referral = ref_code.strip()
            profile.save()

            # --- E-POSTA DOĞRULAMA KISMI ---
            current_site = get_current_site(request)
            mail_subject = 'Activate your UniSkill account'
            message = render_to_string('core/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            try:
                email.send()
                messages.success(request, 'Please confirm your email address to complete the registration.')
            except:
                messages.error(request, 'Error sending confirmation email. Please try again later.')
                user.delete() # Mail gitmezse kullanıcıyı sil
                return redirect('register')
            
            return redirect('login') 
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'core/register.html', {'form': form})

# --- YENİ EKLENEN: AKTİVASYON FONKSİYONU ---
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True # HESABI AKTİF ET
        user.save()
        
        # Profil status'ünü de active yapalım (Admin onayı beklemeden giriş yapabilsin diye)
        # Eğer admin onayı zorunlu kalsın istiyorsan burayı silebilirsin.
        # user.profile.status = 'active'
        # user.profile.save()

        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('register')
# ---------------------------------------------

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('dashboard')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'core/edit_profile.html', {'u_form': u_form, 'p_form': p_form})

def public_profile(request, user_id):
    tutor = get_object_or_404(User, id=user_id)
    try:
        profile = tutor.profile
    except:
        profile = None

    skills = UserSkill.objects.filter(user=tutor, is_approved=True)
    reviews = Review.objects.filter(session__tutor=tutor).order_by('-created_at')
    
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


# ---------------------------------------------------------
# 2. DASHBOARD AND SESSION OPERATIONS
# ---------------------------------------------------------

@login_required
def dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
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

    for session in past_sessions:
        review = Review.objects.filter(session=session).first()
        if review:
            session.is_rated = True
            session.user_rating = review.rating
        else:
            session.is_rated = False
            session.user_rating = None

    received_reviews = Review.objects.filter(session__tutor=request.user).order_by('-created_at')

    lessons_given_count = Session.objects.filter(tutor=request.user, status='completed').count()
    my_rating = Review.objects.filter(session__tutor=request.user).aggregate(Avg('rating'))['rating__avg']

    context = {
        'profile': profile,
        'my_sessions': my_sessions,
        'past_sessions': past_sessions,
        'my_skills': my_skills,
        'lessons_given_count': lessons_given_count,
        'my_rating': my_rating,
        'received_reviews': received_reviews, 
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def add_skill(request):
    if request.method == 'POST':
        form = UserSkillForm(request.POST, request.FILES)
        if form.is_valid():
            user_skill = form.save(commit=False)
            user_skill.user = request.user
            user_skill.save()
            messages.success(request, f"'{user_skill.skill.name}' skill added successfully! Waiting for Admin approval.")
            return redirect('dashboard')
    else:
        form = UserSkillForm()

    return render(request, 'core/add_skill.html', {'form': form})

def search_skills(request):
    skills = UserSkill.objects.filter(is_approved=True).annotate(
        average_rating=Avg('user__given_sessions__review__rating')
    )

    query = request.GET.get('q')
    category_code = request.GET.get('category')
    min_rating = request.GET.get('rating')
    sort_by = request.GET.get('sort') 

    if query:
        skills = skills.filter(
            Q(skill__name__icontains=query) | 
            Q(skill__description__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query)
        )

    if category_code and category_code != 'all':
        skills = skills.filter(skill__category=category_code)

    if min_rating:
        skills = skills.filter(average_rating__gte=int(min_rating))

    if sort_by == 'rating':
        skills = skills.order_by('-average_rating', '-id')
    else:
        skills = skills.order_by('-id')

    context = {
        'skills': skills,
        'categories': CATEGORY_CHOICES,
        'selected_category': category_code,
        'selected_rating': min_rating,
        'selected_sort': sort_by,
        'query': query
    }
    return render(request, 'core/search_skills.html', context)

# --- GÜNCELLENEN REQUEST_SESSION (BİLDİRİM MAİLİ İLE) ---
@login_required
def request_session(request, skill_id):
    skill = get_object_or_404(UserSkill, id=skill_id)
    
    if request.method == 'POST':
        date_str = request.POST.get('date')
        duration = request.POST.get('duration')
        date_obj = parse_datetime(date_str)

        new_session = Session(
            student=request.user,
            tutor=skill.user,
            skill=skill.skill, 
            date=date_obj,
            duration=duration,
            status='pending'
        )
        new_session.save()

        # --- MAİL GÖNDERME KISMI (DERS TALEBİ) ---
        subject = f"UniSkill: New Session Request for {skill.skill.name}!"
        message = f"Hello {skill.user.first_name},\n\n{request.user.get_full_name()} wants to learn '{skill.skill.name}' from you.\n\nDate: {date_str}\nDuration: {duration} hours\n\nPlease log in to Approve or Reject this request: https://bugraozkaya.pythonanywhere.com/dashboard/"
        
        if skill.user.email:
            try:
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER, 
                    [skill.user.email],       
                    fail_silently=True,
                )
            except:
                pass 
        # -----------------------------------------

        messages.success(request, "Session request received! Waiting for approval.")
        return redirect('dashboard')
    
    return render(request, 'core/session_request.html', {'skill': skill})

@login_required
def complete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    if session.status == 'approved':
        session.status = 'completed'
        session.save()
        
        student_profile = session.student.profile
        student_profile.balance -= session.duration
        student_profile.save()
        
        tutor_profile = session.tutor.profile
        tutor_profile.balance += session.duration
        tutor_profile.save()
        
        messages.success(request, f"Session completed. {session.duration} hours transferred.")
    
    return redirect('dashboard')

@login_required
def approve_session_tutor(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user == session.tutor:
        session.status = 'approved'
        session.save()
        messages.success(request, "You approved the session request!")
    return redirect('dashboard')

@login_required
def reject_session_tutor(request, session_id):
    session = get_object_or_404(Session, id=session_id, tutor=request.user)
    if session.status == 'pending_tutor':
        session.status = 'cancelled'
        session.save()
        messages.warning(request, "You rejected the session request.")
    return redirect('dashboard')

@login_required
def cancel_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user == session.student or request.user == session.tutor:
        if session.status not in ['completed', 'cancelled']:
            session.status = 'cancelled'
            session.save()
            messages.info(request, "Session cancelled.")
    return redirect('dashboard')

@login_required
def add_review(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    
    if request.user != session.student:
        messages.error(request, "Only the student who took the session can leave a review.")
        return redirect('dashboard')
        
    if session.status != 'completed':
        messages.error(request, "You cannot review a session that is not completed.")
        return redirect('dashboard')

    if Review.objects.filter(session=session).exists():
        messages.warning(request, "You have already reviewed this session.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = DegerlendirmeFormu(request.POST) 
        if form.is_valid():
            review = form.save(commit=False)
            review.session = session
            review.save()
            messages.success(request, "Your review has been saved! Thank you.")
            return redirect('dashboard')
    else:
        form = DegerlendirmeFormu()

    return render(request, 'core/add_review.html', {'form': form, 'session': session})

@login_required
def meeting_room(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    user_skill = UserSkill.objects.filter(user=session.tutor, skill=session.skill).first()
    location = user_skill.location if user_skill else 'online'

    if request.user != session.student and request.user != session.tutor:
        messages.error(request, "You are not authorized to join this meeting.")
        return redirect('dashboard')
        
    if location != 'online' or session.status != 'approved':
        messages.error(request, "There is no active online meeting for this session.")
        return redirect('dashboard')

    if session.is_expired:
        messages.error(request, "You cannot join because the session time has expired.")
        return redirect('dashboard')
    
    room_name = f"uniskill_session_{session.id}"
    context = {
        'room_name': room_name,
        'session': session,
        'user_display_name': request.user.get_full_name() or request.user.username
    }
    return render(request, 'core/meeting_room.html', context)


# ---------------------------------------------------------
# 3. UNIFIED MESSAGING (WHATSAPP STYLE) & ADMIN
# ---------------------------------------------------------

@login_required
def messaging(request, user_id=None):
    """
    Hem kişi listesini (sol) hem de aktif sohbeti (sağ) yöneten tek fonksiyon.
    Resim gönderme özelliğini de destekler.
    """
    # 1. SOL TARAFTAKİ KİŞİ LİSTESİ
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
                'last_message': msg,
            })
            seen_users.add(other_user)

    # 2. SAĞ TARAFTAKİ AKTİF SOHBET
    active_user = None
    chat_messages = []
    
    if user_id:
        active_user = get_object_or_404(User, id=user_id)
        
        # Mesajları getir
        chat_messages = Message.objects.filter(
            (Q(sender=request.user) & Q(recipient=active_user)) |
            (Q(sender=active_user) & Q(recipient=request.user))
        ).order_by('created_at')

        # Okundu yap
        unread = chat_messages.filter(recipient=request.user, is_read=False)
        unread.update(is_read=True)

        # --- YENİ EKLENEN: RESİM DESTEKLİ MESAJ GÖNDERME ---
        if request.method == 'POST':
            content = request.POST.get('content')
            image = request.FILES.get('image') # Formdan resmi al
            
            # İçerik veya Resim varsa kaydet
            if content or image:
                Message.objects.create(
                    sender=request.user,
                    recipient=active_user,
                    body=content if content else "", # Metin yoksa boş string
                    image=image # Resim verisi (veya None)
                )

                # --- MAİL GÖNDERME KISMI (MESAJ) ---
                if active_user.email: # Eğer kullanıcının maili varsa
                    subject = f"UniSkill: New Message from {request.user.first_name}"
                    email_body = f"Hey {active_user.first_name},\n\n{request.user.get_full_name()} sent you a message:\n\n'{content if content else 'Sent a photo 📷'}'\n\nLog in to reply: https://bugraozkaya.pythonanywhere.com/messaging/{request.user.id}/"
                    
                    try:
                        send_mail(subject, email_body, settings.EMAIL_HOST_USER, [active_user.email], fail_silently=True)
                    except:
                        pass
                # ----------------------------------

                return redirect('messaging', user_id=user_id)
        # ---------------------------------------------------

    # 3. YENİ SOHBET BAŞLATMA
    if request.method == 'POST' and not user_id:
        username = request.POST.get('username')
        if username:
            try:
                recipient = User.objects.get(username=username)
                return redirect('messaging', user_id=recipient.id)
            except User.DoesNotExist:
                messages.error(request, "User not found.")

    context = {
        'conversations': conversations,
        'active_user': active_user,
        'chat_messages': chat_messages,
    }
    return render(request, 'core/messaging.html', context)


@login_required
def admin_stats(request):
    if not request.user.is_superuser:
        messages.error(request, "Only administrators can access this page!")
        return redirect('dashboard')

    total_users = User.objects.count()
    total_skills = UserSkill.objects.count()
    total_hours = Session.objects.filter(status='completed').aggregate(Sum('duration'))['duration__sum'] or 0
    total_sessions_count = Session.objects.filter(status='completed').count()

    cat_data = Session.objects.values('skill__category__name').annotate(total=Count('id')).order_by('-total')
    cat_labels = [item['skill__category__name'] for item in cat_data]
    cat_counts = [item['total'] for item in cat_data]

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
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect(notification.link if notification.link else 'dashboard')


# ---------------------------------------------------------
# 4. LANDING PAGE & LEADERBOARD
# ---------------------------------------------------------

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')

# --- LEADERBOARD ---
def leaderboard(request):
    # 1. En Çok Ders Verenler
    most_active = User.objects.annotate(
        session_count=Count('given_sessions', filter=Q(given_sessions__status='completed'))
    ).filter(session_count__gt=0).order_by('-session_count')[:10]

    # 2. En Yüksek Puanlılar
    top_rated = User.objects.annotate(
        avg_rating=Avg('given_sessions__review__rating')
    ).filter(avg_rating__isnull=False).order_by('-avg_rating')[:10]

    context = {
        'most_active': most_active,
        'top_rated': top_rated
    }
    return render(request, 'core/leaderboard.html', context)