web: cd trailynsafe && python manage.py migrate --noinput && gunicorn trailynsafe.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
