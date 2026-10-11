import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from datetime import datetime, timedelta
import json
import os

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
ADSTERRA_LINK = os.environ.get("ADSTERRA_LINK", "YOUR_ADSTERRA_LINK")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://onlineadswork3615-igtm.github.io/Telegram-earning-bot/")

bot = telebot.TeleBot(BOT_TOKEN)

# ========== FILES ==========
USERS_FILE = "users.json"
TASKS_FILE = "tasks.json"
WITHDRAWS_FILE = "withdraws.json"
COMPLETIONS_FILE = "completions.json"

# ========== HELPER FUNCTIONS ==========
def load(file):
    if not os.path.exists(file):
        return {} if file != "tasks.json" else {"tasks": []}
    try:
        with open(file, 'r') as f:
            return json.load(f)
    except:
        return {} if file != "tasks.json" else {"tasks": []}

def save(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def today():
    return datetime.now().strftime("%Y-%m-%d")

def now():
    return datetime.now().isoformat()

# ========== DEFAULT TASKS (প্রথমবার চালু হলে) ==========
def init_default_tasks():
    data = load(TASKS_FILE)
    if not data["tasks"]:
        data["tasks"] = [
            {
                "id": 1,
                "title": "📺 Ad Watch",
                "desc": "৩০ সেকেন্ড ad দেখো",
                "reward": 10,
                "type": "ad",
                "link": ADSTERRA_LINK,
                "frequency": "daily",
                "status": "active"
            },
            {
                "id": 2,
                "title": "✅ Daily Check-in",
                "desc": "প্রতিদিন একবার",
                "reward": 5,
                "type": "checkin",
                "link": "",
                "frequency": "daily",
                "status": "active"
            },
            {
                "id": 3,
                "title": "📢 Join Channel",
                "desc": "Official channel join করো",
                "reward": 20,
                "type": "link",
                "link": "https://t.me/quickearnbd_official",
                "frequency": "once",
                "status": "active"
            }
        ]
        save(TASKS_FILE, data)

# ========== /start ==========
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or "User"
    
    # Referral check
    referral_by = None
    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("ref_"):
        referral_by = parts[1].replace("ref_", "")
    
    users = load(USERS_FILE)
    
    if user_id not in users:
        users[user_id] = {
            "name": first_name,
            "username": message.from_user.username or "",
            "points": 0,
            "total_earned": 0,
            "referral_by": referral_by,
            "referral_count": 0,
            "join_date": now(),
            "checkin": None,
            "banned": False
        }
        
        # Referral bonus
        if referral_by and referral_by in users and not users[referral_by].get("banned"):
            users[referral_by]["points"] += 50
            users[referral_by]["total_earned"] += 50
            users[referral_by]["referral_count"] += 1
            try:
                bot.send_message(int(referral_by), "🎁 নতুন referral! +50 points")
            except:
                pass
        
        save(USERS_FILE, users)
        
        # Welcome with WebApp button
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🚀 Open App", web_app=WebAppInfo(url=WEBAPP_URL)))
        
        bot.reply_to(message,
            f"👋 Welcome {first_name}!\n\n"
            f"💰 Task করে daily আয় করো\n"
            f"🎁 Referral: 50 points per friend\n"
            f"💸 Min withdraw: 5000 pts ($5)\n\n"
            f"👇 নিচের button-এ ক্লিক করো",
            reply_markup=kb
        )
    else:
        bot.reply_to(message, f"👋 Welcome back {first_name}!\n\n/balance — Balance")

# ========== /balance ==========
@bot.message_handler(commands=['balance'])
def balance(message):
    user_id = str(message.from_user.id)
    users = load(USERS_FILE)
    
    if user_id not in users:
        bot.reply_to(message, "❌ প্রথমে /start দাও")
        return
    
    u = users[user_id]
    points = u["points"]
    usd = round(points / 1000, 4)
    refs = u.get("referral_count", 0)
    
    bot.reply_to(message,
        f"💰 Your Balance\n\n"
        f"Points: {points}\n"
        f"Value: ${usd}\n"
        f"Referrals: {refs}\n"
        f"Min Withdraw: 5000 pts ($5)\n\n"
        f"আরো {max(0, 5000 - points)} points লাগবে"
    )

# ========== /tasks ==========
@bot.message_handler(commands=['tasks'])
def tasks_cmd(message):
    user_id = str(message.from_user.id)
    users = load(USERS_FILE)
    
    if user_id not in users:
        bot.reply_to(message, "❌ প্রথমে /start দাও")
        return
    
    data = load(TASKS_FILE)
    tasks = [t for t in data["tasks"] if t["status"] == "active"]
    
    if not tasks:
        bot.reply_to(message, "😔 এখন কোনো task নেই। পরে আবার দেখো")
        return
    
    completions = load(COMPLETIONS_FILE)
    user_done = completions.get(user_id, {})
    today_str = today()
    
    text = "📋 Available Tasks:\n\n"
    kb = InlineKeyboardMarkup()
    
    for t in tasks:
        tid = str(t["id"])
        freq = t.get("frequency", "daily")
        
        # Check completion
        done = False
        if freq == "daily":
            done = user_done.get(tid, {}).get("date") == today_str
        else:
            done = user_done.get(tid, {}).get("done") == True
        
        status = "✅" if done else "🆕"
        text += f"{status} {t['title']}\n   Reward: {t['reward']} pts\n\n"
        
        if not done:
            if t["type"] == "link":
                kb.add(InlineKeyboardButton(f"{t['title']} (+{t['reward']})", url=t["link"]))
            else:
                kb.add(InlineKeyboardButton(f"{t['title']} (+{t['reward']})", callback_data=f"task_{t['id']}"))
    
    kb.add(InlineKeyboardButton("🚀 Open Full App", web_app=WebAppInfo(url=WEBAPP_URL)))
    
    bot.reply_to(message, text + "👇 Task-এ ক্লিক করো", reply_markup=kb)

# ========== CALLBACK (Task Click) ==========
@bot.callback_query_handler(func=lambda call: call.data.startswith("task_"))
def handle_task(call):
    user_id = str(call.from_user.id)
    task_id = call.data.replace("task_", "")
    
    users = load(USERS_FILE)
    if user_id not in users or users[user_id].get("banned"):
        bot.answer_callback_query(call.id, "❌ Access denied")
        return
    
    data = load(TASKS_FILE)
    task = next((t for t in data["tasks"] if str(t["id"]) == task_id), None)
    
    if not task:
        bot.answer_callback_query(call.id, "❌ Task not found")
        return
    
    completions = load(COMPLETIONS_FILE)
    if user_id not in completions:
        completions[user_id] = {}
    
    freq = task.get("frequency", "daily")
    
    # Check if already done
    if freq == "daily":
        if completions[user_id].get(task_id, {}).get("date") == today():
            bot.answer_callback_query(call.id, "⏰ আজ আগেই করেছো! কাল আসো", show_alert=True)
            return
    else:
        if completions[user_id].get(task_id, {}).get("done"):
            bot.answer_callback_query(call.id, "✅ এটা আগেই করেছো!", show_alert=True)
            return
    
    # Complete task
    reward = task["reward"]
    
    if task["type"] == "ad":
        # For ad type, open link and give reward
        bot.answer_callback_query(call.id, "✅ Ad watched!")
        bot.send_message(call.message.chat.id,
            f"📺 Ad Watch\n\n"
            f"নিচের link-এ ক্লিক করে ৩০ সেকেন্ড থাকো:\n{task['link']}\n\n"
            f"Link-এ ক্লিক করার ৩০ সেকেন্ড পরে points auto add হবে"
        )
        # Award points
        users[user_id]["points"] += reward
        users[user_id]["total_earned"] += reward
        completions[user_id][task_id] = {"date": today(), "done": True, "completed_at": now()}
        save(USERS_FILE, users)
        save(COMPLETIONS_FILE, completions)
        bot.send_message(call.message.chat.id, f"✅ +{reward} points!\n💰 নতুন balance: {users[user_id]['points']} pts")
    
    elif task["type"] == "checkin":
        users[user_id]["points"] += reward
        users[user_id]["total_earned"] += reward
        users[user_id]["checkin"] = today()
        completions[user_id][task_id] = {"date": today(), "done": True, "completed_at": now()}
        save(USERS_FILE, users)
        save(COMPLETIONS_FILE, completions)
        bot.answer_callback_query(call.id, f"✅ +{reward} points!")
        bot.send_message(call.message.chat.id, f"✅ Daily Check-in Complete!\n🎁 +{reward} points\n💰 Balance: {users[user_id]['points']} pts")

# ========== /checkin ==========
@bot.message_handler(commands=['checkin'])
def checkin(message):
    user_id = str(message.from_user.id)
    users = load(USERS_FILE)
    
    if user_id not in users:
        bot.reply_to(message, "❌ /start দাও আগে")
        return
    
    if users[user_id].get("checkin") == today():
        bot.reply_to(message, "⏰ আজ আগেই check-in করেছো! কাল আসো")
        return
    
    users[user_id]["points"] += 5
    users[user_id]["total_earned"] += 5
    users[user_id]["checkin"] = today()
    save(USERS_FILE, users)
    
    bot.reply_to(message, f"✅ Check-in Complete!\n🎁 +5 points\n💰 Balance: {users[user_id]['points']} pts")

# ========== /refer ==========
@bot.message_handler(commands=['refer'])
def refer(message):
    user_id = str(message.from_user.id)
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    users = load(USERS_FILE)
    refs = users.get(user_id, {}).get("referral_count", 0)
    
    bot.reply_to(message,
        f"🎁 Your Referral Link:\n\n{ref_link}\n\n"
        f"প্রতিটা referral-এ 50 points!\n"
        f"তোমার total referrals: {refs}"
    )

# ========== /withdraw ==========
@bot.message_handler(commands=['withdraw'])
def withdraw(message):
    user_id = str(message.from_user.id)
    users = load(USERS_FILE)
    
    if user_id not in users:
        bot.reply_to(message, "❌ /start দাও")
        return
    
    points = users[user_id]["points"]
    
    if points < 5000:
        bot.reply_to(message,
            f"❌ Minimum 5000 points\n"
            f"তোমার: {points} pts\n"
            f"আরো {5000 - points} pts দরকার"
        )
        return
    
    bot.reply_to(message,
        f"✅ তুমি eligible!\n\n"
        f"User ID: {user_id}\n"
        f"Points: {points}\n"
        f"Value: ${round(points/1000, 2)}\n\n"
        f"Admin-কে message দাও: @tousifkhan3615\n"
        f"তোমার user ID দাও verify করার জন্য"
    )

# =============================================
# ========== ADMIN COMMANDS ==========
# =============================================

def is_admin(message):
    return message.from_user.id == ADMIN_ID

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message):
        return
    
    users = load(USERS_FILE)
    tasks_data = load(TASKS_FILE)
    withdraws = load(WITHDRAWS_FILE)
    
    active_tasks = len([t for t in tasks_data["tasks"] if t["status"] == "active"])
    pending_withdraws = len([w for w in withdraws.values() if w.get("status") == "pending"]) if isinstance(withdraws, dict) else 0
    total_points = sum(u.get("points", 0) for u in users.values())
    banned = len([u for u in users.values() if u.get("banned")])
    
    text = (
        f"👑 ADMIN PANEL\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📊 Stats:\n"
        f"👥 Total Users: {len(users)}\n"
        f"🚫 Banned: {banned}\n"
        f"📋 Active Tasks: {active_tasks}\n"
        f"💰 Total Points: {total_points}\n"
        f"💵 Pending $: ${round(total_points/1000, 2)}\n"
        f"📥 Pending Withdraws: {pending_withdraws}\n\n"
        f"🛠️ Commands:\n"
        f"/addtask — নতুন task যোগ\n"
        f"/listtasks — সব task দেখো\n"
        f"/deltask <id> — Task delete\n"
        f"/users — User list\n"
        f"/broadcast <msg> — সবকে message\n"
        f"/give <user_id> <points> — Points দাও\n"
        f"/ban <user_id> — User ban\n"
        f"/unban <user_id> — User unban"
    )
    
    bot.reply_to(message, text)

