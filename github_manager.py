import os
import base64
from github import Github, GithubException
from config import GITHUB_TOKEN, GITHUB_USERNAME


def get_github_client():
    """GitHub client qaytaradi"""
    return Github(GITHUB_TOKEN)


import re
import time


def get_or_create_clean_repo(user, base_name: str, description: str):
    """
    Yangi yoki toza repository yaratadi.
    Agar nom band bo'lsa, avvalgisini o'chiradi yoki unikal nom bilan yaratadi (422 xatosi chiqmasligi uchun).
    """
    clean_name = re.sub(r'[^a-zA-Z0-9-]', '', base_name.lower().replace(' ', '-').replace('_', '-')).strip('-') or "app"
    
    # 1. To'g'ridan-to'g'ri yaratish yoki o'chirish
    for attempt in range(3):
        target_name = clean_name if attempt == 0 else f"{clean_name}-v{attempt+1}"
        try:
            ex = user.get_repo(target_name)
            ex.delete()
            time.sleep(1)
        except Exception:
            pass

        try:
            repo = user.create_repo(
                name=target_name,
                description=description,
                auto_init=False,
                private=False
            )
            return repo, target_name
        except Exception as e:
            if "already exists" in str(e).lower():
                time.sleep(1)
                continue
            raise e
            
    # 2. Agar hali ham band bo'lsa, timestamp qo'shib yaratish
    unique_name = f"{clean_name}-{int(time.time()) % 10000}"
    repo = user.create_repo(name=unique_name, description=description, auto_init=False, private=False)
    return repo, unique_name


def create_web_repo_and_deploy(code: str, app_name: str, logo_path: str = None) -> tuple[bool, str]:
    """
    Web kodni GitHub Pages'ga deploy qiladi.
    Qaytaradi: (muvaffaqiyatli, url_yoki_xato)
    """
    try:
        g = get_github_client()
        user = g.get_user()
        
        # Xavfsiz repo yaratish
        repo, repo_name = get_or_create_clean_repo(
            user, 
            app_name, 
            f"🤖 Telegram Builder Bot tomonidan yaratildi"
        )
        
        # index.html kodni yuklash
        files_to_upload = {}
        
        # Agar kod to'liq HTML bo'lmasa, wrap qilish
        if "<!DOCTYPE html>" not in code and "<html" not in code:
            html_code = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; }}
    </style>
</head>
<body>
{code}
</body>
</html>"""
        else:
            html_code = code
        
        files_to_upload["index.html"] = html_code
        
        # Logo qo'shish
        if logo_path and os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
            
            files_to_upload["logo.png"] = None
            files_to_upload["_logo_data"] = logo_data
        
        # README yaratish
        files_to_upload["README.md"] = f"# {app_name}\n\n🤖 Telegram Builder Bot tomonidan yaratildi\n\n🌐 [Saytni ko'rish](https://{GITHUB_USERNAME}.github.io/{repo_name}/)"
        
        # Fayllarni yuklash
        for filename, content in files_to_upload.items():
            if filename == "_logo_data":
                continue
            if filename == "logo.png" and "_logo_data" in files_to_upload:
                repo.create_file(
                    "logo.png",
                    "Logo qo'shildi",
                    base64.b64decode(files_to_upload["_logo_data"])
                )
            else:
                repo.create_file(
                    filename,
                    f"{filename} qo'shildi",
                    content.encode("utf-8")
                )
        
        # GitHub Pages yoqish (REST API orqali)
        import requests
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        branch_name = repo.default_branch or "main"
        try:
            requests.post(
                f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/pages",
                headers=headers,
                json={"source": {"branch": branch_name, "path": "/"}},
                timeout=10
            )
        except Exception as pe:
            print(f"Pages enable note: {pe}")
        
        pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"
        repo_url = repo.html_url
        
        return True, f"🌐 <b>Sayt URL:</b> {pages_url}\n📦 <b>GitHub Repo:</b> {repo_url}"
        
    except GithubException as e:
        return False, f"GitHub xatosi: {e.data.get('message', str(e))}"
    except Exception as e:
        return False, f"Deploy xatosi: {str(e)}"


def create_flutter_repo(apk_path: str, code: str, app_name: str) -> tuple[bool, str]:
    """
    Flutter kodini va APK'ni GitHub'ga yuklaydi.
    Qaytaradi: (muvaffaqiyatli, repo_url)
    """
    try:
        g = get_github_client()
        user = g.get_user()
        
        # Xavfsiz Flutter repo yaratish
        repo, repo_name = get_or_create_clean_repo(
            user,
            f"{app_name}-flutter",
            f"🤖 Flutter app - Telegram Builder Bot"
        )
        
        # Kod Flutter bo'lmasa, uni Flutter ilovasiga o'rash
        if "package:flutter" not in code and "void main()" not in code:
            dart_code = f"""import 'package:flutter/material.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: '{app_name}',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: Scaffold(
        appBar: AppBar(
          title: Text('{app_name}'),
          centerTitle: true,
          backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.check_circle_outline, size: 80, color: Colors.green),
                const SizedBox(height: 20),
                Text(
                  '{app_name}',
                  style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Ilova Telegram Builder Bot orqali yaratildi!',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 16, color: Colors.grey),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }}
}}
"""
        else:
            dart_code = code

        # Kodni yuklash
        repo.create_file(
            "lib/main.dart",
            "Flutter kodi qo'shildi",
            dart_code.encode("utf-8")
        )
        
        repo.create_file(
            "README.md",
            "README qo'shildi",
            f"# {app_name}\n\n🤖 Telegram Builder Bot tomonidan yaratildi\n\n📱 Flutter ilovasi".encode("utf-8")
        )
        
        # pubspec.yaml yaratish
        safe_name = app_name.lower().replace(" ", "_").replace("-", "_")
        pubspec_content = f"""name: {safe_name}
