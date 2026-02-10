# 📧 Discord Email Verification Bot (OTP-Based)

A production-ready Discord verification bot that uses **slash commands**, **ephemeral replies**, and **email OTP authentication** to verify users and automatically assign roles.

Built for cloud deployment (Railway / Fly.io) using an **email API (Brevo)** instead of SMTP to avoid blocked ports and rate-limit issues.

---

## 🚀 Features

- ✅ Slash commands (`/verify`, `/otp`)
- 🔒 Ephemeral responses (“Only you can see this”)
- 📩 Email OTP verification
- 🔑 Automatic role assignment
- 📝 Admin log channel
- ☁️ Cloud-safe (no SMTP)
- ⚡ Async-friendly (no event-loop blocking)
- 🧪 Free-tier friendly email provider

---

## 🧠 Verification Flow

```
User → /verify
        ↓
Bot replies privately → “Check your DMs”
        ↓
User sends email in DM
        ↓
OTP sent via email API
        ↓
User → /otp 123456
        ↓
Role assigned → Logged in admin channel
```

---

## 🛠 Tech Stack

- Python 3.10+
- discord.py (slash commands / app_commands)
- Brevo Email API
- Railway / Fly.io hosting
- python-dotenv
- requests

---

## 📂 Project Structure

```
discord-verify-bot/
│
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 📦 requirements.txt

```
discord.py
python-dotenv
requests
```

---

## 🔐 Environment Variables

Create these in Railway (or locally in `.env`):

```
DISCORD_TOKEN=your_bot_token

BREVO_API_KEY=xkeysib-xxxxxxx
EMAIL_ADDRESS=verified_sender@gmail.com

VERIFIED_ROLE=Verified
ADMIN_LOG_CHANNEL=admin-logs
```

⚠️ `EMAIL_ADDRESS` must be verified inside Brevo.

---

## 🤖 Discord Setup

### 1️⃣ Bot Permissions

Give the bot:

- ✅ Manage Roles
- ✅ Send Messages
- ✅ Read Message History
- ✅ Use Application Commands
- ✅ Embed Links

Make sure:

📌 **Bot role is above the Verified role** in server settings.

---

### 2️⃣ Channels

Create:

- `#verify`
- `#admin-logs`

---

### 3️⃣ OAuth2 Scopes (Important)

In Discord Developer Portal → OAuth2 → URL Generator:

- ☑️ `bot`
- ☑️ `applications.commands`

Invite the bot again after changing scopes.

---

## 📩 Email Provider Setup (Brevo)

1. Go to https://app.brevo.com  
2. Create API key  
3. Add & verify sender email  
4. Put API key + sender email in Railway variables  
5. Redeploy

Free tier: **300 emails/day**.

---

## ▶️ Run Locally

Install dependencies:

```
pip install -r requirements.txt
```

Run:

```
python main.py
```

---

## ☁️ Deploy to Railway

1. Push repo to GitHub  
2. Create Railway project → Deploy from GitHub  
3. Add environment variables  
4. Set start command:

```
python main.py
```

5. Deploy 🚀

---

## 📄 Resume-Ready Description

> Built a cloud-hosted Discord verification bot using Python and slash commands with email OTP authentication, ephemeral UI, API-based email delivery, and automated role management.

---

## 🔮 Possible Upgrades

- OTP expiry timers  
- `/resend` command  
- Rate limiting  
- Database storage (SQLite / Redis / MongoDB)  
- Auto-kick unverified users  
- Domain-restricted emails  
- Admin dashboard  
- Analytics panel  

---

## 🧑‍💻 Author  
Built by Puneeth Vemuri
