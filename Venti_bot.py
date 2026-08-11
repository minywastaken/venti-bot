
import json
import os
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import discord
from discord.ext import commands
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Dummy web server to satisfy Render's port check
server = HTTPServer(('0.0.0.0', 10000), SimpleHTTPRequestHandler)
threading.Thread(target=server.serve_forever, daemon=True).start()
# ==================== CONFIGURATION & DATA ====================
# Track message counts in memory (or store in your existing JSON data)
user_message_counts={5}

DATA_FILE = "user_data.json"

WINE_BOTTLES = [
    {
        "name": "Apple Cider (Non-alcoholic)",
        "rarity": "3-Star 🍏",
        "min_primos": 50,
        "max_primos": 100,
        "chance": 50,
        "color": 0x7289DA,
        "image": "https://static.wikia.nocookie.net/gensin-impact/images/0/03/Item_Apple_Cider.png",
    },
    {
        "name": "Wolfhook Juice",
        "rarity": "3-Star 🫐",
        "min_primos": 100,
        "max_primos": 200,
        "chance": 30,
        "color": 0x9B59B6,
        "image": "https://static.wikia.nocookie.net/gensin-impact/images/a/a2/Item_Wolfhook_Juice.png",
    },
    {
        "name": "Mondstadt Dandelion Wine",
        "rarity": "4-Star 🍾",
        "min_primos": 200,
        "max_primos": 500,
        "chance": 15,
        "color": 0xA020F0,
        "image": "https://static.wikia.nocookie.net/gensin-impact/images/4/4e/Item_Dandelion_Wine.png",
    },
    {
        "name": "Dawn Winery Reserve (Vintage 100-Year)",
        "rarity": "5-Star 🌟👑",
        "min_primos": 600,
        "max_primos": 1600,
        "chance": 5,
        "color": 0xF1C40F,
        "image": "https://i.imgur.com/vHqB12x.png",
    },
]

# ==================== DATA HELPER FUNCTIONS ====================
def load_data() -> Dict[str, Dict[str, Any]]:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(data: Dict[str, Dict[str, Any]]) -> None:
    """Saves the user database to disk."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_random_wine() -> Dict[str, Any]:
    """Rolls a weighted random wine bottle based on drop chances."""
    roll = random.randint(1, 100)
    cumulative = 0
    for wine in WINE_BOTTLES:
        cumulative += wine["chance"]
        if roll <= cumulative:
            return wine
    return WINE_BOTTLES[0]

# ==================== COGS / COMMANDS ====================

class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """

        :type bot: commands.Bot_client
        """
        self.bot = bot

    @commands.command(name="daily")
    async def daily(self, ctx: commands.Context):
        """Claims daily Primogems with a Venti-themed wine roll."""
        user_id = str(ctx.author.id)
        data = load_data()
        now = datetime.now(timezone.utc)

        # Initialize missing user profile
        user_profile = data.setdefault(user_id, {"primos": 0, "last_daily": None})

        # Cooldown check
        if user_profile["last_daily"]:
            last_claim = datetime.fromisoformat(user_profile["last_daily"])
            time_passed = now - last_claim

            if time_passed < timedelta(hours=24):
                time_remaining = timedelta(hours=24) - time_passed
                hours, remainder = divmod(int(time_remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)

                await ctx.send(
                    f"🎵 *“Wouldn't gliding be faster?”* You already opened a bottle today, traveler! "
                    f"Come back in **{hours}h {minutes}m**."
                )
                return

        # Roll reward
        selected_wine = get_random_wine()
        primos_won = random.randint(selected_wine["min_primos"], selected_wine["max_primos"])

        # Update profile
        user_profile["primos"] += primos_won
        user_profile["last_daily"] = now.isoformat()
        save_data(data)

        # Build response embed
        embed = discord.Embed(
            title=f"🍷 Venti served you: {selected_wine['name']}!",
            description=(
                f"_*\"Ehehe, popped the cork and look what popped out!\"*_\n\n"
                f"**Rarity:** {selected_wine['rarity']}\n"
                f"**Primogems Inside:** **+{primos_won}** 💎\n"
                f"**Total Balance:** {user_profile['primos']} Primogems"
            ),
            color=selected_wine["color"],
        )
        embed.set_thumbnail(url=selected_wine["image"])
        embed.set_footer(text="The Anemo Nation Tavern • Use !balance to check your wallet")

        await ctx.send(embed=embed)


# ==================== BOT SETUP & INITIALIZATION ====================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    user_message_counts[user_id] = user_message_counts.get(user_id, 0) + 1

    await bot.process_commands(message)

@bot.event
async def on_ready():
  if bot.user:
    print(f"Ehehe~ {bot.user.name} has arrived at the Angel's Share!")


async def main():
    async with bot:
        await bot.add_cog(EconomyCog(bot))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    bot.run(os.evinron.get("DISCORD_TOKEN"))
