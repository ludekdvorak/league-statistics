"""
Hamrsport Badminton Rezervační Bot
===================================
Použití:
    pip install playwright
    playwright install chromium
    python hamrsport_bot.py

Nakonfiguruj sekci CONFIG níže před spuštěním.
"""

import asyncio
import time
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


# ==============================================================================
#  CONFIG – uprav tady
# ==============================================================================
USERNAME = os.getenv("HAMR_USERNAME", "tvuj@email.cz")
PASSWORD = os.getenv("HAMR_PASSWORD", "tvojeHeslo123")
# Sloty k rezervaci – přidej nebo odeber dle potřeby
# Každý slot: datum (YYYY-MM-DD), čas, lokalita, sport
SLOTS = [
    {"date": "2026-03-31", "time": "15:30", "lokalita": "Braník",   "sport": "Badminton"},
    {"date": "2026-03-31", "time": "16:00", "lokalita": "Braník",   "sport": "Badminton"},
]
# Polling – jak dlouho čekat na volný slot
POLL_TOTAL_MINUTES = 20    # celková doba čekání
POLL_FAST_MINUTES  = 10    # prvních X minut = rychlý refresh
POLL_FAST_SECONDS  = 3     # interval rychlého refreshe
POLL_SLOW_SECONDS  = 60    # interval pomalého refreshe
# ==============================================================================

LOGIN_URL = "https://hodiny.hamrsport.cz/Login.aspx"
BASE_URL  = "https://hodiny.hamrsport.cz"


async def login(page):
    print("🔐 Přihlašuji se...")
    await page.goto(LOGIN_URL, wait_until="networkidle")
    await page.locator("input[type='text'], input[type='email']").first.fill(USERNAME)
    await page.locator("input[type='password']").first.fill(PASSWORD)
    await page.locator("input[type='submit'], button[type='submit']").first.click()
    await page.wait_for_load_state("networkidle")
    if "Login" in page.url or "login" in page.url:
        raise Exception("❌ Přihlášení selhalo – zkontroluj USERNAME a PASSWORD")
    print("✅ Přihlášení úspěšné!")
    # Přejdi na hlavní stránku s gridem
    await page.goto("https://hodiny.hamrsport.cz/Default.aspx", wait_until="networkidle")


async def setup_dropdowns(page, lokalita, sport):
    """Nastav Lokalitu a Sport v dropdownech."""
    await page.wait_for_selector("select", timeout=5000)

    # Lokalita
    for sel in await page.locator("select").all():
        opts = await sel.locator("option").all_text_contents()
        if lokalita in opts:
            await sel.select_option(label=lokalita)
            await page.wait_for_timeout(1000)
            break

    # Počkej na Sport dropdown
    try:
        await page.wait_for_function(
            f"""() => Array.from(document.querySelectorAll('select'))
                .some(s => Array.from(s.options).map(o=>o.text).includes('{sport}'))""",
            timeout=5000
        )
    except PlaywrightTimeout:
        pass

    for sel in await page.locator("select").all():
        opts = await sel.locator("option").all_text_contents()
        if sport in opts:
            await sel.select_option(label=sport)
            await page.wait_for_load_state("networkidle")
            break


