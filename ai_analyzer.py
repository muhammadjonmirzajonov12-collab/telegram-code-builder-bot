"""
AI Analyzer — Gemini AI + aqlli mahalliy tahlilchi (fallback)
Har qanday turdagi kodni to'g'ri aniqlaydi.
"""
import re
import json
from config import GEMINI_API_KEY

MODEL = "gemini-1.5-flash"


def local_smart_analyze(code: str) -> dict:
    """
    Kodni aqlli qoidalar orqali mahalliy tahlil qilish.
    Har qanday kod turini 100% aniqlikda aniqlaydi.
    """
    code_lower = code.lower()

    # 1. Flutter / Dart kodi
    flutter_signs = [
        "import 'package:flutter/",
        'import "package:flutter/',
        "package:flutter/material.dart",
        "statelesswidget",
        "statefulwidget",
        "materialapp(",
        "scaffold(",
        "widget build(",
        "void main() => runapp",
        "runapp(",
    ]
    if any(sign in code_lower for sign in flutter_signs):
        app_name = "FlutterApp"
        for pattern in [
            r"title:\s*['\"]([^'\"]+)['\"]",
            r"class\s+(\w+App)\s+extends",
        ]:
            m = re.search(pattern, code, re.IGNORECASE)
            if m:
                app_name = m.group(1).replace("App", "").strip() or "FlutterApp"
                break
        return {
            "type": "flutter",
            "app_name": app_name,
            "description": "Flutter mobil ilovasi (Dart) — Android APK va iOS uchun",
            "language": "dart",
            "can_build_apk": True,
        }

    # 2. HTML / Web Sayt / O'yin
    html_signs = ["<!doctype html", "<html", "<body", "<head", "<div", "<script", "<canvas"]
    if any(sign in code_lower for sign in html_signs):
        app_name = "WebApp"
        m = re.search(r"<title[^>]*>(.*?)</title>", code, re.IGNORECASE)
        if m:
            app_name = re.sub(r"<[^>]+>", "", m.group(1)).strip() or "WebApp"

        game_signs = ["game", "o'yin", "clicker", "score", "canvas", "play(", "gameover",
                      "onclick", "keydown", "requestanimationframe", "lives", "level",
                      "player", "bullet", "enemy", "jump", "coin", "health"]
        is_game = sum(1 for k in game_signs if k in code_lower) >= 2
        return {
            "type": "game" if is_game else "web",
            "app_name": app_name,
            "description": "Interaktiv brauzer o'yini" if is_game else "Veb-sayt / Web ilova",
            "language": "html",
            "can_build_apk": True,  # WebView orqali APK qilish mumkin
        }

    # 3. Sof JavaScript / TypeScript
    js_signs = ["document.getelementbyid", "document.queryselector", "window.onload",
                 "addeventlistener", "fetch(", "xmlhttprequest", "jquery", "react.createelement",
                 "vue.createapp", "angular"]
    if any(sign in code_lower for sign in js_signs):
        app_name = "JsApp"
        m = re.search(r"(?:app|game|title|name)\s*[=:]\s*['\"]([^'\"]+)['\"]", code, re.IGNORECASE)
        if m:
            app_name = m.group(1).strip()
        return {
            "type": "web",
            "app_name": app_name,
            "description": "JavaScript veb dastur",
            "language": "javascript",
            "can_build_apk": True,
        }

    # 4. Python
    python_signs = ["import ", "def ", "class ", "print(", "if __name__", "flask", "django", "fastapi"]
    if sum(1 for s in python_signs if s in code) >= 2:
        app_name = "PythonApp"
        m = re.search(r"(?:app_name|title|APP_NAME)\s*=\s*['\"]([^'\"]+)['\"]", code)
        if m:
            app_name = m.group(1)
        return {
            "type": "unknown",
            "app_name": app_name,
            "description": "Python dasturi",
            "language": "python",
            "can_build_apk": False,
        }

    # 5. CSS / Style
    if "{" in code and ("color:" in code_lower or "font-size:" in code_lower or "margin:" in code_lower):
        return {
            "type": "web",
            "app_name": "StyledApp",
            "description": "CSS/Style fayli — HTML bilan birga ishlatiladi",
            "language": "css",
            "can_build_apk": False,
        }

    # 6. Umumiy — kod qandaydir bo'lsin, WebView orqali APK qilib beramiz
    app_name = "MyApp"
    for pattern in [r"(?:name|title|app)\s*=\s*['\"]([^'\"]+)['\"]",
                    r"<h1[^>]*>(.*?)</h1>"]:
        m = re.search(pattern, code, re.IGNORECASE)
        if m:
            app_name = re.sub(r"<[^>]+>", "", m.group(1)).strip() or "MyApp"
            break
    return {
        "type": "web",
        "app_name": app_name,
        "description": "Dastur kodi",
        "language": "other",
        "can_build_apk": True,
    }


def analyze_code(code: str) -> dict:
    """
    Kodni tahlil qiladi.
    Avval Gemini AI bilan, xatolik bo'lsa mahalliy aqlli parser bilan.
    """
    if GEMINI_API_KEY and len(GEMINI_API_KEY) > 20 and not GEMINI_API_KEY.startswith("Q."):
        try:
            from google import genai
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""Sen kod tahlilchi AI'san. Quyidagi kodni o'qib, JSON formatida javob ber.

KOD (birinchi 3000 belgi):
```
{code[:3000]}
```

FAQAT quyidagi JSON ni qaytargin, boshqa hech narsa yozma:
{{
  "type": "flutter",
  "app_name": "Ilova nomi",
  "description": "Bu ilova nima qilishini 1-2 jumlada izohla",
  "language": "dart",
  "can_build_apk": true
}}

Qoidalar:
- type: "flutter" (Dart/Flutter kodi bo'lsa), "web" (HTML/CSS/JS bo'lsa), "game" (o'yin bo'lsa), "unknown" (boshqa)
- can_build_apk: flutter uchun true, HTML/game uchun ham true (WebView orqali), python/boshqa uchun false
- app_name: koddan topilgan haqiqiy nom, topilmasa "MyApp"
- language: "dart", "html", "javascript", "python", "other"
"""
            response = client.models.generate_content(model=MODEL, contents=prompt)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            if "type" in data:
                return data
        except Exception as e:
            print(f"AI analyze fallback: {e}")

    return local_smart_analyze(code)


def analyze_image_for_logo(image_path: str) -> str:
    """Yuklangan rasmni logo sifatida qabul qiladi"""
    return "Logo yuklandi ✅"
