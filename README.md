# Pinterest Growth Agent (PGA)

An autonomous AI agent that grows your Pinterest account by finding high-demand keywords, generating optimized pins, and posting them safely — all on autopilot.

## How It Works

```
Research → Generate → Post → Learn → Repeat (daily)
```

1. **Research** — Scrapes Pinterest for trending topics and high-value keywords
2. **Generate** — Creates unique AI images + SEO-optimized metadata
3. **Post** — Publishes pins safely via Playwright with anti-detection
4. **Learn** — Tracks performance and prioritizes what works

---

## Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd pinterest-growth-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `PINTEREST_EMAIL` — Your Pinterest login email
- `PINTEREST_PASSWORD` — Your Pinterest password
- `GROQ_API_KEY` — Free API key from [console.groq.com](https://console.groq.com)

### 3. Configure Settings

Edit `config.yaml` to set:
- `seed_keywords` — Topics/niche you want to post about
- `categories` — Pinterest categories for your niche
- `schedule.start_hour` — When to run daily (24h format)
- `schedule.timezone` — Your timezone

### 4. Run the Agent

```bash
# Initialize database and start scheduler (runs daily)
python -m src.main start

# OR run a single cycle manually
python -m src.main run-now

# Check status and statistics
python -m src.main stats
```

---

## GitHub Actions Deployment

This project supports automated deployment via GitHub Actions. To enable:

1. Go to your repository **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:
   - `PINTEREST_EMAIL` — Your Pinterest email
   - `PINTEREST_PASSWORD` — Your Pinterest password
   - `GROQ_API_KEY` — Your Groq API key
   - `BASEROW_TOKEN` — Your Baserow API token (for database)
   - `BASEROW_DATABASE_ID` — Your Baserow database ID

3. Enable GitHub Actions in your repository settings

The workflow will automatically:
- Install dependencies
- Validate configuration
- Run the agent on schedule

---

## Database: Baserow Integration

This project uses [Baserow](https://baserow.io/) as its primary database instead of SQLite for better scalability and remote access.

### Setup Baserow

1. Create a free account at [baserow.io](https://baserow.io)
2. Create a new database with the following tables:

#### Tables Structure

**keywords**
- `term` (Text, unique)
- `suggestion_rank` (Number)
- `related_terms` (Long Text, JSON)
- `source` (Text)
- `performance_score` (Number)
- `discovered_at` (Date)

**trends**
- `name` (Text)
- `velocity` (Number)
- `region` (Text)
- `category` (Text)
- `keywords` (Long Text, JSON)
- `fetched_at` (Date)

**pins**
- `image_path` (Text)
- `image_hash` (Text, unique)
- `title` (Text)
- `description` (Long Text)
- `alt_text` (Text)
- `target_keyword` (Text)
- `board_name` (Text)
- `content_type` (Text)
- `status` (Single select: pending, posted, failed)
- `scheduled_at` (Date)
- `posted_at` (Date)
- `pinterest_url` (URL)
- `created_at` (Date)

**engagement**
- `pin_id` (Number)
- `impressions` (Number)
- `saves` (Number)
- `clicks` (Number)
- `ctr` (Number)
- `save_rate` (Number)
- `scraped_at` (Date)

**agent_log**
- `action` (Text)
- `details` (Long Text, JSON)
- `created_at` (Date)

**scraper_health**
- `module_name` (Text, unique)
- `run_count` (Number)
- `success_count` (Number)
- `failure_count` (Number)
- `last_run_at` (Date)
- `last_success_at` (Date)
- `last_failure_at` (Date)
- `last_error` (Long Text)
- `avg_results` (Number)

**diagnostic_reports**
- `scraper_module` (Text)
- `failure_count` (Number)
- `last_error` (Long Text)
- `diagnosis` (Long Text)
- `suggested_fix` (Long Text)
- `status` (Single select: pending, resolved)
- `created_at` (Date)
- `resolved_at` (Date)

3. Get your API Token from **Settings** → **API Token**
4. Note your Database ID from the URL

### Configure Baserow Connection

Add to your `.env` file:

```bash
BASEROW_URL=https://api.baserow.io
BASEROW_TOKEN=your_baserow_token_here
BASEROW_DATABASE_ID=your_database_id_here
```

---

## Project Structure

```
src/
├── main.py              # CLI entry point (Typer + Rich)
├── orchestrator.py      # Daily loop controller
├── models.py            # Shared data models
├── brain/               # Research & keyword discovery
├── creator/             # AI image + metadata generation
├── worker/              # Pinterest posting + safety
├── analyzer/            # Performance tracking + learning
├── store/               # Database layer (Baserow + SQLite fallback)
├── diagnostic/          # AI-powered scraper self-healing
├── report/              # Cycle reports (rich CLI + file)
└── utils/               # Config, logging, constants
```

---

## Configuration Files

### config.yaml

Main configuration file for:
- Account settings
- Browser configuration
- Niche keywords and categories
- Posting schedule
- AI provider settings
- Safety limits
- Content strategy

### .env

Environment variables (never commit this file):
- API keys (Groq, Baserow)
- Pinterest credentials
- Optional fallback API keys

---

## Safety Features

- **Anti-detection**: Uses Playwright stealth with randomized delays
- **Shadowban check**: Monitors pin visibility after posting
- **Daily limits**: Configurable caps on actions per day
- **Proxy rotation**: Support for proxy rotation (configure in config.yaml)
- **Cooldown mode**: Automatic cooldown if issues detected

---

## Troubleshooting

### Common Issues

**Playwright browser not found**
```bash
playwright install chromium
```

**Database connection error**
- Verify Baserow token and database ID in `.env`
- Check that all required tables exist in Baserow

**API rate limits**
- Groq free tier: ~30 requests/minute
- Reduce `max_images_per_day` in config.yaml if needed

**Pinterest login fails**
- Ensure credentials in `.env` are correct
- Try manual login first to verify account
- Check if 2FA is enabled (may need app password)

---

## Documentation

- [BEGINNERS_GUIDE_EN.md](BEGINNERS_GUIDE_EN.md) — Step-by-step walkthrough for new users
- [BEGINNERS_GUIDE_AR.md](BEGINNERS_GUIDE_AR.md) — دليل المبتدئين باللغة العربية
- [BEGINNERS_GUIDE_FR.md](BEGINNERS_GUIDE_FR.md) — Guide du débutant en français

---

## License

MIT License — feel free to use and modify for your needs.
