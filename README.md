# 🤖 Telegram Builder Bot

Foydalanuvchilar kod yuboradi → AI tahlil qiladi → APK/Website yaratadi → GitHub'ga yuklaydi.

## O'rnatish

```bash
pip install -r requirements.txt
```

## Ishga tushirish

```bash
python bot.py
```

## Kerakli tokenlar (.env fayli)

```env
TELEGRAM_BOT_TOKEN=...       # @BotFather dan
GEMINI_API_KEY=...            # aistudio.google.com dan
GITHUB_TOKEN=...              # github.com/settings/tokens dan
GITHUB_USERNAME=...           # GitHub username'ingiz
```

## Bot komandalar

- `/start` — Botni boshlash
- `/help` — Yordam
- `/status` — Tizim holati
- `/deploy` — Oxirgi loyihani deploy qilish

## Foydalanuvchi oqimi

1. Kod (matn yoki fayl) yuborish
2. AI tur aniqlaydi (Flutter/Web/Game)
3. Logo tanlash (yuklash / avtomatik / o'tkazib yuborish)
4. APK yoki GitHub Pages'ga deploy