# ========== /addtask ==========
@bot.message_handler(commands=['addtask'])
def add_task(message):
    if not is_admin(message):
        return
    
    # Usage: /addtask Title | Desc | Reward | Type | Link | Frequency
    # Example: /addtask 📺 Ad Watch | 30 sec ad | 10 | ad | https://link.com | daily
    text = message.text.replace("/addtask", "").strip()
    
    if not text:
        bot.reply_to(message,
            "📝 Usage:\n"
            "/addtask Title | Desc | Reward | Type | Link | Frequency\n\n"
            "Example:\n"
            "/addtask 📺 Ad Watch | 30 sec ad দেখো | 10 | ad | https://adsterra.com/xxx | daily\n\n"
            "Type: ad / link / checkin\n"
            "Frequency: daily / once"
        )
        return
    
    parts = [p.strip() for p in text.split("|")]
    
    if len(parts) < 4:
        bot.reply_to(message, "❌ কমপক্ষে ৪টা field দাও: Title | Desc | Reward | Type")
        return
    
    title = parts[0]
    desc = parts[1]
    try:
        reward = int(parts[2])
    except:
        bot.reply_to(message, "❌ Reward সংখ্যা হতে হবে")
        return
    task_type = parts[3].lower()
    link = parts[4] if len(parts) > 4 else ""
    frequency = parts[5].lower() if len(parts) > 5 else "daily"
    
    if task_type not in ["ad", "link", "checkin"]:
        bot.reply_to(message, "❌ Type হবে: ad / link / checkin")
        return
    
    if frequency not in ["daily", "once"]:
        bot.reply_to(message, "❌ Frequency হবে: daily / once")
        return
    
    data = load(TASKS_FILE)
    new_id = max([t["id"] for t in data["tasks"]], default=0) + 1
    
    data["tasks"].append({
        "id": new_id,
        "title": title,
        "desc": desc,
        "reward": reward,
        "type": task_type,
        "link": link,
        "frequency": frequency,
        "status": "active"
    })
    save(TASKS_FILE, data)
    
    bot.reply_to(message,
        f"✅ Task যোগ হয়েছে!\n\n"
        f"ID: {new_id}\n"
        f"Title: {title}\n"
        f"Reward: {reward} pts\n"
        f"Type: {task_type}\n"
        f"Frequency: {frequency}"
    )