async def try_book_slot(page, slot: dict) -> bool:
    """
    Zkusí zarezervovat jeden slot.
    Vrátí True pokud rezervace proběhla, False pokud slot není volný.
    """
    target_date = slot["date"]
    target_time = slot["time"]
    dt          = datetime.strptime(target_date, "%Y-%m-%d")
    date_str_cs = dt.strftime("%d.%m.%Y")

    # Počkej na načtení gridu
    try:
        await page.wait_for_selector("tr td", timeout=5000)
    except PlaywrightTimeout:
        print("  ⚠️  Grid se nenačetl")
        return False
    await page.wait_for_timeout(500)

    # Najdi záhlaví s časy
    all_rows     = await page.locator("tr").all()
    header_idx   = -1
    time_col_idx = -1

    for i, row in enumerate(all_rows):
        texts = [(await c.inner_text()).strip() for c in await row.locator("td, th").all()]
        if len([t for t in texts if len(t) == 5 and t[2] == ':']) >= 3:
            header_idx = i
            for j, t in enumerate(texts):
                if t == target_time:
                    time_col_idx = j
                    break
            break

    if header_idx == -1:
        print(f"  ⚠️  Záhlaví s časy nenalezeno")
        return False

    if time_col_idx == -1:
        # Čas možná není vidět – zkus scrollovat doprava a znovu načíst řádky
        print(f"  ⚠️  Čas {target_time} není vidět – zkouším scrollovat...")
        await page.evaluate("document.querySelector('table') && document.querySelector('table').scrollIntoView()")
        await page.keyboard.press("End")
        await page.wait_for_timeout(500)
        all_rows = await page.locator("tr").all()
        for i, row in enumerate(all_rows):
            texts = [(await c.inner_text()).strip() for c in await row.locator("td, th").all()]
            if len([t for t in texts if len(t) == 5 and t[2] == ':']) >= 3:
                header_idx = i
                for j, t in enumerate(texts):
                    if t == target_time:
                        time_col_idx = j
                        break
                break
        if time_col_idx == -1:
            print(f"  ⚠️  Čas {target_time} nenalezen ani po scrollu – zkontroluj formát (např. '21:00')")
            return False

    # Najdi řádek s datumem
    data_row_idx = -1
    for i, row in enumerate(all_rows):
        if i <= header_idx:
            continue
        if date_str_cs in (await row.inner_text()).strip():
            data_row_idx = i
            break

    if data_row_idx == -1:
        print(f"  ⚠️  Datum {date_str_cs} nenalezeno v gridu")
        return False

    # Zkontroluj buňku
    target_row  = all_rows[data_row_idx]
    target_cell = target_row.locator("td, th").nth(time_col_idx)
    cell_text   = (await target_cell.inner_text()).strip()
    cell_class  = await target_cell.get_attribute("class") or ""

    print(f"  📋 [{date_str_cs} {target_time}] text='{cell_text}' class='{cell_class}'")

    if not cell_text:
        print("  ⛔ Slot je obsazený (prázdná buňka)")
        return False

    # Klikni
    box = await target_cell.bounding_box()
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        await page.mouse.move(cx, cy)
        await page.wait_for_timeout(300)
        await page.mouse.click(cx, cy)
        await page.wait_for_timeout(500)
        if await page.locator("text=Rezervační údaje").count() == 0:
            await page.evaluate("el => el.click()", await target_cell.element_handle())
            await page.wait_for_timeout(500)

    # Čekej na dialog
    try:
        await page.wait_for_selector("text=Rezervační údaje", timeout=4000)
    except PlaywrightTimeout:
        print("  ⚠️  Dialog se neotevřel")
        return False

    print("  ✅ Rezervační dialog otevřen – potvrzuji...")

    for label in ["Dokončit", "Rezervovat", "Potvrdit", "Confirm", "OK"]:
        btn = page.get_by_role("button", name=label)
        if await btn.count() > 0:
            await btn.first.click()
            await page.wait_for_load_state("networkidle")
            print(f"  ✅ Kliknuto na '{label}'")
            return True

    submit = page.locator("input[type='submit']")
    if await submit.count() > 0:
        await submit.first.click()
        await page.wait_for_load_state("networkidle")
        return True

    return False


async def poll_and_book(page, slot: dict):
    """Opakovaně refreshuje a zkouší zarezervovat jeden slot."""
    import time as _time
    start     = _time.time()
    total_sec = POLL_TOTAL_MINUTES * 60
    fast_sec  = POLL_FAST_MINUTES  * 60
    attempt   = 0
    slot_time = slot['time']
    slot_date = slot['date']
    slot_lok  = slot['lokalita']
    label     = f"{slot_date} {slot_time} ({slot_lok})"

    while True:
        elapsed = _time.time() - start
        if elapsed > total_sec:
            print(f"  ⏰ Vypršel limit {POLL_TOTAL_MINUTES} minut pro slot {label}")
            return False

        attempt += 1
        remaining = int((total_sec - elapsed) / 60)
        print(f"\n  🔄 [{label}] pokus #{attempt} | zbývá ~{remaining} min")

        await page.reload(wait_until="networkidle")
        await close_any_dialog(page)

        # Před každým pokusem zkontroluj jestli jsme už nezarezervovali
        if await is_already_booked(page, slot):
            return True  # považuj za úspěch

        await setup_dropdowns(page, slot["lokalita"], slot["sport"])
        success = await try_book_slot(page, slot)
        if success:
            return True

        wait = POLL_FAST_SECONDS if elapsed < fast_sec else POLL_SLOW_SECONDS
        phase = "rychlá" if elapsed < fast_sec else "pomalá"
        print(f"  ⏳ Čekám {wait}s ({phase} fáze)...")
        await asyncio.sleep(wait)


