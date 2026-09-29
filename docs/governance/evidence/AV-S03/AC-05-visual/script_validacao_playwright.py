import json, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5183"
RESULTS = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto(f"{BASE}/academico", wait_until="networkidle")
    time.sleep(0.5)
    url_after_direct_nav = page.url
    RESULTS["step1_direct_nav_to_academico_unauth"] = {
        "url": url_after_direct_nav,
        "redirected_to_login": "/login" in url_after_direct_nav,
    }
    page.screenshot(path="/tmp/ac05_step1_redirect_to_login.png", full_page=True)

    hist_state = page.evaluate("() => window.history.state")
    RESULTS["step2_history_state_after_redirect"] = hist_state

    page.fill('input[type="email"]', "professor.demo@avalia-platform.example")
    page.fill('input[type="password"]', "DemoAvalIA123!")
    page.screenshot(path="/tmp/ac05_step3_login_form_filled.png", full_page=True)

    # Aguarda explicitamente a URL mudar para /academico apos o clique (timeout 10s)
    page.click('button:has-text("Entrar")')
    try:
        page.wait_for_url("**/academico", timeout=10000)
        RESULTS["step4_wait_for_url_academico"] = "OK - navegou para /academico"
    except Exception as e:
        RESULTS["step4_wait_for_url_academico"] = f"TIMEOUT/ERRO: {e}"

    time.sleep(0.5)
    url_after_login = page.url
    RESULTS["step4_url_after_login"] = url_after_login
    RESULTS["step4_returned_to_academico"] = url_after_login.rstrip("/").endswith("/academico")
    page.screenshot(path="/tmp/ac05_step4_after_login.png", full_page=True)

    browser.close()

with open("/tmp/ac05_results.json", "w") as f:
    json.dump(RESULTS, f, indent=2, ensure_ascii=False)

print(json.dumps(RESULTS, indent=2, ensure_ascii=False))
