# Quizzer

Django quiz application with Ukrainian and English interfaces.

## Local setup (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

## Quiz features

- Save public quizzes to Favorites from the quiz detail page.
- Select a category and configure answer/question shuffling in the editor. Answer shuffling is enabled by default; question shuffling is optional.
- Upload JPEG, PNG, WebP or GIF images (maximum 5 MB) for questions, or choose the Image type and supply an image URL. Leaving the upload empty preserves the existing image; Remove image clears it.
- Author statistics show total attempts, average scores, and error rates for current questions. Per-question data is available only for attempts made after this feature was added; skipped questions count as incorrect. Existing overall results remain included.
- Initial categories are History, Science, Programming, Cinema, Geography and General knowledge. Administrators can manage categories at `/admin/quizzes/category/`.

## Notifications

Use Follow author on a quiz page to receive an in-site notification when that author first makes a quiz public. Editing or republishing the same quiz does not send another notification. Private quizzes and drafts do not appear in the notification feed. Manage subscriptions and mark notifications as read on the Notifications page.

Quiz of the week is opt-in on that page. An administrator chooses a public published quiz at `/admin/quizzes/weeklyquiz/add/`, with the Monday date identifying the week. Saving a new selection immediately notifies opted-in users. Future dates are rejected; there is no background scheduler or email delivery. Existing selections cannot be edited through the admin.

## Verification and media

```powershell
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Uploads are stored in `media/` and excluded from Git. Development Django serves them with `DEBUG=True`; production hosting must serve and persist `MEDIA_ROOT` separately. Replaced/deleted image files are retained on disk rather than automatically deleted.

Translations are in [locale/](locale/). GNU gettext is required to run `makemessages` and `compilemessages`.
