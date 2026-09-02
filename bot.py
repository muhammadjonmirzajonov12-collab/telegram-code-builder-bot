"""
🤖 Telegram Builder Bot — Professional 24/7 Versiya
Foydalanuvchilar kod yuboradi, AI tahlil qiladi, nom va logo so'raydi,
Web bo'lsa 24/7 bepul GitHub Pages'ga deploy qiladi,
Flutter bo'lsa bulutda bepul APK yaratib, .apk faylni to'g'ridan-to'g'ri Telegram chatga yuboradi.
"""
import os
import html
import shutil
import logging
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)

from config import TELEGRAM_BOT_TOKEN, TEMP_DIR
from ai_analyzer import analyze_code
from flutter_builder import prepare_flutter_project, build_apk, is_flutter_available, add_logo_to_flutter
from github_manager import (
    create_web_repo_and_deploy, create_flutter_repo, 
    check_github_connection, wait_and_download_github_apk
)
from logo_handler import process_logo, generate_simple_logo

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

import json

# Foydalanuvchi ma'lumotlar ombori (global zaxira)
SESSION_FILE = os.path.join(TEMP_DIR, "sessions.json")
user_data_store = {}


def load_sessions():
    global user_data_store
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_data_store = {int(k): v for k, v in data.items()}
    except Exception:
        pass


def save_sessions():
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in user_data_store.items()}, f, ensure_ascii=False)
    except Exception:
        pass


def set_user_data(context, user_id: int, data: dict):
    """Ma'lumotni ham context'ga ham global omborga saqlaydi"""
    user_data_store[user_id] = data
    context.user_data[f"session_{user_id}"] = data
    save_sessions()


def get_user_data(context, user_id: int):
    """Avval context'dan, keyin global ombordan, keyin fayldan qidiradi"""
    # 1. context.user_data ichida bor?
    key = f"session_{user_id}"
    if key in context.user_data:
        return context.user_data[key]
    # 2. Global omborda bor?
    if user_id in user_data_store:
        return user_data_store[user_id]
    # 3. Diskdan qayta yuklash
    load_sessions()
    if user_id in user_data_store:
        context.user_data[key] = user_data_store[user_id]
        return user_data_store[user_id]
    return None


load_sessions()


