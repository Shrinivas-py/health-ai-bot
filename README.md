# Health AI WhatsApp Bot

A smart WhatsApp bot that provides AI-powered health advice and symptom analysis using Twilio and Flask.

## Features

- 🩺 **Symptom Analysis**: AI-powered health symptom evaluation
- 🚨 **Emergency Detection**: Identifies urgent medical situations
- 💬 **WhatsApp Integration**: Works seamlessly with WhatsApp via Twilio
- 📊 **User Analytics**: Tracks conversations and provides insights
- 🔒 **Privacy Focused**: Secure handling of health information

## Quick Start

1. **Clone Repository**
   ```bash
   git clone https://github.com/Shrinivas-py/health-ai-whatsapp-bot.git
   cd health-ai-whatsapp-bot
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Add your Twilio credentials

4. **Run Locally**
   ```bash
   python src/whatsapp_bot.py
   ```

## Deployment

This bot is configured for easy deployment on:
- ✅ **Render** (Free tier available)
- ✅ **Railway** ($5/month free credits)
- ✅ **Heroku** (Paid plans)

See `RENDER_DEPLOYMENT.md` for detailed deployment instructions.

## Environment Variables

```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=whatsapp:+1234567890
FLASK_DEBUG=False
```

## Project Structure

```
health-ai-whatsapp-bot/
├── src/
│   ├── whatsapp_bot.py    # Main Flask app and webhook handler
│   ├── health_ai.py       # AI symptom analysis engine
│   ├── database.py        # SQLite database management
│   └── utils.py           # Utility functions
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── Procfile              # Railway/Heroku deployment
└── README.md             # This file
```

## Testing

Run the complete test suite:
```bash
python test_complete.py
```

## Support

For issues or questions, please create an issue on GitHub.

---

**Made with ❤️ for healthcare accessibility**