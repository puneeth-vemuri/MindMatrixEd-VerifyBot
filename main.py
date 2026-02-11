import discord
from discord import app_commands, ui
from dotenv import load_dotenv
import os
import random
import asyncio
import requests

# ---------------- LOAD ENV ---------------- #
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_SENDER = os.getenv("EMAIL_ADDRESS")
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
VERIFIED_ROLE = os.getenv("VERIFIED_ROLE")
ADMIN_LOG_CHANNEL = os.getenv("ADMIN_LOG_CHANNEL")

# ---------------- BOT SETUP ---------------- #
intents = discord.Intents.default()
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

otp_store: dict[int, int] = {}

def send_otp_via_api(email: str, otp: int):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {"api-key": BREVO_API_KEY, "Content-Type": "application/json"}
    payload = {
        "sender": {"name": "MindMatrixEd VerifyBot", "email": EMAIL_SENDER},
        "to": [{"email": email}],
        "subject": "Discord Verification Code",
        "htmlContent": f"<h2>Your Discord OTP</h2><p>Your code is: <h1>{otp}</h1></p>",
    }
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    response.raise_for_status()

# ---------------- MODAL FOR EMAIL ---------------- #
class EmailModal(ui.Modal, title='Email Verification'):
    email = ui.TextInput(label='Enter your email address', placeholder='email@example.com')

    async def on_submit(self, interaction: discord.Interaction):
        otp = random.randint(100000, 999999)
        otp_store[interaction.user.id] = otp
        
        # Prevent blocking the interaction while sending email
        await interaction.response.send_message(f"📧 Sending OTP to **{self.email.value}**...", ephemeral=True)
        
        try:
            await asyncio.to_thread(send_otp_via_api, self.email.value, otp)
            await interaction.edit_original_response(content=f"✅ OTP sent to **{self.email.value}**! Use `/otp` here to verify.")
        except Exception as e:
            await interaction.edit_original_response(content=f"❌ Failed to send email: {e}")

# ---------------- EVENTS & COMMANDS ---------------- #
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

@tree.command(name="verify", description="Verify your email address")
async def verify(interaction: discord.Interaction):
    # This opens the pop-up window in the channel
    await interaction.response.send_modal(EmailModal())

@tree.command(name="otp", description="Submit your OTP code")
@app_commands.describe(code="Your 6-digit OTP")
async def otp(interaction: discord.Interaction, code: int):
    if interaction.guild is None:
        return await interaction.response.send_message("❌ Use this in the server.", ephemeral=True)

    if interaction.user.id not in otp_store:
        return await interaction.response.send_message("❌ Run /verify first.", ephemeral=True)

    if otp_store[interaction.user.id] != code:
        return await interaction.response.send_message("❌ Invalid OTP.", ephemeral=True)

    role = discord.utils.get(interaction.guild.roles, name=VERIFIED_ROLE)
    if not role:
        return await interaction.response.send_message("❌ Role not found.", ephemeral=True)

    try:
        await interaction.user.add_roles(role)
        del otp_store[interaction.user.id]
        await interaction.response.send_message("🎉 You are now verified!", ephemeral=True)
        
        log_channel = discord.utils.get(interaction.guild.text_channels, name=ADMIN_LOG_CHANNEL)
        if log_channel:
            await log_channel.send(f"✅ {interaction.user.mention} verified successfully.")
    except discord.Forbidden:
        await interaction.response.send_message("❌ I can't assign roles. Check my permissions!", ephemeral=True)

# ---------------- HELP COMMAND ---------------- #
@tree.command(name="help", description="Show the help menu")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎓 Mind Matrix Bot Help",
        description="Welcome to the Mind Matrix Discord Bot!\n\n**Verification Steps:**",
        color=discord.Color.blue()
    )
    embed.add_field(name="1️⃣ Step One", value="Use `/verify` to open the email prompt.", inline=False)
    embed.add_field(name="2️⃣ Step Two", value="Check your email for the 6-digit OTP code.", inline=False)
    embed.add_field(name="3️⃣ Step Three", value="Use `/otp <code>` to finish verification.", inline=False)
    
    # Adding a button for quick access
    view = ui.View()
    button = ui.Button(label="Start Verification", style=discord.ButtonStyle.primary, custom_id="verify_btn")
    
    # Simple callback for the button to trigger the same /verify logic
    async def button_callback(btn_interaction):
        await btn_interaction.response.send_modal(EmailModal())
    
    button.callback = button_callback
    view.add_item(button)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

bot.run(TOKEN)