# ========== /listtasks ==========
@bot.message_handler(commands=['listtasks'])
def list_tasks(message):
    if not is_admin(message):
        return
    
    data = load(TASKS_FILE)
    tasks = data["tasks"]
    
    if not tasks:
        bot.reply_to(message, "কোনো task নেই")
        return
    
    text = "📋 All Tasks:\n\n"
    for t in tasks:
        status = "🟢" if t["status"] == "active" else "🔴"
        text += f"{status} ID: {t['id']}\n"
        text += f"   {t['title']}\n"
        text += f"   Reward: {t['reward']} pts | Type: {t['type']} | Freq: {t.get('frequency','daily')}\n\n"
    
    bot.reply_to(message, text)

# ========== /deltask ==========
@bot.message_handler(commands=['deltask'])
def del_task(message):
    if not is_admin(message):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /deltask <id>")
        return
    
    try:
        tid = int(parts[1])
    except:
        bot.reply_to(message, "❌ ID সংখ্যা হতে হবে")
        return
    
    data = load(TASKS_FILE)
    original = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != tid]
    
    if len(data["tasks"]) == original:
        bot.reply_to(message, f"❌ Task ID {tid} পাওয়া যায়নি")
        return
    
    save(TASKS_FILE, data)
    bot.reply_to(message, f"✅ Task {tid} delete হয়েছে")

