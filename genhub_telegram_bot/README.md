# GenHub Works Telegram Bot — MVP

This starter bot includes:

- `/start` welcome menu
- Services listing
- Hire Talent requirement form
- SQLite storage
- Admin notification for new requirements
- Freelancer and contact guidance

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your values:

- `BOT_TOKEN`: token from BotFather
- `ADMIN_CHAT_ID`: your Telegram user/chat ID, so the bot can notify you
- `DB_PATH`: optional SQLite database path

Start the bot:

```bash
python bot.py
```

Never commit `.env` or expose your bot token publicly.
