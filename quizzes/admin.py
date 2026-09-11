from django.contrib import admin

from .models import Answer, Question, Quiz


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type', 'time_limit', 'order')
    list_filter = ('question_type',)
    inlines = (AnswerInline,)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'is_published', 'created_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'description')
    readonly_fields = ('invite_code',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)
