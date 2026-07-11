FROM python:3.13-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# App user
RUN useradd --system --create-home --shell /bin/bash unitur

WORKDIR /app

# Python deps
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App code (CSS is a plain, pre-built static file already committed in static/css/)
COPY --chown=unitur:unitur . .

# Create log/run dirs
RUN mkdir -p /var/log/unitur /run/unitur \
    && chown unitur:unitur /var/log/unitur /run/unitur

USER unitur

ENV DJANGO_SETTINGS_MODULE=config.settings \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
