from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuthorFollow, Notification, NotificationPreference, Quiz, WeeklyQuiz


@receiver(post_save, sender=Quiz)
def announce_quiz(sender, instance, raw=False, **kwargs):
    if raw or not instance.is_published or instance.is_private:
        return
    if not Quiz.objects.filter(pk=instance.pk, announced=False).update(announced=True):
        return
    instance.announced = True
    Notification.objects.bulk_create([
        Notification(user_id=user_id, quiz=instance, kind='author', event=f'author:{instance.pk}')
        for user_id in AuthorFollow.objects.filter(author=instance.owner).exclude(user=instance.owner).values_list('user_id', flat=True)
    ], ignore_conflicts=True)


@receiver(post_save, sender=WeeklyQuiz)
def announce_weekly(sender, instance, created, raw=False, **kwargs):
    if raw or not created or not instance.quiz.is_published or instance.quiz.is_private:
        return
    Notification.objects.bulk_create([
        Notification(user_id=user_id, quiz=instance.quiz, kind='weekly', event=f'weekly:{instance.week}')
        for user_id in NotificationPreference.objects.filter(weekly=True).values_list('user_id', flat=True)
    ], ignore_conflicts=True)
