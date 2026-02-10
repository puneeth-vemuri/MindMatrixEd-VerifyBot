import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import random
import smtplib
from email.message import EmailMessage
import asyncio
from discord.ext import tasks

# ---------------- LOAD ENV ---------------- #

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

EMAIL = os.getenv("EMAIL_ADDRESS")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

VERIFIED_ROLE = os.getenv("VERIFIED_ROLE")
ADMIN_LOG_CHANNEL = os.getenv("ADMIN_LOG_CHANNEL")

VERIFY_CHANNEL = "verify"

# ---------------- BOT SETUP ---------------- #

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

otp_store: dict[int, int] = {}

# ---------------- EMAIL FUNCTION ---------------- #

def send_otp(email: str, otp: int):
    msg = EmailMessage()
    msg["Subject"] = "Discord Verification Code"
    msg["From"] = EMAIL
    msg["To"] = email

    msg.set_content(
        f"""
Your Discord verification code is:

{otp}

If you didn’t request this, ignore it.
"""
    )

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(EMAIL, EMAIL_PASS)
        server.send_message(msg)

# ---------------- READY EVENT ---------------- #

@bot.event
async def on_ready():
    await tree.sync()
    cleanup_verify_channel.start()
    print(f"✅ Logged in as {bot.user}")

# ---------------- AUTO CLEAN VERIFY CHANNEL ---------------- #

@tasks.loop(minutes=5)
async def cleanup_verify_channel():
    await bot.wait_until_ready()

    for guild in bot.guilds:
        channel = discord.utils.get(guild.text_channels, name=VERIFY_CHANNEL)

        if not channel:
            continue

        try:
            async for msg in channel.history(limit=100):
                if msg.pinned:
                    continue
                await msg.delete()

        except discord.Forbidden:
            print("❌ Missing permission to delete messages in #verify")

        except Exception as e:
            print("Cleanup error:", e)

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

        # 🔥 Run SMTP in background thread
        await asyncio.to_thread(send_otp, email, otp)

        await interaction.user.send(
            "✅ OTP sent! Use `/otp <code>` in the server."
        )

    except asyncio.TimeoutError:
        await interaction.user.send(
            "⏰ Timed out. Run /verify again."
        )

    except Exception as e:
        await interaction.user.send(
            f"❌ Failed to send email: {e}"
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

    # ---- Admin Log ---- #

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
