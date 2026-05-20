# Installation Guide

This guide will help you install and configure the Pinterest Growth Agent (PGA) for use with GitHub Actions and Baserow.

## Prerequisites

- Python 3.11 or higher
- A GitHub account
- A free [Baserow](https://baserow.io) account
- A free [Groq](https://console.groq.com) API key
- Pinterest account credentials

---

## Step 1: Fork/Clone the Repository

### Option A: Fork to Your GitHub Account

1. Go to the repository on GitHub
2. Click **Fork** in the top-right corner
3. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pinterest-growth-agent.git
   cd pinterest-growth-agent
   ```

### Option B: Use as Template

1. Click **Use this template** → **Create a new repository**
2. Name your repository
3. Clone the new repository

---

## Step 2: Set Up Baserow Database

1. **Create Account**: Go to [baserow.io](https://baserow.io) and sign up for free

2. **Create Database**: 
   - Click **Create New** → **Database**
   - Name it `Pinterest Growth Agent`

3. **Create Tables**: Create the following tables with exact names:

   ### keywords
   | Field Name | Field Type | Notes |
   |------------|-----------|-------|
   | term | Text | Make unique |
   | suggestion_rank | Number | |
   | related_terms | Long Text | Store as JSON |
   | source | Text | Default: autosuggest |
   | performance_score | Number | Default: 0 |
   | discovered_at | Date | |

   ### trends
   | Field Name | Field Type |
   |------------|-----------|
   | name | Text |
   | velocity | Number |
   | region | Text |
   | category | Text |
   | keywords | Long Text (JSON) |
   | fetched_at | Date |

   ### pins
   | Field Name | Field Type | Notes |
   |------------|-----------|-------|
   | image_path | Text | |
   | image_hash | Text | Make unique |
   | title | Text | |
   | description | Long Text | |
   | alt_text | Text | |
   | target_keyword | Text | |
   | board_name | Text | |
   | content_type | Text | |
   | status | Single Select | Options: pending, posted, failed |
   | scheduled_at | Date | |
   | posted_at | Date | |
   | pinterest_url | URL | |
   | created_at | Date | |

   ### engagement
   | Field Name | Field Type |
   |------------|-----------|
   | pin_id | Number |
   | impressions | Number |
   | saves | Number |
   | clicks | Number |
   | ctr | Number |
   | save_rate | Number |
   | scraped_at | Date |

   ### agent_log
   | Field Name | Field Type |
   |------------|-----------|
   | action | Text |
   | details | Long Text (JSON) |
   | created_at | Date |

   ### scraper_health
   | Field Name | Field Type | Notes |
   |------------|-----------|-------|
   | module_name | Text | Make unique |
   | run_count | Number | |
   | success_count | Number | |
   | failure_count | Number | |
   | last_run_at | Date | |
   | last_success_at | Date | |
   | last_failure_at | Date | |
   | last_error | Long Text | |
   | avg_results | Number | |

   ### diagnostic_reports
   | Field Name | Field Type | Notes |
   |------------|-----------|-------|
   | scraper_module | Text | |
   | failure_count | Number | |
   | last_error | Long Text | |
   | diagnosis | Long Text | |
   | suggested_fix | Long Text | |
   | status | Single Select | Options: pending, resolved |
   | created_at | Date | |
   | resolved_at | Date | |

4. **Get API Token**:
   - Click your profile → **Settings** → **API Token**
   - Generate a new token
   - Copy and save it securely

5. **Get Database ID**:
   - Open your database
   - Look at the URL: `https://baserow.io/database/XXXXX/...`
   - The number after `/database/` is your Database ID

---

## Step 3: Configure GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

   | Secret Name | Value |
   |-------------|-------|
   | `PINTEREST_EMAIL` | Your Pinterest login email |
   | `PINTEREST_PASSWORD` | Your Pinterest password |
   | `GROQ_API_KEY` | Get from [console.groq.com](https://console.groq.com) |
   | `BASEROW_TOKEN` | Your Baserow API token from Step 2 |
   | `BASEROW_DATABASE_ID` | Your Baserow database ID from Step 2 |

4. (Optional) For server deployment:
   | Secret Name | Value |
   |-------------|-------|
   | `SERVER_SSH_KEY` | SSH private key for deployment |
   | `SERVER_HOST` | Server hostname/IP |
   | `SERVER_USER` | SSH username |

---

## Step 4: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. If prompted, click **I understand my workflows, go ahead and enable them**
3. The workflow will run automatically on:
   - Every push to main/master branch
   - Daily at 8 AM UTC (configurable in `.github/workflows/ci-cd.yml`)
   - Manual trigger via **Run workflow** button

---

## Step 5: Local Development (Optional)

If you want to run locally instead of/in addition to GitHub Actions:

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/pinterest-growth-agent.git
cd pinterest-growth-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor

# Initialize database
python -c "from src.store.database import Database; from src.utils.config import load_config; db = Database(load_config()['paths']['database']); db.initialize()"

# Run once
python -m src.main run-now

# Or start scheduler
python -m src.main start
```

---

## Step 6: Customize Configuration

Edit `config.yaml` to customize:

```yaml
# Your niche
niche:
  seed_keywords:
    - "Your Topic 1"
    - "Your Topic 2"
  categories:
    - "Your Category"

# Posting schedule
schedule:
  start_hour: 8  # 24h format
  timezone: "US/Eastern"
  
# AI settings
ai:
  max_images_per_day: 15
```

---

## Verification

### Check GitHub Actions Status

1. Go to **Actions** tab
2. You should see workflow runs
3. Click on a run to see detailed logs

### Check Baserow Data

1. Log into Baserow
2. Open your database
3. You should see data appearing in tables after runs

### Check Pinterest

1. Log into Pinterest
2. Verify pins are being posted according to schedule

---

## Troubleshooting

### Workflow Fails on First Run

**Missing secrets**: Ensure all required secrets are set in GitHub Settings

**Baserow connection error**: 
- Verify token and database ID are correct
- Check table names match exactly (case-sensitive)

**Pinterest login fails**:
- Verify credentials in secrets
- Try manual login to ensure account is accessible
- Check if 2FA is enabled (may need app-specific password)

### No Pins Being Generated

**Check logs**: Look at GitHub Actions logs for errors

**Verify Groq API key**: Test at [console.groq.com](https://console.groq.com)

**Check config.yaml**: Ensure seed_keywords are not empty

---

## Next Steps

- Monitor your Pinterest analytics
- Adjust keywords based on performance
- Increase posting limits gradually as account warms up
- Review [BEGINNERS_GUIDE_EN.md](BEGINNERS_GUIDE_EN.md) for advanced tips

---

## Support

For issues or questions:
1. Check existing Issues in the repository
2. Review the troubleshooting section above
3. Consult the beginner guides (EN/AR/FR)
