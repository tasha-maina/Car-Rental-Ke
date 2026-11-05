# Car Rental KE (Django)
    python3 -m venv venv && venv/bin/pip install -r requirements.txt
    venv/bin/python manage.py migrate
    venv/bin/python manage.py seed_fleet
    venv/bin/python manage.py createsuperuser
    venv/bin/python manage.py runserver
Site: http://127.0.0.1:8000/ · Admin (edit prices, confirm payments): /admin/

## Automatic M-Pesa (STK push)
Needs a Safaricom Daraja app + paybill/till. Set env vars, then restart:

    export MPESA_ENV=production   # or sandbox
    export MPESA_CONSUMER_KEY=... MPESA_CONSUMER_SECRET=...
    export MPESA_SHORTCODE=... MPESA_PASSKEY=...
    export MPESA_TRANSACTION_TYPE=CustomerBuyGoodsOnline   # only for a Till; default is Paybill
    export MPESA_CALLBACK_URL=https://YOUR-DOMAIN/mpesa/callback/

The callback URL must be public HTTPS (use ngrok when testing locally).
Without these, the site falls back to manual Send Money to 0790434294.

## Going live
    export DJANGO_SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_urlsafe(50))')"
    export DJANGO_DEBUG=False
    export DJANGO_ALLOWED_HOSTS=yourdomain.co.ke,www.yourdomain.co.ke
    export DJANGO_CSRF_ORIGINS=https://yourdomain.co.ke,https://www.yourdomain.co.ke
    venv/bin/python manage.py collectstatic --noinput
    venv/bin/python manage.py migrate
    venv/bin/gunicorn config.wsgi
Run behind HTTPS (e.g. nginx/Caddy or a host like Render/Railway). Use a real DB (Postgres) for heavy traffic.
