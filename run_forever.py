"""
24/7 Bot Supervisor — Bot to'xtab qolsa avtomatik qayta ishga tushiradi
"""
import time
import subprocess
import sys

print("🚀 Bot 24/7 rejimida nazorat ostida ishga tushmoqda...")

while True:
    try:
        print("\n[24/7 Supervisor] Bot ishga tushirildi...")
        process = subprocess.Popen([sys.executable, "bot.py"])
        process.wait()
        
        print(f"\n[24/7 Supervisor] Bot to'xtadi (exit code {process.returncode}). 3 soniyada qayta ishga tushiriladi...")
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n[24/7 Supervisor] Qo'lda to'xtatildi.")
        if 'process' in locals():
            process.terminate()
        break
    except Exception as e:
        print(f"\n[24/7 Supervisor] Xatolik: {e}. 5 soniyada qayta uriniladi...")
        time.sleep(5)
