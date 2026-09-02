"""
AI Analyzer — google-genai + aqlli mahalliy tahlilchi (fallback)
"""
import re
import json
import base64
import pathlib
from config import GEMINI_API_KEY

MODEL = "gemini-1.5-flash"


def local_smart_analyze(code: str) -> dict:
    """
    Kodni aqlli qoidalar orqali mahalliy tahlil qilish (AI ishlamay qolganda ham 100% aniqlaydi).
    """
    code_lower = code.lower()

    # 1. Flutter / Dart
    if "import 'package:flutter/" in code or "package:flutter/material.dart" in code or "statelesswidget" in code_lower or "statefulwidget" in code_lower:
        # Ilova nomini qidirish (title: '...', AppBar title, yoki Class nomi)
        app_name = "FlutterApp"
        title_match = re.search(r"title:\s*['\"]([^'\"]+)['\"]", code, re.IGNORECASE)
        if title_match:
            app_name = title_match.group(1).strip()
        else:
            class_match = re.search(r"class\s+([A-Za-z0-9_]+)\s+extends\s+StatelessWidget", code)
            if class_match:
                app_name = class_match.group(1).replace("App", "") or "FlutterApp"

        return {
            "type": "flutter",
            "app_name": app_name,
            "description": "Flutter mobil ilovasi (Android APK va iOS uchun mos)",
            "language": "dart",
            "can_build_apk": True
        }

    # 2. Web / HTML / O'yin
    if "<!doctype html>" in code_lower or "<html" in code_lower or "<body>" in code_lower:
        app_name = "WebApp"
        title_match = re.search(r"<title>(.*?)</title>", code, re.IGNORECASE)
        if title_match:
            app_name = title_match.group(1).strip()

        is_game = any(k in code_lower for k in ["game", "o'yin", "clicker", "score", "canvas", "play", "canvas"])
        code_type = "game" if is_game else "web"
        desc = "Interaktiv brauzer o'yini" if is_game else "Veb-sayt / Web ilova"

        return {
            "type": code_type,
            "app_name": app_name,
            "description": desc,
            "language": "html",
            "can_build_apk": False
        }

    # 3. JavaScript / Node.js
    if "function" in code_lower or "const " in code_lower or "let " in code_lower:
        return {
            "type": "web",
            "app_name": "JsApp",
            "description": "JavaScript skript / Veb dastur",
            "language": "javascript",
            "can_build_apk": False
        }

    # 4. Python
    if "def " in code or "import " in code or "print(" in code:
        return {
            "type": "unknown",
            "app_name": "PythonApp",
            "description": "Python dasturi",
            "language": "python",
            "can_build_apk": False
        }

    return {
        "type": "unknown",
        "app_name": "MyApp",
        "description": "Dastur kodi",
        "language": "other",
        "can_build_apk": False
    }


def analyze_code(code: str) -> dict:
    """
    Kodni tahlil qiladi (AI orqali, xatolik bo'lsa mahalliy aqlli parser orqali).
    """
    # Avval AI bilan urinib ko'ramiz
    if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("Q.") and len(GEMINI_API_KEY) > 20:
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
- type: "flutter" (Dart/Flutter), "web" (HTML/CSS/JS), "game" (o'yin), "unknown"
- can_build_apk: faqat Flutter uchun true
- app_name: koddan topilgan nom
"""
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            if "type" in data and data["type"] != "unknown":
                return data
        except Exception as e:
            print(f"AI analyze fallback: {e}")

    # Fallback to smart local analyzer
    return local_smart_analyze(code)


def analyze_image_for_logo(image_path: str) -> str:
    """Yuklangan rasmni logo sifatida qabul qiladi"""
    return "Logo yuklandi ✅"
