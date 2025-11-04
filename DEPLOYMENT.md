# InsightLens Deployment Guide

## Table of Contents
- [Local Development Setup](#local-development-setup)
- [Free Deployment Options](#free-deployment-options)
- [Render.com Deployment (Recommended)](#rendercom-deployment-recommended)
- [Railway Deployment](#railway-deployment)
- [Fly.io Deployment](#flyio-deployment)
- [Environment Variables](#environment-variables)

---

## Local Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (or Docker)
- Git

### Step 1: Clone and Setup Virtual Environment

```bash
git clone https://github.com/monideep2255/InsightLens.git
cd InsightLens

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Setup PostgreSQL

**Option A: Using Docker (Easiest)**
```bash
docker run --name insightlens-db \
  -e POSTGRES_USER=insightlens \
  -e POSTGRES_PASSWORD=dev_password \
  -e POSTGRES_DB=insightlens \
  -p 5432:5432 \
  -d postgres:14
```

**Option B: Native PostgreSQL**
```bash
# macOS
brew install postgresql@14
brew services start postgresql@14
createdb insightlens

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb insightlens

# Windows
# Download from: https://www.postgresql.org/download/windows/
# Then use pgAdmin to create database 'insightlens'
```

### Step 4: Configure Environment Variables

```bash
# Copy the sample
cp .env.sample .env

# Generate a secure SESSION_SECRET
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit .env with your values
nano .env  # or use your preferred editor
```

Required variables:
```env
DATABASE_URL=postgresql://insightlens:dev_password@localhost:5432/insightlens
SESSION_SECRET=your_generated_secret_here
OPENAI_API_KEY=sk-proj-your-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
MONTHLY_API_BUDGET=20.0
```

### Step 5: Initialize Database

```bash
python recreate_db.py
```

### Step 6: Run the Application

**Development Mode:**
```bash
python main.py
```

**Production Mode (with Gunicorn):**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
```

Visit: **http://localhost:5000**

---

## Free Deployment Options

### Comparison Table

| Platform | Free Tier | Database | Auto-Sleep | Setup Difficulty |
|----------|-----------|----------|------------|------------------|
| **Render.com** ⭐ | 750 hrs/mo | PostgreSQL ✅ | Yes (15 min) | Easy |
| **Railway** | $5 credit/mo | PostgreSQL ✅ | No | Easy |
| **Fly.io** | 3 VMs (256MB) | Postgres ✅ | No | Medium |
| **PythonAnywhere** | Limited | MySQL ⚠️ | N/A | Easy |

**Recommendation:** Use **Render.com** for the best free tier experience.

---

## Render.com Deployment (Recommended)

### Method 1: Using Blueprint (One-Click)

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Deploy to Render:**
   - Visit: https://render.com
   - Sign up with GitHub
   - Click **"New +"** → **"Blueprint"**
   - Select your `InsightLens` repository
   - Render will read `render.yaml` and create:
     - PostgreSQL database
     - Web service
     - Auto-configured DATABASE_URL

3. **Set Required Secrets:**
   - Go to your web service dashboard
   - Navigate to **"Environment"** tab
   - Add:
     ```
     OPENAI_API_KEY=sk-proj-your-key-here
     ADMIN_PASSWORD=your_secure_password
     ```

4. **Deploy:**
   - Click **"Create New Resources"**
   - Wait 3-5 minutes for first deploy
   - Your app will be live at: `https://insightlens.onrender.com`

### Method 2: Manual Setup

#### Step 1: Create Database

1. Log in to https://dashboard.render.com
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `insightlens-db`
   - **Database:** `insightlens`
   - **User:** `insightlens`
   - **Region:** Oregon (US West)
   - **Plan:** **Free**
4. Click **"Create Database"**
5. Copy the **Internal Database URL** (Important!)

#### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `insightlens`
   - **Region:** Oregon (US West) - same as DB
   - **Branch:** `main`
   - **Root Directory:** leave empty
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 main:app`
   - **Plan:** **Free**

#### Step 3: Set Environment Variables

In the **"Environment"** tab, add:

```
DATABASE_URL=[paste Internal Database URL from Step 1]
SESSION_SECRET=[generate with: python -c "import secrets; print(secrets.token_hex(32))"]
OPENAI_API_KEY=sk-proj-your-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
MONTHLY_API_BUDGET=20.0
```

#### Step 4: Deploy

- Click **"Create Web Service"**
- Monitor logs in the dashboard
- First deploy: ~5 minutes
- Subsequent deploys: ~2-3 minutes

### Auto-Deploy on Git Push

Render automatically redeploys when you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
# Render auto-deploys in ~2 minutes
```

### Important Notes

- **Free tier sleeps after 15 min inactivity** (wakes in ~30 seconds on request)
- **750 hours/month free** (~31 days if always on)
- **Database:** 1GB storage free
- To keep always-on: Upgrade to Starter ($7/month)

---

## Railway Deployment

### Step 1: Install Railway CLI (Optional)

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Deploy

**Via Dashboard:**
1. Go to https://railway.app
2. Sign up with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select `InsightLens`
5. Railway auto-detects Python and installs dependencies

**Via CLI:**
```bash
railway init
railway up
```

### Step 3: Add PostgreSQL

1. In project dashboard, click **"New"** → **"Database"** → **"PostgreSQL"**
2. Railway automatically sets `DATABASE_URL` environment variable

### Step 4: Set Environment Variables

```bash
railway variables set OPENAI_API_KEY=sk-proj-your-key-here
railway variables set SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
railway variables set ADMIN_USERNAME=admin
railway variables set ADMIN_PASSWORD=your_password
railway variables set MONTHLY_API_BUDGET=20.0
```

### Step 5: Deploy

Railway auto-deploys on push. Your app URL: `https://insightlens-production.up.railway.app`

**Note:** Free tier is $5 credit/month (~500 hours). May need to upgrade after trial.

---

## Fly.io Deployment

### Step 1: Install Fly CLI

```bash
# macOS/Linux
curl -L https://fly.io/install.sh | sh

# Windows
iwr https://fly.io/install.ps1 -useb | iex
```

### Step 2: Login and Launch

```bash
fly auth login
fly launch
```

Fly will ask questions:
- **App name:** `insightlens` (or your choice)
- **Region:** Choose closest to you
- **PostgreSQL:** Yes → Select free tier (3GB)
- **Deploy now:** No (we need to set secrets first)

### Step 3: Set Secrets

```bash
fly secrets set OPENAI_API_KEY=sk-proj-your-key-here
fly secrets set SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(32))")
fly secrets set ADMIN_USERNAME=admin
fly secrets set ADMIN_PASSWORD=your_password
fly secrets set MONTHLY_API_BUDGET=20.0
```

### Step 4: Deploy

```bash
fly deploy
```

Your app: `https://insightlens.fly.dev`

**Note:** Free tier: 3 VMs with 256MB RAM. May be limited for concurrent users.

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SESSION_SECRET` | Flask session encryption key | Random 64-char hex string |
| `OPENAI_API_KEY` | OpenAI API key for AI analysis | `sk-proj-...` |
| `ADMIN_USERNAME` | Admin panel username | `admin` |
| `ADMIN_PASSWORD` | Admin panel password | Strong password |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONTHLY_API_BUDGET` | Monthly spending limit (USD) | `20.0` |

### Generating Secure Secrets

**SESSION_SECRET:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**ADMIN_PASSWORD:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

---

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt
```

### Database connection errors
- Verify `DATABASE_URL` is set correctly
- Check PostgreSQL is running: `pg_isready`
- Test connection: `psql $DATABASE_URL`

### Port already in use
```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill it or use different port
export PORT=8000
python main.py
```

### OpenAI API errors
- Verify API key: https://platform.openai.com/api-keys
- Check usage limits: https://platform.openai.com/usage
- Ensure billing is set up

### Import errors (openai, langchain, etc.)
```bash
pip install --upgrade openai langchain langchain-community
```

---

## Performance Tips

### Production Optimizations

1. **Use Gunicorn with multiple workers:**
   ```bash
   gunicorn --bind 0.0.0.0:$PORT --workers 4 --worker-class sync --timeout 120 main:app
   ```

2. **Set up a CDN** (Cloudflare free tier)

3. **Enable database connection pooling** (already configured in `app.py`)

4. **Monitor API costs** via admin dashboard at `/admin/api-usage`

---

## Next Steps

- [ ] Deploy to Render.com
- [ ] Set up custom domain (optional)
- [ ] Configure monitoring (UptimeRobot for free uptime checks)
- [ ] Set up backup strategy for PostgreSQL
- [ ] Review security settings

---

## Support

- **Issues:** https://github.com/monideep2255/InsightLens/issues
- **Render Docs:** https://render.com/docs
- **Railway Docs:** https://docs.railway.app
- **Fly.io Docs:** https://fly.io/docs