# ============================================================
# START komandasi
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = html.escape(user.first_name or "Foydalanuvchi")
    
    text = f"""👋 Salom, <b>{first_name}</b>!

🤖 <b>Telegram Builder Bot</b>ga xush kelibsiz!

<b>Men nima qila olaman:</b>
• 📱 <b>Flutter kodi</b> → Bulutda bepul APK yaratish va faylni chatga tashlash
• 🌐 <b>Web sayt / O'yin</b> → 24/7 bepul GitHub Pages hostingga chiqarish
• 🎨 <b>Logo yaratish</b> → Rasm yuklash yoki AI bilan avtomatik logo generatsiya
• 📦 <b>GitHub</b> → Kodlarni profilingizga saqlash

━━━━━━━━━━━━━━━━━
<b>🚀 Qanday ishlatish:</b>
1️⃣ Kodingizni matn yoki fayl ko'rinishida yuboring
2️⃣ AI kod turini aniqlaydi va nom so'raydi
3️⃣ Logo tanlaysiz
4️⃣ APK faylingiz yoki 24/7 ishlovchi Saytingiz tayyor! 🎉

<b>Buyruqlar:</b>
/start — Qayta boshlash
/help — Yordam
/status — Tizim va GitHub holati
━━━━━━━━━━━━━━━━━

📩 <b>Kodingizni hoziroq yuboring!</b>"""
    
    keyboard = [
        [KeyboardButton("📤 Kod yuborish")],
        [KeyboardButton("❓ Yordam"), KeyboardButton("🔗 Tizim holati")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


# ============================================================
# HELP komandasi
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """❓ <b>Yordam bo'limi</b>

<b>Qo'llab-quvvatlanadigan dasturlar:</b>
• 📱 <b>Flutter / Dart</b> — To'liq avtomatik APK yig'iladi va <code>.apk</code> fayl chatga yuboriladi.
• 🌐 <b>HTML / CSS / JavaScript</b> — 24/7 bepul GitHub Pages hostingga deploy qilinadi.
• 🎮 <b>Web O'yinlar</b> — Brauzerda ishlovchi o'yinlar darhol online qilinadi.

<b>Kodni qanday yuborish mumkin:</b>
• To'g'ridan-to'g'ri xabar sifatida yozing
• Yoki <code>.dart</code>, <code>.html</code>, <code>.js</code>, <code>.txt</code> fayl tashlang

<b>Logo imkoniyatlari:</b>
• Istalgan rasm yuborishingiz mumkin
• Yoki AI yordamida ilova nomiga mos zamonaviy gradient logo yaratiladi"""
    
    await update.message.reply_text(text, parse_mode="HTML")


# ============================================================
# STATUS komandasi
# ============================================================
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Tizim holati tekshirilmoqda...")
    
    success, info = check_github_connection()
    flutter_ok = is_flutter_available()
    
    if success:
        text = f"""✅ <b>Tizim 100% Faol va Ishlamoqda!</b>

🐙 <b>GitHub:</b> ✅ Ulangan (@{html.escape(info)})
☁️ <b>Bulutli APK Builder:</b> ✅ Tayyor (GitHub Actions)
🤖 <b>AI Tahlilchi:</b> ✅ Tayyor (Gemini Flash + Smart Engine)
🌐 <b>Web Hosting:</b> ✅ 24/7 GitHub Pages faol"""
    else:
        text = f"""⚠️ <b>Tizim holati:</b>

🐙 <b>GitHub:</b> ❌ Ulanmagan ({html.escape(str(info))})
🤖 <b>AI:</b> ✅ Tayyor
Iltimos, GitHub tokeningizni tekshiring."""
    
    await update.message.reply_text(text, parse_mode="HTML")


# ============================================================
# Matnli xabarlarni qabul qilish
# ========    # 1. Agar foydalanuvchi ilova nomini yozayotgan bo'lsa
    if context.user_data.get("waiting_app_name"):
        context.user_data["waiting_app_name"] = False
        target_uid = context.user_data.get("app_name_user_id", user_id)
        user_info = get_user_data(context, target_uid)
        if user_info:
            clean_name = text.replace("/", "").replace("\\", "").strip()[:40] or "MyApp"
            user_info["analysis"]["app_name"] = clean_name
            set_user_data(context, target_uid, user_info)
            await update.message.reply_text(
                f"✅ Ilova nomi o'rnatildi: <b>{html.escape(clean_name)}</b>",
                parse_mode="HTML"
            )
            await ask_for_logo(update.message, target_uid, context=context)
            return

    # 2. Asosiy menyu tugmalari
    if text in ["📤 Kod yuborish", "❓ Yordam", "🔗 Tizim holati", "🔗 GitHub holati"]:
        if text == "❓ Yordam":
            await help_command(update, context)
        elif text in ["🔗 Tizim holati", "🔗 GitHub holati"]:
            await status_command(update, context)
        else:
            await update.message.reply_text("📩 Kodingizni yuboring (matn yoki fayl ko'rinishida)!")
        return
    
    # 3. Juda qisqa matnlar
    if len(text) < 15:
        await update.message.reply_text(
            "⚠️ Kodingiz juda qisqa. To'liq dastur kodini yuboring yoki fayl tashlang."
        )
        return
    
    await process_code(update, context, text, user_id)


# ============================================================
# Fayl ko'rinishida kod qabul qilish
# ============================================================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    
    allowed_ext = [".dart", ".html", ".htm", ".js", ".txt", ".py", ".css"]
    filename = doc.file_name or "code.txt"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in allowed_ext and doc.mime_type not in ["text/plain", "text/html"]:
        await update.message.reply_text(
            f"⚠️ Bu fayl turi qo'llab-quvvatlanmaydi.\n"
            f"Qo'llab-quvvatlanadigan turlar: {', '.join(allowed_ext)}"
        )
        return
    
    msg = await update.message.reply_text(f"📥 Fayl yuklanmoqda: <code>{html.escape(filename)}</code>...", parse_mode="HTML")
    
    file = await context.bot.get_file(doc.file_id)
    file_path = os.path.join(TEMP_DIR, f"{user_id}_{filename}")
    await file.download_to_drive(file_path)
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    try:
        await msg.delete()
    except Exception:
        pass
        
    await process_code(update, context, code, user_id)


# ============================================================
# Kodni AI bilan tahlil qilish va Ilova nomini so'rash
# ============================================================
async def process_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str, user_id: int):
    msg = await update.message.reply_text("🤖 AI kodni tahlil qilmoqda...")
    
    # AI tahlil
    analysis = analyze_code(code)
    
    # Ma'lumotlarni ikki qatlamda xavfsiz saqlash
    session = {
        "code": code,
        "analysis": analysis,
        "logo_path": None,
        "project_dir": os.path.join(TEMP_DIR, f"project_{user_id}")
    }
    set_user_data(context, user_id, session)
    
    code_type = analysis.get("type", "unknown")
    suggested_name = analysis.get("app_name", "MyApp")
    description = analysis.get("description", "")
    
    type_emoji = {
        "flutter": "📱",
        "web": "🌐", 
        "game": "🎮",
        "unknown": "❓"
    }.get(code_type, "❓")
    
    result_text = f"""✅ <b>Kod tahlili tugadi!</b>

{type_emoji} <b>Tur:</b> {html.escape(code_type.upper())}
📝 <b>Tavsif:</b> {html.escape(description)}
📏 <b>Kod hajmi:</b> {len(code)} belgi

━━━━━━━━━━━━━━━━━
❓ <b>Ilova nomini nima qilamiz?</b>
Yangi nom yozib yuboring yoki quyidagi tavsiya qilingan nomni tasdiqlang:"""
    
    context.user_data["waiting_app_name"] = True
    context.user_data["app_name_user_id"] = user_id

    keyboard = [
        [InlineKeyboardButton(f"✅ \"{suggested_name}\" ma'qul", callback_data=f"setname_default_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await msg.edit_text(result_text, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        await update.message.reply_text(result_text, parse_mode="HTML", reply_markup=reply_markup)


# ============================================================
# Logo so'rash
# ============================================================
async def ask_for_logo(message, user_id: int, context=None):
    user_info = get_user_data(context, user_id) if context else user_data_store.get(user_id)
    if not user_info:
        return
    
    app_name = user_info["analysis"].get("app_name", "MyApp")
    safe_name = html.escape(app_name)
    
    text = f"""🖼 <b>\"{safe_name}\" uchun logo qanday bo'lsin?</b>

• O'z rasmingizni yuborishingiz mumkin
• Yoki AI ilovangiz nomiga mos chiroyli logo yaratib beradi"""
    
    keyboard = [
        [InlineKeyboardButton("🖼 Rasm yuboraman", callback_data=f"logo_upload_{user_id}")],
        [InlineKeyboardButton("🎨 Avtomatik logo yaratish", callback_data=f"logo_auto_{user_id}")],
        [InlineKeyboardButton("⏭ Logosiz davom etish", callback_data=f"logo_skip_{user_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


# ============================================================
# Logo callback'lari
# ============================================================
async def logo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = int(data.split("_")[-1])
    
    user_info = get_user_data(context, user_id)
    if not user_info:
        await query.edit_message_text("ℹ️ Yangi kod yuboring yoki /start bosing.")
        return
    
    # 1. Nomni tasdiqlash tugmasi
    if "setname_default" in data:
        context.user_data["waiting_app_name"] = False
        app_name = user_info["analysis"].get("app_name", "MyApp")
        await query.edit_message_text(f"✅ Ilova nomi: <b>{html.escape(app_name)}</b>", parse_mode="HTML")
        await ask_for_logo(query.message, user_id, context=context)
        return

    # 2. Rasm yuklash tanlansa
    if "logo_upload" in data:
        context.user_data["waiting_logo"] = True
        context.user_data["logo_user_id"] = user_id
        await query.edit_message_text(
            "📸 Logo rasmini yuboring (PNG yoki JPG formatda):"
        )
        
    # 3. Avtomatik logo tanlansa
    elif "logo_auto" in data:
        app_name = user_info["analysis"].get("app_name", "MyApp")
        logo_path = os.path.join(TEMP_DIR, f"logo_{user_id}.png")
        
        await query.edit_message_text("🎨 Logo generatsiya qilinmoqda...")
        generate_simple_logo(app_name, logo_path)
        user_info["logo_path"] = logo_path
        set_user_data(context, user_id, user_info)
        
        try:
            with open(logo_path, "rb") as photo_f:
                await query.message.reply_photo(
                    photo=photo_f,
                    caption=f"✅ <b>{html.escape(app_name)}</b> uchun logo tayyorlandi!",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Logo send error: {e}")
            
        await show_build_options(query.message, user_id, context=context)
        
    # 4. Logosiz o'tilsa
    elif "logo_skip" in data:
        user_info["logo_path"] = None
        set_user_data(context, user_id, user_info)
        await query.edit_message_text("⏭ Logosiz davom etilmoqda...")
        await show_build_options(query.message, user_id, context=context)


# ============================================================
# Rasm kelganda uni logoga aylantirish
# ============================================================
async def handle_logo_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_logo"):
        return
    
    user_id = context.user_data.get("logo_user_id")
    user_info = get_user_data(context, user_id) if user_id else None
    if not user_id or not user_info:
        await update.message.reply_text("❌ Avval kodingizni yuboring.")
        return
    
    context.user_data["waiting_logo"] = False
    
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    
    raw_path = os.path.join(TEMP_DIR, f"logo_raw_{user_id}.jpg")
    logo_path = os.path.join(TEMP_DIR, f"logo_{user_id}.png")
    
    await file.download_to_drive(raw_path)
    process_logo(raw_path, logo_path)
    if os.path.exists(raw_path):
        os.remove(raw_path)
    
    user_info["logo_path"] = logo_path
    set_user_data(context, user_id, user_info)
    
    try:
        with open(logo_path, "rb") as photo_f:
            await update.message.reply_photo(
                photo=photo_f,
                caption="✅ Logo qabul qilindi va tayyorlandi!"
            )
    except Exception as e:
        logger.error(f"Photo send error: {e}")
    
    await show_build_options(update.message, user_id, context=context)


# ============================================================
# Amalni tanlash tugmalari (Build / Deploy)
# ============================================================
async def show_build_options(message, user_id: int, context=None):
    user_info = get_user_data(context, user_id) if context else user_data_store.get(user_id)
    if not user_info:
        return
    
    analysis = user_info["analysis"]
    code_type = analysis.get("type", "unknown")
    app_name = analysis.get("app_name", "MyApp")
    safe_name = html.escape(app_name)
    
    buttons = [
        [InlineKeyboardButton("📱 APK yaratish va Telegram'ga yuborish", callback_data=f"build_apk_{user_id}")]
    ]
    
    if code_type in ["web", "game"]:
        buttons.append([InlineKeyboardButton(
            "🌐 24/7 Web Sayt qilib chiqarish (GitHub Pages)", callback_data=f"deploy_web_{user_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        "📦 Kodni GitHub'ga yuklash", callback_data=f"deploy_flutter_{user_id}"
    )])
    buttons.append([InlineKeyboardButton(
        "❌ Bekor qilish", callback_data=f"cancel_{user_id}"
    )])
    
    code_type_text = {
        "flutter": "📱 Flutter", 
        "web": "🌐 Web Sayt", 
        "game": "🎮 Web O'yin"
    }.get(code_type, "❓ Dastur")
    
    await message.reply_text(
        f"🚀 <b>{safe_name}</b> — {code_type_text}\n\nQaysi amalni bajarishni tanlang:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ============================================================
# Build va Deploy jarayonlari
# ============================================================
async def build_deploy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "no_action":
        return
    
    parts = data.rsplit("_", 1)
    if len(parts) != 2:
        return
    
    action = parts[0]
    user_id = int(parts[1])
    
    user_info = get_user_data(context, user_id)
    if not user_info:
        await query.edit_message_text("ℹ️ Yangi kod yuboring yoki /start bosing.")
        return
    
    code = user_info["code"]
    analysis = user_info["analysis"]
    logo_path = user_info.get("logo_path")
    app_name = analysis.get("app_name", "MyApp")
    safe_name = html.escape(app_name)
    flutter_ok = is_flutter_available()
    
    # 1. Bekor qilish
    if action == "cancel":
        if user_id in user_data_store:
            del user_data_store[user_id]
        await query.edit_message_text("❌ Bekor qilindi.")
        return
    
    # 2. APK yaratish va faylni Telegram chatga yuborish
    elif action == "build_apk":
        if flutter_ok:
            await query.edit_message_text(
                f"⏳ <b>{safe_name}</b> uchun APK yaratilmoqda...\n(3-5 daqiqa vaqt olishi mumkin)",
                parse_mode="HTML"
            )
            project_dir = user_info["project_dir"]
            os.makedirs(project_dir, exist_ok=True)
            prepare_flutter_project(code, app_name, project_dir)
            if logo_path:
                add_logo_to_flutter(logo_path, project_dir)
            
            success, result = build_apk(project_dir, app_name)
            if success and os.path.exists(result):
                await query.edit_message_text("✅ APK tayyor! Yuborilmoqda...")
                with open(result, "rb") as apk_file:
                    await query.message.reply_document(
                        document=apk_file,
                        filename=f"{app_name.replace(' ', '_')}.apk",
                        caption=f"📱 <b>{safe_name}</b> — APK tayyor!\n\n📦 Faylni yuklab olib telefoningizga o'rnating.",
                        parse_mode="HTML"
                    )
                shutil.rmtree(project_dir, ignore_errors=True)
            else:
                await query.edit_message_text(f"❌ APK yaratib bo'lmadi:\n{html.escape(str(result))}")
        else:
            # Bulutda bepul GitHub Actions orqali build va to'g'ridan-to'g'ri .apk yuklab yuborish
            await query.edit_message_text(
                f"⏳ <b>{safe_name}</b> uchun APK bulutda yaratilmoqda...\n\n"
                "⚙️ <i>GitHub Actions bulutida APK yig'ilmoqda (2-3 daqiqa).\n"
                "Tayyor bo'lishi bilan .apk faylni shu yerga yuboraman!</i>",
                parse_mode="HTML"
            )
            
            # GitHub repo yaratish
            success, repo_url, repo_name = create_flutter_repo(None, code, app_name)
            if not success:
                await query.edit_message_text(f"❌ GitHub'ga yuklashda xatolik:\n{html.escape(str(repo_url))}")
                return
            
            # Status xabari
            async def update_status(text):
                try:
                    await query.edit_message_text(
                        f"⏳ <b>{safe_name}</b> uchun APK yig'ilmoqda...\n\n{text}",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

            # APK kutish va yuklab olish
            apk_dir = os.path.join(TEMP_DIR, f"apk_{user_id}")
            ok, apk_path = await wait_and_download_github_apk(repo_name, apk_dir, status_callback=update_status)
            
            if ok and os.path.exists(apk_path):
                await query.edit_message_text(f"✅ <b>{safe_name}</b> APK tayyor! Fayl yuborilmoqda...", parse_mode="HTML")
                with open(apk_path, "rb") as apk_file:
                    caption_text = (
                        f"📱 <b>{safe_name}</b> — APK fayli tayyor!\n\n"
                        f"⚡ <b>24/7 Rejim:</b> O'rnatilgan ilova telefoningizda 24/7 uzluksiz ishlaydi!\n"
                        f"📦 <b>24/7 Bulutli Zaxira:</b> {repo_url}\n\n"
                        f"📥 <i>Faylni yuklab olib telefoningizga o'rnating.</i>"
                    )
                    await query.message.reply_document(
                        document=apk_file,
                        filename=f"{app_name.replace(' ', '_')}.apk",
                        caption=caption_text,
                        parse_mode="HTML"
                    )
                shutil.rmtree(apk_dir, ignore_errors=True)
            else:
                await query.edit_message_text(
                    f"⚠️ APK yaratishda xatolik yuz berdi: {html.escape(str(apk_path))}\n\n"
                    f"📦 Kodingiz GitHub'da saqlandi: {repo_url}"
                )
    
    # 3. Web Saytni 24/7 GitHub Pages'ga deploy qilish
    elif action == "deploy_web":
        await query.edit_message_text(
            f"⏳ <b>{safe_name}</b> 24/7 GitHub Pages hostingga yuklanmoqda...",
            parse_mode="HTML"
        )
        
        success, result = create_web_repo_and_deploy(code, app_name, logo_path)
        
        if success:
            msg = (
                f"🎉 <b>{safe_name}</b> muvaffaqiyatli 24/7 ishga tushirildi!\n\n"
                f"{result}\n\n"
                f"🌐 <i>Saytingiz butun dunyo bo'ylab 24/7 doimiy ishlaydi (bepul HTTPS/SSL bilan).</i>\n"
                f"⚠️ <i>Dastlabki 1 daqiqada GitHub saytni faollashtiradi.</i>"
            )
            try:
                await query.edit_message_text(msg, parse_mode="HTML", disable_web_page_preview=False)
            except Exception:
                await query.edit_message_text(msg.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""))
        else:
            await query.edit_message_text(f"❌ Deploy qilib bo'lmadi:\n{html.escape(str(result))}")
    
    # 4. Faqat Flutter kodini GitHub'ga saqlash
    elif action == "deploy_flutter":
        await query.edit_message_text(
            f"⏳ <b>{safe_name}</b> GitHub'ga yuklanmoqda...",
            parse_mode="HTML"
        )
        
        success, result, repo_name = create_flutter_repo(None, code, app_name)
        
        if success:
            actions_url = f"{result}/actions"
            msg = (
                f"🎉 <b>{safe_name}</b> GitHub'ga yuklandi!\n\n"
                f"📦 <b>Repo:</b> {result}\n"
                f"⚙️ <b>Bulutda APK yaratish:</b> {actions_url}\n\n"
                f"💡 <i>GitHub Actions bulutda bepul APK faylini yaratmoqda (taxminan 2-3 daqiqa).\n"
                f"Jarayon tugagach Actions sahifasidan .apk faylni yuklab olishingiz mumkin!</i>"
            )
            try:
                await query.edit_message_text(msg, parse_mode="HTML", disable_web_page_preview=True)
            except Exception:
                await query.edit_message_text(f"🎉 {app_name} GitHub'ga yuklandi!\n\nRepo: {result}\nActions (APK): {actions_url}")
        else:
            await query.edit_message_text(f"❌ GitHub'ga yuklashda xatolik:\n{html.escape(str(result))}")
    
    # Sessiyani tozalash
    if user_id in user_data_store:
        logo = user_data_store[user_id].get("logo_path")
        if logo and os.path.exists(logo):
            try:
                os.remove(logo)
            except Exception:
                pass
        del user_data_store[user_id]


# ============================================================
# Deploy komandasi
# ============================================================
async def deploy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_data_store:
        await update.message.reply_text(
            "⚠️ Hech qanday loyiha tayyorlanmagan.\n"
            "Avval kodingizni yuboring."
        )
        return
    await show_build_options(update.message, user_id)


# ============================================================
# Global Xatolik ushlagich
# ============================================================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Xatolik: {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Kichik xatolik yuz berdi. Iltimos, /start bosing va qayta urinib ko'ring."
            )
        except Exception:
            pass


# ============================================================
# ASOSIY BOT ISHGA TUSHIRISH
# ============================================================
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Buyruqlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("deploy", deploy_command))
    
    # Xabarlar
    app.add_handler(MessageHandler(filters.PHOTO, handle_logo_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_text))
    
    # Callback tugmalar
    app.add_handler(CallbackQueryHandler(logo_callback, pattern="^(logo_|setname_)"))
    app.add_handler(CallbackQueryHandler(build_deploy_callback, pattern="^(build_|deploy_|cancel_|no_action)"))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    print("Telegram Builder Bot 24/7 ishga tushdi!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
