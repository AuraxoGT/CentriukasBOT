import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from aiohttp import web
import os

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Simple web server to keep Render happy
async def handle(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await start_web_server()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="atidefinti", description="Priversti asmenį atsidefinti.")
@app_commands.describe(target_user="Pasirinkite asmenį")
async def atidefinti(interaction: discord.Interaction, target_user: discord.Member):
    await interaction.response.defer(ephemeral=True)

    if not target_user.voice or not target_user.voice.channel:
        await interaction.followup.send("❌ Asmuo nėra voice chate.")
        return

    original_channel = target_user.voice.channel
    guild = interaction.guild
    temp_channels = []

    try:
        for i in range(5):
            channel = await guild.create_voice_channel(name=f"Temp VC {i+1}")
            temp_channels.append(channel)

        loop_count = 0
        while target_user.voice and target_user.voice.self_deaf and loop_count < 30:
            loop_count += 1
            for channel in temp_channels:
                if not target_user.voice or not target_user.voice.channel:
                    break
                if not target_user.voice.self_deaf:
                    break
                await target_user.move_to(channel)
                await asyncio.sleep(1.2)

        if target_user.voice:
            await target_user.move_to(original_channel)

        if target_user.voice and not target_user.voice.self_deaf:
            await interaction.followup.send("✅ Asmuo atsidefino ir buvo gražintas.")
        else:
            await interaction.followup.send("⚠️ Asmuo neatsidefino per nustatyta laiką.")

    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {e}")

    finally:
        await asyncio.sleep(1)
        for channel in temp_channels:
            try:
                await channel.delete()
            except:
                pass

# Run the bot using the token from environment variable
bot.run(os.environ["DISCORD_BOT_TOKEN"])
