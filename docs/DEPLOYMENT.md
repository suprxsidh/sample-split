# Deployment Guide

This guide provides detailed deployment instructions for SampleSplit on various platforms.

## Quick Reference

| Platform | Difficulty | Auto-deploy | Free Tier |
|----------|------------|-------------|-----------|
| Railway | Easy | Yes | Yes |
| Render | Easy | Yes | Yes |
| Fly.io | Medium | Yes | Yes |
| Docker | Medium | No | N/A |
| VPS | Medium | No | N/A |

---

## Railway (Recommended)

Railway is the easiest platform for deploying SampleSplit.

### Prerequisites

- [Railway](https://railway.app) account
- GitHub account with forked repository

### Steps

1. **Fork the Repository**
   ```bash
   # On GitHub, fork the repository
   # https://github.com/suprxsidh/sample-split
   ```

2. **Create New Railway Project**
   - Go to [railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize GitHub if needed
   - Select your forked repository

3. **Configure Environment Variables**
   - Click on the deployed service
   - Go to "Variables" tab
   - Add `SECRET_KEY` with a random 32+ character string
     ```bash
     # Generate a secret key locally
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Optionally add `FLASK_ENV=production`

4. **Deploy**
   - Railway will automatically detect the Dockerfile
   - Deployment takes 2-3 minutes
   - Your app will be available at `https://your-project.railway.app`

### Railway CLI (Optional)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
cd sample-split
railway link

# Open dashboard
railway open

# View logs
railway logs

# Add environment variable
railway variables set SECRET_KEY=your-secret-key
```

---

## Render

### Prerequisites

- [Render](https://render.com) account
- GitHub account with forked repository

### Steps

1. **Create Web Service**
   - Go to [render.com](https://render.com)
   - Click "New +"
   - Select "Web Service"

2. **Connect GitHub**
   - Connect your GitHub account
   - Select your forked repository

3. **Configure Build Settings**
   - **Root Directory**: (leave empty)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`

4. **Add Environment Variables**
   - Click "Environment" tab
   - Add `SECRET_KEY` with a random string
   - Add `FLASK_ENV=production`

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

---

## Fly.io

### Prerequisites

- [flyctl](https://fly.io/docs/flyctl/install/) installed
- Fly.io account

### Steps

1. **Login to Fly.io**
   ```bash
   fly auth login
   ```

2. **Launch Application**
   ```bash
   cd sample-split
   fly launch
   ```
   - App name: `samplesplit` (or your choice)
   - Region: Select closest to you
   - Would you like to set up a Postgres database now? No
   - Would you like to set up an Upstash Redis database now? No

3. **Configure Secrets**
   ```bash
   fly secrets set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

5. **Open App**
   ```bash
   fly open
   ```

### Useful Fly.io Commands

```bash
# View logs
fly logs

# Check status
fly status

# Scale (if needed)
fly scale count 2

# Set secrets
fly secrets set KEY=value

# View secrets
fly secrets list
```

---

## Docker

### Local Deployment

```bash
# Build image
docker build -t samplesplit .

# Run container
docker run -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -e FLASK_ENV=production \
  samplesplit
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
    restart: unless-stopped
    volumes:
      - ./data:/app/data
```

Run:

```bash
docker-compose up -d
```

### Production Considerations

For production Docker deployments:

1. **Use a reverse proxy** (nginx, Caddy, Traefik)
2. **Enable HTTPS** (Let's Encrypt)
3. **Set up backups** for the SQLite database
4. **Monitor resource usage**

Example with Caddy:

```yaml
services:
  web:
    build: .
    restart: unless-stopped
    environment:
      - SECRET_KEY=${SECRET_KEY}
    networks:
      - proxy

  caddy:
    image: caddy:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./caddy_data:/data
    networks:
      - proxy

networks:
  proxy:
    external: true
```

---

## VPS Deployment

### Ubuntu/Debian

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-venv nginx certbot python3-certbot-nginx
   ```

2. **Create User**
   ```bash
   sudo adduser samplesplit
   sudo usermod -aG sudo samplesplit
   su - samplesplit
   ```

3. **Clone and Setup**
   ```bash
   git clone https://github.com/suprxsidh/sample-split.git
   cd sample-split
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create Service**
   ```bash
   sudo nano /etc/systemd/system/samplesplit.service
   ```
   
   ```ini
   [Unit]
   Description=SampleSplit Flask Application
   After=network.target

   [Service]
   User=samplesplit
   WorkingDirectory=/home/samplesplit/sample-split
   Environment="PATH=/home/samplesplit/sample-split/venv/bin"
   Environment="SECRET_KEY=your-secret-key"
   Environment="FLASK_ENV=production"
   ExecStart=/home/samplesplit/sample-split/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Configure Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/samplesplit
   ```
   
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

6. **Enable and Start**
   ```bash
   sudo ln -s /etc/nginx/sites-available/samplesplit /etc/nginx/sites-enabled
   sudo systemctl enable samplesplit
   sudo systemctl start samplesplit
   sudo nginx -t
   sudo systemctl reload nginx
   ```

7. **Setup HTTPS (Let's Encrypt)**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

---

## Database Backups

### SQLite Backup

```bash
# Manual backup
cp samplesplit.db samplesplit_backup_$(date +%Y%m%d).db

# Automated backup script
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
cp /app/samplesplit.db "$BACKUP_DIR/samplesplit_$DATE.db"
# Keep only last 30 backups
ls -t "$BACKUP_DIR"/*.db | tail -n +31 | xargs -r rm
```

### Restore from Backup

```bash
# Stop the application
sudo systemctl stop samplesplit

# Replace database
cp samplesplit_backup_20240101.db samplesplit.db

# Start the application
sudo systemctl start samplesplit
```

---

## Troubleshooting

### Application Won't Start

1. Check logs:
   ```bash
   # Docker
   docker logs <container_id>
   
   # Systemd
   journalctl -u samplesplit -f
   ```

2. Verify environment variables:
   ```bash
   # Check if SECRET_KEY is set
   echo $SECRET_KEY
   ```

3. Check database:
   ```bash
   # Verify database file exists and is readable
   ls -la samplesplit.db
   ```

### Database Locked

SQLite can show "database is locked" errors under heavy load. Solutions:

1. Use PostgreSQL for production
2. Reduce gunicorn workers
3. Check for long-running transactions

### Static Files Not Loading

Ensure `static/` folder exists and contains your CSS files. Check Flask configuration.

---

## Security Checklist

Before going to production:

- [ ] Set `SECRET_KEY` to a random 32+ character string
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (Let's Encrypt, Cloudflare, etc.)
- [ ] Configure firewall (only allow ports 80, 443)
- [ ] Set up database backups
- [ ] Review rate limiting settings
- [ ] Check CSRF protection is enabled
- [ ] Update email/contact information

---

## Getting Help

- Open an [issue](https://github.com/suprxsidh/sample-split/issues) for bugs
- Check the [FAQ](FAQ.md) for common questions
- Read the [Contributing Guide](../CONTRIBUTING.md)
