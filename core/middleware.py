import time
from django.core.cache import cache
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages

class AdminBruteForceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_login_url = reverse('admin:login')
        ip = self.get_client_ip(request)
        
        # 1. CHECK IF BLOCKED (On Page Load)
        blocked_expiry = cache.get(f'admin_blocked_{ip}')
        if blocked_expiry:
            remaining = int(blocked_expiry - time.time())
            if remaining > 0:
                if request.path == admin_login_url:
                    return render(request, 'core/login_blocked.html', {
                        'remaining': remaining,
                        'next_url': admin_login_url 
                    })
            else:
                # Unblock if time has expired
                cache.delete(f'admin_blocked_{ip}')

        # Process the request (Call Django's view function)
        response = self.get_response(request)

        # 2. FAILED LOGIN CHECK (After POST Request)
        if request.path == admin_login_url and request.method == 'POST':
            
            # Check not just 'authenticated' but also 'is_staff'.
            # This way, normal users attacking admin are also caught.
            if not request.user.is_staff:
                fail_key = f'admin_fail_{ip}'
                count = cache.get(fail_key, 0) + 1
                
                # Cache duration 2 mins (kept short for testing purposes)
                cache.set(fail_key, count, 120) 

                remaining_attempts = 3 - count
                
                # 3. ERROR: BLOCK
                if count >= 3:
                    expiry_time = time.time() + 30
                    cache.set(f'admin_blocked_{ip}', expiry_time, 30)
                    cache.delete(fail_key)
                    
                    return render(request, 'core/login_blocked.html', {
                        'remaining': 30,
                        'next_url': admin_login_url
                    })

                # 1. and 2. ERROR: SHOW MESSAGE
                if remaining_attempts > 0:
                    msg = f"⚠️ Incorrect Password! (Attempt {count}) - Remaining attempts: {remaining_attempts}"
                    
                    # Inject message into the form (Show immediately without Redirect)
                    # Django 5.x COMPATIBLE METHOD:
                    if hasattr(response, 'context_data') and response.context_data:
                        form = response.context_data.get('form')
                        if form:
                            # Add error to form
                            form.add_error(None, msg)
                            
                            # Get template name (can be a list, checking it)
                            template_name = response.template_name
                            if isinstance(template_name, list):
                                template_name = template_name[0]
                            
                            # Re-render page with UPDATED context
                            # (Instead of setting is_rendered=False)
                            return render(request, template_name, response.context_data)
                    
                    # Backup method (If the above doesn't work)
                    messages.error(request, msg)

            else:
                # LOGIN SUCCESSFUL (User has Staff permissions)
                # Clear past errors
                cache.delete(f'admin_fail_{ip}')

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')