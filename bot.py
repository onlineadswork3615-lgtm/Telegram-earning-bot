import telebot
from datetime import datetime
import json
import os

# ==========================================
# এখানে ৩টা জিনিস বসাও
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "এখানে_তোমার_bot_token_বসাও")
ADSTERRA_LINK = os.environ.get("ADSTERRA_LINK", "এখানে_তোমার_adsterra_link_বসাও")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "users.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or "User"
    username = message.from_user.username or ""
    
    referral_by = None
    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("ref_"):
        referral_by = parts[1].replace("ref_", "")
    
    db = load_db()
    
    if user_id not in db:
        db[user_id] = {
            "username": username,
            "first_name": first_name,
            "points": 0,
            "total_earned": 0,
            "referral_by": referral_by,
            "referral_count": 0,
            "join_date": datetime.now().isoformat(),
            "checkin_date": None
        }
        
        if referral_by and referral_by in db:
            db[referral_by]["points"] += 50
            db[referral_by]["total_earned"] += 50
            db[referral_by]["referral_count"] += 1
            try:
                bot.send_message(int(referral_by), "🎁 নতুন referral থেকে +50 points!")
            except:
                pass
        
        save_db(db)
        bot.reply_to(message,
            f"👋 Welcome {first_name}!\n\n"
            f"💰 টাস্ক করে আয় করো\n"
            f"🎁 Referral bonus: 50 points\n\n"
            f"📋 Commands:\n"
            f"/tasks — টাস্ক দেখো\n"
            f"/balance — ব্যালেন্স\n"
            f"/checkin — Daily bonus\n"
            f"/refer — Referral link\n"
            f"/withdraw — Withdraw"
        )
    else:
        bot.reply_to(message, f"👋 Welcome back {first_name}!\n\n/balance — ব্যালেন্স দেখো")

@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    if user_id not in db:
        bot.reply_to(message, "❌ প্রথমে /start দাও")
        return
    
    points = db[user_id]["points"]
    usd = round(points / 1000, 4)
    remaining = max(0, 5000 - points)
    
    bot.reply_to(message,
        f"💰 Your Balance\n\n"
        f"Points: {points}\n"
        f"Value: ${usd}\n"
        f"Min Withdraw: 5000 pts ($5)\n\n"
        f"আরো {remaining} points লাগবে"
    )

@bot.message_handler(commands=['tasks'])
def tasks(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    if user_id not in db:
        bot.reply_to(message, "❌ প্রথমে /start দাও")
        return
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton("📺 Ad Watch (+10 pts)", url=ADSTERRA_LINK)
    keyboard.add(btn)
    
    bot.reply_to(message,
        f"📋 Available Tasks:\n\n"
        f"1️⃣ Ad Watch (৩০ সেকেন্ড)\n"
        f"   Reward: 10 points\n"
        f"   👇 Button-এ ক্লিক করো\n\n"
        f"⚠️ ৩০ সেকেন্ড পরে /adcomplete দাও",
        reply_markup=keyboard
    )

@bot.message_handler(commands=['adcomplete'])
def adcomplete(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    if user_id not in db:
        bot.reply_to(message, "❌ প্রথমে /start দাও")
        return
    
    db[user_id]["points"] += 10
    db[user_id]["total_earned"] += 10
    save_db(db)
    
    bot.reply_to(message,
        f"✅ +10 points যোগ হয়েছে!\n"
        f"💰 নতুন Balance: {db[user_id]['points']} pts"
    )

@bot.message_handler(commands=['checkin'])
def checkin(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    if user_id not in db:
        bot.reply_to(message, "❌ প্রথমে /start দাও")
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    if db[user_id].get("checkin_date") == today:
        bot.reply_to(message, "⏰ আজকের check-in আগেই করেছো! কাল আসো")
        return
    
    db[user_id]["points"] += 5
    db[user_id]["total_earned"] += 5
    db[user_id]["checkin_date"] = today
    save_db(db)
    
    bot.reply_to(message,
        f"✅ Daily Check-in Complete!\n"
        f"🎁 +5 points\n"
        f"💰 Balance: {db[user_id]['points']} pts"
    )

@bot.message_handler(commands=['refer'])
def refer(message):
    user_id = str(message.from_user.id)
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    bot.reply_to(message,
        f"🎁 Your Referral Link:\n\n"
        f"{ref_link}\n\n"
        f"প্রতিটা referral-এ 50 points!"
    )

@bot.message_handler(commands=['withdraw'])
def withdraw(message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    if user_id not in db:
        bot.reply_to(message, "❌ প্রথমে /start দাও")
        return
    
    points = db[user_id]["points"]
    
    if points < 5000:
        bot.reply_to(message,
            f"❌ Minimum 5000 points লাগবে\n"
            f"তোমার: {points} pts\n"
            f"আরো {5000 - points} pts দরকার"
        )
        return
    
    bot.reply_to(message,
        f"✅ তুমি eligible!\n\n"
        f"User ID: {user_id}\n"
        f"Points: {points}\n"
        f"Value: ${round(points/1000, 2)}\n\n"
        f"Admin-কে message দাও: @tousifkhan3615"
    )

@bot.message_handler(commands=['admin_stats'])
def admin_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    db = load_db()
    total_users = len(db)
    total_points = sum(u["points"] for u in db.values())
    
    bot.reply_to(message,
        f"📊 Bot Stats\n\n"
        f"Total Users: {total_users}\n"
        f"Total Points: {total_points}\n"
        f"Pending $: ${round(total_points/1000, 2)}"
    )

print("🤖 Bot started...")
bot.infinity_polling()
