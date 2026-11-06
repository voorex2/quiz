def notification_count(request):
    if not request.user.is_authenticated:
        return {}
    return {'unread_notifications': request.user.notifications.filter(
        is_read=False, quiz__is_published=True, quiz__is_private=False).count()}
