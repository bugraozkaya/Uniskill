from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        # Sadece okunmamış (is_read=False) bildirimleri çekiyoruz
        unread_notifs = Notification.objects.filter(recipient=request.user, is_read=False)
        return {
            'notifications': unread_notifs,
            'notification_count': unread_notifs.count()
        }
    return {}