async def is_already_booked(page, slot: dict) -> bool:
    """Zkontroluje v gridu jestli buňka ukazuje naši rezervaci (číslo = počet rezervací)."""
    dt          = datetime.strptime(slot["date"], "%Y-%m-%d")
    date_str_cs = dt.strftime("%d.%m.%Y")
    target_time = slot["time"]

    # Hledej v aktuálním gridu – buňka s číslem (1,2..) znamená naše rezervace
    all_rows = await page.locator("tr").all()
    header_idx   = -1
    time_col_idx = -1

    for i, row in enumerate(all_rows):
        texts = [(await c.inner_text()).strip() for c in await row.locator("td, th").all()]
        if len([t for t in texts if len(t) == 5 and t[2] == ':']) >= 3:
            header_idx = i
            for j, t in enumerate(texts):
                if t == target_time:
                    time_col_idx = j
                    break
            break

    if header_idx == -1 or time_col_idx == -1:
        return False

    for i, row in enumerate(all_rows):
        if i <= header_idx:
            continue
        if date_str_cs in (await row.inner_text()).strip():
            cell = row.locator("td, th").nth(time_col_idx)
            text = (await cell.inner_text()).strip()
            # Číslo v buňce = naše rezervace
            if text.isdigit():
                print(f"  ⚠️  Slot {date_str_cs} {target_time} už je zarezervován ('{text}') – přeskakuji!")
                return True
            break

    return False


async def close_any_dialog(page):
    """Zavře jakýkoliv otevřený dialog/modal."""
    # Zkus křížek v dialogu
    for selector in ["a.ui-dialog-titlebar-close", ".ui-dialog-titlebar-close", "span.ui-icon-closethick", "img[src*='close']", "a[title='Zavřít']"]:
        btn = page.locator(selector)
        if await btn.count() > 0:
            await btn.first.click()
            await page.wait_for_timeout(500)
            print("  ✅ Dialog zavřen")
            return
    # Zkus Escape
    await page.keyboard.press("Escape")
    await page.wait_for_timeout(300)


async def handle_slot(page, slot: dict, idx: int, total: int):
    """Zpracuje jeden slot – nejdřív zkusí přímo, pak polluje."""
    label = f"{slot['date']} {slot['time']} ({slot['lokalita']} / {slot['sport']})"
    print(f"\n{'─'*50}")
    print(f"🎯 Slot {idx}/{total}: {label}")
    print(f"{'─'*50}")

    # Zkontroluj jestli slot už není zarezervován
    if await is_already_booked(page, slot):
        return False

    # Reload aby byl grid čerstvý
    await page.reload(wait_until="networkidle")
    await page.wait_for_timeout(1000)
    await close_any_dialog(page)
    await setup_dropdowns(page, slot["lokalita"], slot["sport"])
    success = await try_book_slot(page, slot)

    if not success:
        print(f"  🔁 Spouštím polling (max {POLL_TOTAL_MINUTES} min)...")
        success = await poll_and_book(page, slot)

    if success:
        print(f"  🎉 Slot {label} ZAREZERVOVÁN!")
        await page.screenshot(path=f"rezervace_{idx}.png")
    else:
        print(f"  😕 Slot {label} se nepodařilo zarezervovat.")

    return success


async def main():
    print(f"""
╔══════════════════════════════════════════╗
  Hamrsport Badminton Bot
  Slotů k rezervaci: {len(SLOTS)}""")
    for i, s in enumerate(SLOTS, 1):
        print(f"  {i}. {s['date']} {s['time']} – {s['lokalita']} / {s['sport']}")
    print(f"""  Polling: {POLL_FAST_MINUTES}min po {POLL_FAST_SECONDS}s → {POLL_TOTAL_MINUTES-POLL_FAST_MINUTES}min po {POLL_SLOW_SECONDS}s
╚══════════════════════════════════════════╝""")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(locale="cs-CZ", viewport={"width": 1280, "height": 900})
        page    = await context.new_page()

        try:
            await login(page)

            results = []
            for i, slot in enumerate(SLOTS, 1):
                ok = await handle_slot(page, slot, i, len(SLOTS))
                results.append((slot, ok))

            # Shrnutí
            print(f"\n{'═'*50}")
            print("  VÝSLEDKY:")
            for slot, ok in results:
                status = "✅ OK" if ok else "❌ SELHALO"
                print(f"  {status}  {slot['date']} {slot['time']} {slot['lokalita']}")
            print(f"{'═'*50}")

        except Exception as e:
            print(f"\n💥 Chyba: {e}")
            await page.screenshot(path="error.png")
            raise
        finally:
            print("\nProhlížeč zůstává otevřený 60s...")
            await page.wait_for_timeout(60_000)
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())