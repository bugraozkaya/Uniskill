import time
from django.core.cache import cache
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

class AdminBruteForceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_login_url = reverse('admin:login')
        ip = self.get_client_ip(request)
        
        # 1. IP Engelli mi kontrolü
        blocked_expiry = cache.get(f'admin_blocked_{ip}')
        if blocked_expiry:
            remaining = int(blocked_expiry - time.time())
            if remaining > 0:
                if request.path == admin_login_url:
                    return render(request, 'core/login_blocked.html', {'remaining': remaining})
            else:
                cache.delete(f'admin_blocked_{ip}')

        response = self.get_response(request)

        # 2. Hatalı giriş kontrolü
        if request.path == admin_login_url and request.method == 'POST':
            if not request.user.is_authenticated:
                fail_key = f'admin_fail_{ip}'
                count = cache.get(fail_key, 0) + 1
                cache.set(fail_key, count, 300)

                remaining_attempts = 3 - count
                
                # 3 hak dolduysa engelle
                if count >= 3:
                    expiry_time = time.time() + 30
                    cache.set(f'admin_blocked_{ip}', expiry_time, 30)
                    cache.delete(fail_key)
                    return render(request, 'core/login_blocked.html', {'remaining': 30})

                # İLK HATADA VE SONRASINDA MESAJI GÖSTERMEK İÇİN:
                if remaining_attempts > 0:
                    # Mesajı ekliyoruz
                    messages.error(request, f"⚠️ Incorrect password! ({count}. Attempt) - Remaining attempts: {remaining_attempts}")
                    
                    # Sayfayı render etmek yerine redirect (yönlendirme) yapıyoruz.
                    # Redirect yapınca Django mesajı bir sonraki yüklemede (anında) gösterir.
                    return redirect(admin_login_url)
            else:
                cache.delete(f'admin_fail_{ip}')

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')