# Unitur – Multi-Language Tour Agency Website

A production-ready Django 5 travel agency platform with multilingual support (EN, UZ, RU, IT, ES, JA), tour/hotel/domestic-tour booking, Celery async tasks, Cloudinary media, and a plain HTML/CSS/JS frontend (no Node.js build step — `static/css/tailwind.css` is a pre-built, committed stylesheet).

---

## Quick Start

### 1. Prerequisites

- Python 3.13+
- PostgreSQL 14+
- Redis 7+

### 2. Clone & create virtual environment

```bash
git clone <repo-url> unitur
cd unitur
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your DATABASE_URL, REDIS_URL, Cloudinary credentials, etc.
```

### 4. Database setup

```bash
# Create the PostgreSQL role + database (name must match .env's DATABASE_URL)
createuser unitur --pwprompt
createdb unitur_db --owner=unitur

python manage.py migrate
```

### 5. Seed sample data (optional)

```bash
python manage.py seed_data
# Creates: admin/admin123, sample tours, countries, hotels, articles, reviews
```

### 6. Start development server

```bash
python manage.py runserver
```

Open: http://localhost:8000
Admin: `http://localhost:8000/<ADMIN_URL from .env>/`

---

## Celery Workers

```bash
# Start Celery worker (async emails, auto-translate)
celery -A config.celery worker -l info

# Start Celery Beat (scheduled tasks)
celery -A config.celery beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Project Structure

```
unitur/
├── config/
│   ├── settings.py          # Single settings module for dev/test/production
│   ├── urls.py               # Root URL config
│   ├── wsgi.py, celery.py, storages.py
├── apps/
│   ├── core/                 # Base models, context processors, sitemaps
│   ├── tours/                # Tour packages, itineraries, departures
│   ├── ichki_turlar/         # Domestic multi-city tours
│   ├── destinations/         # Continents, countries, cities, attractions
│   ├── hotels/                # Hotels, rooms, amenities
│   ├── bookings/              # Inquiries, booking forms, async emails
│   ├── guides/                 # Travel articles with CKEditor
│   ├── reviews/                # Moderated reviews & ratings
│   ├── accounts/               # User profiles
│   └── dashboard/               # Staff-only admin dashboard
├── templates/                 # All HTML templates
├── static/                    # CSS / JS assets (plain files, no build step)
└── media/                     # User-uploaded files (dev only; Cloudinary in prod)
```

---

## Key Features

| Feature | Implementation |
|---------|---------------|
| **6 Languages** | django-modeltranslation + django-rosetta |
| **Booking System** | Multi-step form, Celery email tasks |
| **Filterable Tours** | django-filter with URL-persistent GET params |
| **Rich Content** | CKEditor for articles/guides |
| **SEO** | sitemaps, robots.txt |
| **Admin** | django-import-export, staff dashboard |
| **Media** | Cloudinary storage in production, local filesystem in dev |
| **Rate Limiting** | django-ratelimit (production only) |
| **Error Tracking** | Sentry integration (optional, via `SENTRY_DSN`) |
| **Caching** | Redis in production, in-memory in dev/tests |
| **CSP** | django-csp security headers |

---

## Environment Variables Reference

See `.env.example` for the full annotated list. Key ones:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` (dev) / `False` (prod) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Media storage (production) |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials (production) |
| `SENTRY_DSN` | Sentry project DSN (optional) |
| `ADMIN_URL` | Custom admin path |
| `HTTPS_ENABLED` | Enables HSTS/secure cookies (production) |

There is **one** settings module (`config/settings.py`) for every environment — behavior is switched by `DEBUG` (from `.env`) and an auto-detected `TESTING` flag (true whenever pytest is running), not by separate settings files.

---

## Running Tests

```bash
pytest
```

Tests always run against an isolated in-memory SQLite database and locmem cache, regardless of what `.env` points at.

---

## Deployment

1. Set `DEBUG=False` and configure `ALLOWED_HOSTS`, `HTTPS_ENABLED=True` in `.env`
2. Run `python manage.py collectstatic`
3. Use gunicorn: `gunicorn --config gunicorn.conf.py config.wsgi:application`
4. Set up Nginx as reverse proxy (see `deploy/nginx.conf`)
5. Configure SSL certificate (Let's Encrypt)

Or via Docker Compose: `docker compose up -d --build` (see `docker-compose.yml`).

---

## Languages

Access any page with a language prefix:
`/en/tours/`, `/uz/tours/`, `/ru/tours/`, `/it/tours/`, `/es/tours/`, `/ja/tours/`

Manage translations: `http://localhost:8000/rosetta/`
