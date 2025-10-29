python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py add_data_from_json
python manage.py collectstatic --noinput
gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi