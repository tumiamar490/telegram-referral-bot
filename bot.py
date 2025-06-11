import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- কনফিগারেশন ---
# এই লিংকগুলো আপনার নিজের লিংক দিয়ে পরিবর্তন করতে পারেন, যদি চান।
PREMIUM_GROUP_LINK = "https://t.me/+kfLVIaUbgoY0YTBl"
INSTRUCTIONS_CHANNEL_LINK = "https://t.me/+FKMJZInx45FlYWZl"
REQUIRED_REFERRALS = 3
DATA_FILE = "user_data.json"

# --- ডেটা লোড এবং সেভ করার ফাংশন ---
def load_user_data():
    """ইউজার ডেটা JSON ফাইল থেকে লোড করে।"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {} # যদি ফাইল খালি বা ভুল ফরম্যাটে থাকে
    return {}

def save_user_data(data):
    """ইউজার ডেটা JSON ফাইলে সেভ করে।"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- কমান্ড হ্যান্ডলার ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /start কমান্ড হ্যান্ডেল করে।"""
    user = update.effective_user
    user_id_str = str(user.id)
    user_data = load_user_data()

    # যদি ইউজার আগে থেকেই রেজিস্টার্ড না থাকে
    if user_id_str not in user_data:
        user_data[user_id_str] = {
            "name": user.full_name,
            "referrals": 0,
            "referred_by": None
        }
        
        # যদি রেফারেলের মাধ্যমে জয়েন করে
        if context.args:
            referrer_id = context.args[0]
            if referrer_id != user_id_str and referrer_id in user_data:
                user_data[user_id_str]["referred_by"] = referrer_id
                
                # রেফারারের কাউন্ট বাড়ানো
                if "referrals" in user_data[referrer_id]:
                    user_data[referrer_id]["referrals"] += 1
                else:
                    user_data[referrer_id]["referrals"] = 1

                save_user_data(user_data) # ডেটা সেভ করা
                
                # রেফারারকে তার সফল রেফারেল সম্পর্কে জানানো
                try:
                    current_referrals = user_data[referrer_id]['referrals']
                    await context.bot.send_message(
                        chat_id=referrer_id,
                        text=f"🎉 দারুণ! {user.full_name} আপনার লিংকের মাধ্যমে জয়েন করেছে।\n\nআপনার মোট রেফারেল সংখ্যা: {current_referrals}"
                    )
                    
                    # রেফারার যদি টার্গেট পূরণ করে
                    if current_referrals >= REQUIRED_REFERRALS:
                        await context.bot.send_message(
                            chat_id=referrer_id,
                            text=f"🎉 অভিনন্দন! আপনি সফলভাবে {REQUIRED_REFERRALS} জনকে রেফার করেছেন।\n\n🎁 இதோ আপনার প্রিমিয়াম গ্রুপের জয়েনিং লিংক:\n{PREMIUM_GROUP_LINK}"
                        )
                except Exception as e:
                    print(f"Referrer notification error: {e}")

    save_user_data(user_data) # নতুন ইউজারের ডেটা সেভ করা

    # নতুন ইউজারকে স্বাগত বার্তা পাঠানো
    welcome_text = f"👋 স্বাগতম, {user.full_name}!\n\nআমাদের প্রিমিয়াম গ্রুপে জয়েন করার জন্য আপনাকে মাত্র {REQUIRED_REFERRALS} জন বন্ধুকে রেফার করতে হবে।"
    keyboard = [
        [InlineKeyboardButton("🔗 আমার রেফারেল লিংক", callback_data="get_link")],
        [InlineKeyboardButton("🤔 কিভাবে রেফার করব?", callback_data="how_to_refer")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# --- বাটন হ্যান্ডলার ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ইনলাইন বাটনগুলোর কাজ পরিচালনা করে।"""
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    bot_username = (await context.bot.get_me()).username
    user_data = load_user_data()
    
    if query.data == "get_link":
        referral_count = user_data.get(user_id, {}).get("referrals", 0)
        
        referral_link = f"https://t.me/{bot_username}?start={user_id}"
        message_text = (
            f"🔗 আপনার ইউনিক রেফারেল লিংক:\n`{referral_link}`\n\n"
            f"(এই লিংকটি কপি করে আপনার বন্ধুদের সাথে শেয়ার করুন।)\n\n"
            f"✅ আপনার মোট রেফারেল সংখ্যা: {referral_count} জন।"
        )
        # প্রিমিয়াম লিংক পাওয়ার শর্ত চেক করা
        if referral_count >= REQUIRED_REFERRALS:
             message_text += f"\n\n🎉 অভিনন্দন! আপনি সফলভাবে আপনার টার্গেট পূরণ করেছেন। இதோ প্রিমিয়াম গ্রুপের লিংক:\n{PREMIUM_GROUP_LINK}"

        await query.edit_message_text(text=message_text, parse_mode='Markdown')

    elif query.data == "how_to_refer":
        message_text = (
            f"🤔 **কিভাবে রেফার করবেন?**\n\n"
            f"১. প্রথমে 'আমার রেফারেল লিংক' বাটন থেকে আপনার লিংকটি নিন।\n"
            f"২. সেই লিংকটি আপনার বন্ধুদের পাঠান।\n"
            f"৩. আপনার বন্ধু যখন ওই লিংকে ক্লিক করে বটে /start কমান্ড দেবে, আপনার একটি রেফারেল গণনা করা হবে।\n\n"
            f"ℹ️ বিস্তারিত নিয়মাবলী জানতে আমাদের চ্যানেলে চোখ রাখুন:\n{INSTRUCTIONS_CHANNEL_LINK}"
        )
        keyboard = [[InlineKeyboardButton("🔙 ফিরে যান", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')

    elif query.data == "back_to_main":
        user = query.from_user
        welcome_text = f"👋 স্বাগতম, {user.full_name}!\n\nআমাদের প্রিমিয়াম গ্রুপে জয়েন করার জন্য আপনাকে মাত্র {REQUIRED_REFERRALS} জন বন্ধুকে রেফার করতে হবে।"
        keyboard = [
            [InlineKeyboardButton("🔗 আমার রেফারেল লিংক", callback_data="get_link")],
            [InlineKeyboardButton("🤔 কিভাবে রেফার করব?", callback_data="how_to_refer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=welcome_text, reply_markup=reply_markup)


# --- Main Function ---
def main():
    """বটটি শুরু এবং পরিচালনা করে।"""
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("ত্রুটি: BOT_TOKEN এনভায়রনমেন্ট ভেরিয়েবলে সেট করা নেই।")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("বট চলছে...")
    application.run_polling()

if __name__ == "__main__":
    main()
