#!/bin/bash
# =============================================================================
# Unitur – First-time server setup script
# Run as root on a fresh Ubuntu 22.04 / 24.04 server
# Usage: sudo bash setup.sh
# =============================================================================
set -e

APP_USER="unitur"
APP_DIR="/var/www/unitur"
LOG_DIR="/var/log/unitur"
RUN_DIR="/run/unitur"
PYTHON_VERSION="3.13"

echo "=============================="
echo " Unitur Server Setup"
echo "=============================="

# --- System packages ---
apt-get update
apt-get install -y \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    certbot python3-certbot-nginx \
    git curl build-essential libpq-dev \
    supervisor

# --- Create app user ---
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home $APP_DIR --create-home $APP_USER
    echo "User '$APP_USER' created."
fi

# --- Directories ---
mkdir -p $LOG_DIR $RUN_DIR
chown $APP_USER:$APP_USER $LOG_DIR $RUN_DIR
chmod 750 $LOG_DIR

# --- Log rotation ---
cat > /etc/logrotate.d/unitur << 'EOF'
/var/log/unitur/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 unitur unitur
    sharedscripts
    postrotate
        systemctl reload unitur-gunicorn 2>/dev/null || true
    endscript
}
EOF

# --- PostgreSQL: create DB + user ---
echo "Creating PostgreSQL database..."
sudo -u postgres psql << 'PSQL'
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'unitur') THEN
        CREATE USER unitur WITH PASSWORD 'CHANGE_THIS_PASSWORD';
    END IF;
END$$;
CREATE DATABASE unitur_db OWNER unitur;
GRANT ALL PRIVILEGES ON DATABASE unitur_db TO unitur;
PSQL
echo "Database created. Set password in .env"

# --- Redis: bind to localhost only ---
sed -i 's/^bind .*/bind 127.0.0.1 ::1/' /etc/redis/redis.conf
systemctl restart redis-server
systemctl enable redis-server

# --- systemd tmpfiles for /run/unitur ---
cat > /etc/tmpfiles.d/unitur.conf << EOF
d /run/unitur 0755 $APP_USER $APP_USER -
EOF
systemd-tmpfiles --create /etc/tmpfiles.d/unitur.conf

# --- Copy systemd service files ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp $SCRIPT_DIR/gunicorn.service    /etc/systemd/system/unitur-gunicorn.service
cp $SCRIPT_DIR/celery.service      /etc/systemd/system/unitur-celery.service
cp $SCRIPT_DIR/celery-beat.service /etc/systemd/system/unitur-celery-beat.service
systemctl daemon-reload

# --- Let the app user (re)start ONLY its own services without a password ---
# deploy.sh runs as $APP_USER and calls `sudo systemctl restart ...`; grant just
# those specific commands so the deploy completes without manual intervention.
cat > /etc/sudoers.d/unitur-deploy << EOF
$APP_USER ALL=(root) NOPASSWD: /usr/bin/systemctl restart unitur-gunicorn, /usr/bin/systemctl restart unitur-celery, /usr/bin/systemctl restart unitur-celery-beat, /usr/bin/systemctl reload unitur-gunicorn, /usr/bin/systemctl is-active unitur-gunicorn, /usr/bin/systemctl is-active unitur-celery, /usr/bin/systemctl is-active unitur-celery-beat
EOF
chmod 0440 /etc/sudoers.d/unitur-deploy
visudo -c -f /etc/sudoers.d/unitur-deploy

echo ""
echo "=============================="
echo " Setup complete!"
echo "=============================="
echo "Next steps:"
echo "  1. Clone your repo to $APP_DIR"
echo "  2. Copy .env.production to $APP_DIR/.env and fill in values"
echo "  3. Run: sudo -u $APP_USER bash $APP_DIR/deploy/deploy.sh"
echo "  4. Configure nginx: cp deploy/nginx.conf /etc/nginx/sites-available/unitur"
echo "  5. Update domain in nginx.conf, then: certbot --nginx -d yourdomain.com"
echo "  6. Enable services:"
echo "     systemctl enable --now unitur-gunicorn"
echo "     systemctl enable --now unitur-celery"
echo "     systemctl enable --now unitur-celery-beat"