description: Generated by TelegramBuilderBot
publish_to: 'none'
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.6

flutter:
  uses-material-design: true
"""
        repo.create_file("pubspec.yaml", "pubspec.yaml qo'shildi", pubspec_content.encode("utf-8"))

        # GitHub Actions orqali bepul APK build workflow
        workflow_content = f"""name: Build APK

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: 'zulu'
          java-version: '17'

      - name: Set up Flutter
        uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.22.x'
          channel: 'stable'

      - name: Create Android project and Build APK
        run: |
          flutter create . --project-name=app_builder --platforms=android --org com.builder.app --overwrite
          flutter pub get
          flutter build apk --release --target-platform=android-arm,android-arm64 --no-tree-shake-icons

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-release
          path: build/app/outputs/flutter-apk/app-release.apk
"""
        repo.create_file(".github/workflows/build_apk.yml", "Avtomatik APK build workflow", workflow_content.encode("utf-8"))

        # APK faylni yuklash (agar lokal mavjud bo'lsa)
        if apk_path and os.path.exists(apk_path):
            with open(apk_path, "rb") as f:
                apk_data = f.read()
            if len(apk_data) < 25 * 1024 * 1024:
                repo.create_file(
                    "app-release.apk",
                    "APK qo'shildi",
                    apk_data
                )
        
        return True, repo.html_url, repo_name
        
    except Exception as e:
        return False, str(e), None


def check_github_connection() -> tuple[bool, str]:
    """GitHub ulanishini tekshiradi"""
    try:
        g = get_github_client()
        user = g.get_user()
        return True, user.login
    except Exception as e:
        return False, str(e)


async def wait_and_download_github_apk(repo_name: str, output_dir: str, status_callback=None) -> tuple[bool, str]:
    """
    GitHub Actions'da APK yig'ilishini kutadi va tayyor .apk faylni yuklab oladi.
    """
    import io
    import time
    import zipfile
    import requests
    import asyncio

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    # 1. Workflow ishga tushishini kutish
    run_id = None
    for attempt in range(15):  # 1 daqiqa qidirish
        await asyncio.sleep(4)
        url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/actions/runs"
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                runs = resp.json().get("workflow_runs", [])
                if runs:
                    run_id = runs[0]["id"]
                    break
        except Exception:
            pass

    if not run_id:
        return False, "GitHub Actions workflow ishga tushmadi."

    # 2. Workflow tugashini kutish
    start_time = time.time()
    while time.time() - start_time < 360:  # 6 daqiqagacha
        await asyncio.sleep(10)
        run_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/actions/runs/{run_id}"
        try:
            resp = requests.get(run_url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status")
                conclusion = data.get("conclusion")
                
                if status == "completed":
                    if conclusion == "success":
                        break
                    else:
                        return False, f"Bulutda APK build xatosi (status: {conclusion})."
                
                if status_callback:
                    elapsed = int(time.time() - start_time)
                    try:
                        await status_callback(f"⏳ Bulutda APK yig'ilmoqda ({elapsed}s)...")
                    except Exception:
                        pass
        except Exception:
            pass

    # 3. Artifact (APK) ni topish va yuklab olish
    art_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/actions/runs/{run_id}/artifacts"
    try:
        resp = requests.get(art_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return False, "Artifacts ro'yxatini olib bo'lmadi."
        
        artifacts = resp.json().get("artifacts", [])
        if not artifacts:
            return False, "Yaratilgan APK artifact topilmadi."
        
        artifact_id = artifacts[0]["id"]
        download_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/actions/artifacts/{artifact_id}/zip"
        
        zip_resp = requests.get(download_url, headers=headers, timeout=60)
        if zip_resp.status_code != 200:
            return False, f"APK faylini yuklab olib bo'lmadi (HTTP {zip_resp.status_code})."
        
        # 4. Zip ichidan .apk faylni chiqarib olish
        os.makedirs(output_dir, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(zip_resp.content)) as z:
            for filename in z.namelist():
                if filename.endswith(".apk") or "release" in filename.lower():
                    extracted_path = os.path.join(output_dir, f"{repo_name}.apk")
                    with open(extracted_path, "wb") as f_out:
                        f_out.write(z.read(filename))
                    return True, extracted_path
            
            # Agar nomi boshqacha bo'lsa
            first_file = z.namelist()[0]
            extracted_path = os.path.join(output_dir, f"{repo_name}.apk")
            with open(extracted_path, "wb") as f_out:
                f_out.write(z.read(first_file))
            return True, extracted_path

    except Exception as e:
        return False, f"Yuklab olishda xatolik: {e}"

    return False, "APK fayl topilmadi."
