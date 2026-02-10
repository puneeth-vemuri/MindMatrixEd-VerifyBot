import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import random
import asyncio
import requests

# ---------------- LOAD ENV ---------------- #

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

EMAIL_SENDER = os.getenv("EMAIL_ADDRESS")  # verified in Brevo
BREVO_API_KEY = os.getenv("BREVO_API_KEY")

VERIFIED_ROLE = os.getenv("VERIFIED_ROLE")
ADMIN_LOG_CHANNEL = os.getenv("ADMIN_LOG_CHANNEL")

# ---------------- BOT SETUP ---------------- #

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

otp_store: dict[int, int] = {}

# ---------------- EMAIL VIA BREVO API ---------------- #

def send_otp_via_api(email: str, otp: int):

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "sender": {
            "name": "MindMatrixEd VerifyBot",
            "email": EMAIL_SENDER,
        },
        "to": [{"email": email}],
        "subject": "Discord Verification Code",
        "htmlContent": f"""
        <h2>Your Discord OTP</h2>
        <p>Your verification code is:</p>
        <h1>{otp}</h1>
        <p>If you didn't request this, ignore it.</p>
        """,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=10,
    )

    response.raise_for_status()

# ---------------- READY EVENT ---------------- #

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ---------------- SLASH COMMANDS ---------------- #

# /verify
@tree.command(name="verify", description="Verify your email address")
async def verify(interaction: discord.Interaction):

    await interaction.response.send_message(
        "📧 Check your DMs to continue verification.",
        ephemeral=True,
    )

    await interaction.user.send(
        "📧 Please reply with your email address for verification."
    )

    def check(m):
        return (
            m.author == interaction.user
            and isinstance(m.channel, discord.DMChannel)
        )

    try:
        email_msg = await bot.wait_for("message", timeout=120, check=check)
        email = email_msg.content.strip()

        otp = random.randint(100000, 999999)
        otp_store[interaction.user.id] = otp

        # Run HTTP call in background thread
        await asyncio.to_thread(send_otp_via_api, email, otp)

        await interaction.user.send(
            "✅ OTP sent! Use `/otp <code>` in the server."
        )

    except asyncio.TimeoutError:
        await interaction.user.send(
            "⏰ Timed out. Run /verify again."
        )

    except Exception as e:
        await interaction.user.send(
            f"❌ Failed to send email. Contact admin.\n{e}"
        )

# /otp
@tree.command(name="otp", description="Submit your OTP code")
@app_commands.describe(code="Your 6-digit OTP")
async def otp(interaction: discord.Interaction, code: int):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Use this inside the server.",
            ephemeral=True,
        )
        return

    if interaction.user.id not in otp_store:
        await interaction.response.send_message(
            "❌ Run /verify first.",
            ephemeral=True,
        )
        return

    if otp_store[interaction.user.id] != code:
        await interaction.response.send_message(
            "❌ Invalid OTP.",
            ephemeral=True,
        )
        return

    role = discord.utils.get(
        interaction.guild.roles,
        name=VERIFIED_ROLE,
    )

    if not role:
        await interaction.response.send_message(
            "❌ Verified role not found. Contact admin.",
            ephemeral=True,
        )
        return

    try:
        await interaction.user.add_roles(role)

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ I don't have permission to assign roles.",
            ephemeral=True,
        )
        return

    del otp_store[interaction.user.id]

    await interaction.response.send_message(
        "🎉 You are now verified!",
        ephemeral=True,
    )

    log_channel = discord.utils.get(
        interaction.guild.text_channels,
        name=ADMIN_LOG_CHANNEL,
    )

    if log_channel:
        await log_channel.send(
            f"✅ {interaction.user.mention} verified successfully."
        )

# ---------------- RUN ---------------- #

bot.run(TOKEN)