# ========== /users ==========
@bot.message_handler(commands=['users'])
def list_users(message):
    if not is_admin(message):
        return
    
    users = load(USERS_FILE)
    if not users:
        bot.reply_to(message, "কোনো user নেই")
        return
    
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("points", 0), reverse=True)
    
    text = f"👥 Total Users: {len(users)}\n\n"
    for i, (uid, u) in enumerate(sorted_users[:20], 1):
        status = "🚫" if u.get("banned") else "🟢"
        text += f"{i}. {status} {u.get('name', 'User')} — {u.get('points', 0)} pts\n"
        text += f"   ID: {uid}\n\n"
    
    if len(users) > 20:
        text += f"\n... আরো {len(users) - 20} জন"
    
    bot.reply_to(message, text)

# ========== /give ==========
@bot.message_handler(commands=['give'])
def give_points(message):
    if not is_admin(message):
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /give <user_id> <points>")
        return
    
    try:
        uid = parts[1]
        pts = int(parts[2])
    except:
        bot.reply_to(message, "❌ Format ভুল")
        return
    
    users = load(USERS_FILE)
    if uid not in users:
        bot.reply_to(message, "❌ User নেই")
        return
    
    users[uid]["points"] += pts
    users[uid]["total_earned"] += pts
    save(USERS_FILE, users)
    
    bot.reply_to(message, f"✅ {pts} pts দেওয়া হয়েছে {users[uid]['name']} কে")
    try:
        bot.send_message(int(uid), f"🎁 Admin আপনাকে {pts} points দিয়েছে!")
    except:
        pass

