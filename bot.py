import threading
import os
import discord
from discord.ext import commands
from flask import Flask, request
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load your environment variables
TOKEN = os.getenv("DISCORD_TOKEN")
KICK_CLIENT_ID = os.getenv("CLIENT_ID")
REDIRECT_URI = os.getenv("REDIRECT_URI")
LOG_CHANNEL_ID = 1394430417951653929  # Your channel ID as an integer

# Initialize Discord bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # To read message content in DMs
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize Flask app
app = Flask(__name__)

# Flask route to check if the server is running
@app.route("/")
def home():
    return "Flask app is running!"

# Flask callback route to handle Kick OAuth redirect
@app.route("/callback")
def callback():
    # Log when the callback URL is hit
    print("Callback route hit!")

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return "Missing code or state", 400

    # Handle code exchange and token retrieval here...
    # For now, let's just show what was received
    return f"Received code: {code}, state: {state}"

# **This is where you place the Flask running code**
def run_flask():
    app.run(host="0.0.0.0", port=8080)  # Listen on all IPs

# Discord bot event when ready
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

# Discord bot event when a new member joins
@bot.event
async def on_member_join(member):
    if member.bot:
        return

    oauth_url = (
        f"https://kick.com/oauth/authorize?"
        f"client_id={KICK_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=user.read chat:read&"
        f"state={member.id}&"
        f"prompt=consent"
    )
    
    try:
        await member.send(
            f"Welcome to the server!\n"
            f"1. Click here to link your Kick account: {oauth_url}\n"
            f"2. After that, please reply here with your CSGOStake ID, CSGOGem ID, and Upgrader ID separated by spaces."
        )
    except discord.Forbidden:
        print(f"Cannot send DM to {member.name}")

# Discord bot event when a message is received
@bot.event
async def on_message(message):
    if message.guild is None and not message.author.bot:
        ids = message.content.split()
        if len(ids) == 3:
            csgostake_id, csgogem_id, upgrader_id = ids

            # Log the IDs to your specific channel
            channel = bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"User {message.author} sent IDs:\n"
                    f"CSGOStake ID: {csgostake_id}\n"
                    f"CSGOGem ID: {csgogem_id}\n"
                    f"Upgrader ID: {upgrader_id}"
                )
            else:
                print(f"Log channel with ID {LOG_CHANNEL_ID} not found!")

            await message.channel.send("Thanks! Your IDs have been recorded.")
        else:
            await message.channel.send("Please send exactly 3 IDs separated by spaces.")
    await bot.process_commands(message)

# Command to manually send Kick linking URL via Discord DM
@bot.command()
async def sendlink(ctx):
    member = ctx.author

    oauth_url = (
        f"https://kick.com/oauth/authorize?"
        f"client_id={KICK_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=user.read chat:read&"
        f"state={member.id}"
    )

    try:
        await member.send(
            f"Welcome! Click this link to link your Kick account:\n{oauth_url}\n"
            "After linking, reply here with your CSGOStake ID, CSGOGem ID, and Upgrader ID separated by spaces."
        )
        await ctx.send("I've sent you a DM with the Kick linking link!")
    except discord.Forbidden:
        await ctx.send("I can't send you a DM. Please enable DMs from server members.")

# Run both Flask and the Discord bot using threading
if __name__ == "__main__":
    # Start Flask app in a separate thread
    threading.Thread(target=run_flask).start()

    # Run the Discord bot (this blocks, so it needs to run after Flask starts)
    bot.run(TOKEN)