<!--
Purpose: Describe actual production deployment setup for backend (VPS + Docker + Nginx + SSL) and frontend (Vercel).
Used by: Developers and operators deploying or maintaining the production system.
-->

# 13. Deployment Guide

Sistem dijalankan dengan arsitektur terpisah (*Decoupled Architecture*):
- **Backend** → VPS (Docker + Nginx + Let's Encrypt SSL)
- **Frontend** → Vercel (auto-deploy dari GitHub)

---

## Arsitektur Deployment

```
Internet
    │
    ├─→ fakeaccountdetection.v-teki.com (Vercel, HTTPS)
    │       NEXT_PUBLIC_API_URL = https://api.v-teki.com
    │
    └─→ api.v-teki.com (VPS 69.62.123.214)
            Nginx (443 HTTPS, cert via Let's Encrypt)
                ↓ proxy_pass
            localhost:8080
                ↓
            Docker Container (FastAPI + Uvicorn)
                ↓ volume mount
            /opt/fake-account-detection/models/
            /opt/fake-account-detection/data/
```

---

## 1. Backend — VPS + Docker

### Prasyarat (VPS)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin

# Install Nginx + Certbot
apt-get install -y nginx certbot python3-certbot-nginx
```

### File Konfigurasi

**`Dockerfile`** (di root repo):
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ \
    && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir xgboost
COPY backend/ ./backend/
COPY data/ ./data/
COPY models/ ./models/
ENV PYTHONPATH=/app
CMD ["python3", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**`docker-compose.yml`** (di root repo):
```yaml
services:
  backend:
    build: .
    container_name: fakedetect-backend
    restart: always
    ports:
      - "8080:8080"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app
```

### Deploy / Update Backend

```bash
# Di VPS, dari /opt/fake-account-detection/
git pull origin main
docker compose up -d --build

# Cek status
docker compose ps
docker compose logs -f backend

# Jika perlu retrain model di VPS
python3 scripts/train_model.py
python3 scripts/train_new_user_model.py
```

> **Catatan:** File `.pkl` tidak di-track git (ada di `.gitignore`). Model perlu dilatih langsung di VPS setelah pull pertama.

---

## 2. Nginx + SSL (api.v-teki.com)

### Konfigurasi Nginx

File: `/etc/nginx/sites-available/fakedetect-api`

```nginx
server {
    listen 80;
    server_name api.v-teki.com;
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Aktifkan site
ln -s /etc/nginx/sites-available/fakedetect-api /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### SSL Certificate (Let's Encrypt)

```bash
# Dapatkan dan pasang SSL otomatis
certbot --nginx -d api.v-teki.com

# Certbot otomatis menambahkan blok HTTPS + redirect 80→443
# Auto-renew sudah diatur via systemd timer
certbot renew --dry-run  # test
```

### DNS Setup (Hostinger)

Tambahkan A Record di panel DNS Hostinger untuk domain `v-teki.com`:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | api | 69.62.123.214 | 3600 |

---

## 3. Frontend — Vercel

### Setup Awal

1. Buka [vercel.com](https://vercel.com) → login dengan akun `nudgesimulation@gmail.com`
2. **New Project** → Import repo `nudge-deploy/fake-account-detection`
3. **Framework Preset:** Next.js (auto-detected)
4. **Root Directory:** `frontend`
5. **Environment Variables:** Tambahkan:
   ```
   NEXT_PUBLIC_API_URL = https://api.v-teki.com
   ```
6. Klik **Deploy**

### Update Setelah Code Change

Setiap `git push` ke `main` akan otomatis trigger redeploy di Vercel.

Jika hanya **environment variable** yang berubah:
1. Vercel Dashboard → Project Settings → Environment Variables
2. Edit nilai `NEXT_PUBLIC_API_URL`
3. Klik **Redeploy** (wajib — env var Next.js di-bake saat build time)

### Custom Domain

Domain `fakeaccountdetection.v-teki.com` dikonfigurasi di Vercel Dashboard → Domains.

---

## 4. Troubleshooting

| Problem | Penyebab | Solusi |
|---------|---------|--------|
| Frontend "Gangguan Koneksi API" | `NEXT_PUBLIC_API_URL` salah atau belum redeploy | Cek env var di Vercel, lalu redeploy |
| Port 8080 sudah dipakai | Proses lain | `lsof -i :8080` → kill prosesnya |
| Docker container tidak muncul | `git pull` gagal atau `.pkl` tidak ada | Jalankan `git pull origin main` lalu retrain |
| SSL expired | Certbot auto-renew gagal | `certbot renew` manual |
| Mixed Content error | Backend masih HTTP, frontend HTTPS | Pastikan Nginx + certbot sudah terpasang |

---

## 5. Environment Variables

| Variable | Platform | Nilai Produksi |
|----------|----------|----------------|
| `NEXT_PUBLIC_API_URL` | Vercel (build time) | `https://api.v-teki.com` |
| `GROQ_API_KEY` | Vercel (optional) | Key dari console.groq.com |
| `PYTHONPATH` | Docker | `/app` |