# ========== /ban ==========
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not is_admin(message):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /ban <user_id>")
        return
    
    uid = parts[1]
    users = load(USERS_FILE)
    
    if uid not in users:
        bot.reply_to(message, "❌ User নেই")
        return
    
    users[uid]["banned"] = True
    save(USERS_FILE, users)
    bot.reply_to(message, f"✅ {users[uid]['name']} ban হয়েছে")

# ========== /unban ==========
@bot.message_handler(commands=['unban'])
def unban_user(message):
    if not is_admin(message):
        return
    
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /unban <user_id>")
        return
    
    uid = parts[1]
    users = load(USERS_FILE)
    
    if uid not in users:
        bot.reply_to(message, "❌ User নেই")
        return
    
    users[uid]["banned"] = False
    save(USERS_FILE, users)
    bot.reply_to(message, f"✅ {users[uid]['name']} unban হয়েছে")

# ========== /broadcast ==========
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if not is_admin(message):
        return
    
    msg = message.text.replace("/broadcast", "").strip()
    if not msg:
        bot.reply_to(message, "Usage: /broadcast <message>")
        return
    
    users = load(USERS_FILE)
    sent = 0
    failed = 0
    
    bot.reply_to(message, f"📢 Broadcasting to {len(users)} users...")
    
    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 Announcement:\n\n{msg}")
            sent += 1
        except:
            failed += 1
    
    bot.reply_to(message, f"✅ Sent: {sent}\n❌ Failed: {failed}")

# ========== INIT & RUN ==========
init_default_tasks()

print("🤖 Bot started...")
print(f"Admin ID: {ADMIN_ID}")
print(f"WebApp URL: {WEBAPP_URL}")
bot.infinity_polling()
