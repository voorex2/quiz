from django.db import migrations


def initialize(apps, schema_editor):
    category = apps.get_model('quizzes', 'Category')
    for name in ('History', 'Science', 'Programming', 'Cinema', 'Geography', 'General knowledge'):
        category.objects.get_or_create(name=name)
    apps.get_model('quizzes', 'Quiz').objects.filter(is_published=True, is_private=False).update(announced=True)


class Migration(migrations.Migration):
    dependencies = [('quizzes', '0005_category_question_image_quiz_announced_and_more')]
    operations = [migrations.RunPython(initialize, migrations.RunPython.noop)]
