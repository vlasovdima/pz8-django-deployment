import json
import os
import sys
from pathlib import Path

BASE_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(BASE_SRC))

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-for-pz8-deployment-suite-1234567890")
os.environ.setdefault("DJANGO_DEBUG", "False")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")
os.environ.setdefault("DJANGO_CSRF_TRUSTED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.contrib.auth.models import User
from django.test import Client
from tickets.models import Category, Ticket


def run_all_tests():
    client = Client()

    # 1. Проверка /healthz/
    resp = client.get("/healthz/")
    assert resp.status_code == 200, f"Expected 200 on /healthz/, got {resp.status_code}"
    assert resp.json() == {"status": "ok"}, f"Unexpected /healthz/ body: {resp.content}"

    # 2. Проверка ALLOWED_HOSTS при DEBUG=False
    bad_host_resp = client.get("/healthz/", HTTP_HOST="evil.example.com")
    assert bad_host_resp.status_code == 400, f"Expected 400 for untrusted host, got {bad_host_resp.status_code}"

    # 3. Проверка выдачи статики через WhiteNoise при DEBUG=False
    js_resp = client.get("/static/tickets/app.js")
    assert js_resp.status_code == 200, f"Expected 200 for /static/tickets/app.js, got {js_resp.status_code}"
    css_resp = client.get("/static/vendor/tabler/css/tabler.min.css")
    assert css_resp.status_code == 200, f"Expected 200 for tabler.min.css, got {css_resp.status_code}"

    # 4. Проверка защиты API без авторизации
    unauth_resp = client.get("/api/categories/")
    assert unauth_resp.status_code == 403, f"Expected 403 for unauthenticated /api/categories/, got {unauth_resp.status_code}"

    # 5. Авторизация и проверка GET/POST/PATCH и недопустимого перехода статуса
    user1, _ = User.objects.get_or_create(username="pz8_tester1")
    user1.set_password("StrongPass123!")
    user1.save()

    user2, _ = User.objects.get_or_create(username="pz8_tester2")
    user2.set_password("StrongPass123!")
    user2.save()

    cat, _ = Category.objects.get_or_create(name="Сеть и VPN")
    assert client.login(username="pz8_tester1", password="StrongPass123!")

    cat_resp = client.get("/api/categories/")
    assert cat_resp.status_code == 200
    assert any(c["name"] == "Сеть и VPN" for c in cat_resp.json())

    # POST /api/tickets/
    create_resp = client.post(
        "/api/tickets/",
        data=json.dumps({
            "title": "Проверка развёртывания ПЗ8",
            "description": "Тестовая заявка для проверки API",
            "category": cat.id,
        }),
        content_type="application/json",
    )
    assert create_resp.status_code == 201, f"Create failed: {create_resp.content}"
    ticket_id = create_resp.json()["id"]

    # Недопустимый переход статуса: new -> done должен быть отклонён
    bad_patch = client.patch(
        f"/api/tickets/{ticket_id}/",
        data=json.dumps({"status": "done"}),
        content_type="application/json",
    )
    assert bad_patch.status_code == 400, f"Expected 400 for new->done, got {bad_patch.status_code}"

    # Допустимый переход: new -> progress
    ok_patch = client.patch(
        f"/api/tickets/{ticket_id}/",
        data=json.dumps({"status": "progress"}),
        content_type="application/json",
    )
    assert ok_patch.status_code == 200
    assert ok_patch.json()["status"] == "progress"

    # Проверка изоляции прав: user2 не должен видеть/редактировать заявку user1
    client2 = Client()
    assert client2.login(username="pz8_tester2", password="StrongPass123!")
    foreign_resp = client2.patch(
        f"/api/tickets/{ticket_id}/",
        data=json.dumps({"status": "done"}),
        content_type="application/json",
    )
    assert foreign_resp.status_code == 404, f"Expected 404 for foreign ticket, got {foreign_resp.status_code}"

    # 6. Проверка наличия понятного сообщения о недоступности API в app.js
    app_js_text = (BASE_SRC / "tickets" / "static" / "tickets" / "app.js").read_text(encoding="utf-8")
    assert "Сервис API временно недоступен" in app_js_text

    # Очистка тестовых записей
    Ticket.objects.filter(id=ticket_id).delete()
    print("ALL PZ8 TESTS PASSED (7/7 checks)")


if __name__ == "__main__":
    run_all_tests()
