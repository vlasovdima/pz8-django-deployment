import os
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

SKILL_SCRIPTS = Path(r"c:\Users\kirak\Downloads\mp\.agents\skills\gost-student-reports\scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))

from screenshot_helper import ScreenshotSession


def main():
    env = os.environ.copy()
    env["DJANGO_SECRET_KEY"] = "a-very-long-and-random-secret-key-for-pz8-deployment-verification-1234567890"
    env["DJANGO_DEBUG"] = "False"
    env["DJANGO_ALLOWED_HOSTS"] = "127.0.0.1,localhost"
    env["DJANGO_CSRF_TRUSTED_ORIGINS"] = "http://127.0.0.1:8018,http://localhost:8018"

    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:8018", "--noreload"],
        cwd=str(SRC_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    time.sleep(3)

    try:
        with ScreenshotSession(width=1440, height=900) as session:
            # 1. /healthz/
            session.navigate("http://127.0.0.1:8018/healthz/", wait_seconds=1.5)
            session.capture_screenshot(str(SCREENSHOTS_DIR / "1_healthz.png"))

            # 2. Страница входа (проверка статики Tabler при DEBUG=False)
            session.navigate("http://127.0.0.1:8018/accounts/login/", wait_seconds=1.5)
            session.capture_screenshot(str(SCREENSHOTS_DIR / "2_login.png"))

            # 3. Вход и главная страница заявок
            session.eval_js(
                """
                document.getElementById('id_username').value = 'pz8_tester1';
                document.getElementById('id_password').value = 'StrongPass123!';
                document.querySelector('form button[type="submit"]').click();
                """,
                wait_after=2.5,
            )
            session.navigate("http://127.0.0.1:8018/tickets/", wait_seconds=2.0)
            session.capture_screenshot(str(SCREENSHOTS_DIR / "3_tickets_dashboard.png"))

            # 4. Ответ REST API /api/categories/
            session.navigate("http://127.0.0.1:8018/api/categories/", wait_seconds=1.5)
            session.capture_screenshot(str(SCREENSHOTS_DIR / "4_api_categories.png"))

        print("Screenshots captured successfully.")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
