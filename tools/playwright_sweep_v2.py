import asyncio, os
from playwright.async_api import async_playwright

# This script lives in tools/, one level inside the site root (where
# index.html etc. actually are). Switch into the site root first so every
# relative path below works no matter where this is run from.
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAGES = ["index.html", "contact.html", "services.html", "fully-open-source-grav-projects.html",
         "about.html", "open-source-with-a-positive-vibe.html", "testimonials.html",
         "dual-purpose-documentation-framework.html", "systems-oriented-design.html"]
# NOTE: keep this list in sync with the identical PAGES list in
# verify_all_v2.py, error_check.py, and sync_boilerplate.py --
# add a new page to all four when one is created.
WIDTHS = [1280, 390, 320]
SCHEMES = ["light", "dark"]

async def main():
    base = "file://" + os.getcwd() + "/"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        issues = []
        for page_name in PAGES:
            for width in WIDTHS:
                for scheme in SCHEMES:
                    ctx = await browser.new_context(viewport={"width": width, "height": 900}, color_scheme=scheme)
                    pg = await ctx.new_page()
                    console_errors = []
                    failed = []
                    pg.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                    pg.on("requestfailed", lambda req: failed.append((req.url, req.failure)))
                    await pg.goto(base + page_name, wait_until="networkidle")
                    await pg.wait_for_timeout(300)
                    # overflow check
                    overflow = await pg.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
                    # leaked markdown check (common syntax leaks)
                    body_text = await pg.inner_text("body")
                    leaks = []
                    for marker in ["**", "](", "##"]:
                        if marker in body_text:
                            leaks.append(marker)
                    if overflow:
                        issues.append(f"{page_name} @ {width}px {scheme}: HORIZONTAL OVERFLOW")
                    if leaks:
                        issues.append(f"{page_name} @ {width}px {scheme}: possible markdown leak {leaks}")
                    real_failed = [f for f in failed if "tally.so" not in f[0] and page_name == "contact.html"]
                    unexpected_failed = [f for f in failed if not ("contact.html" == page_name and "tally" in f[0].lower())]
                    if unexpected_failed:
                        issues.append(f"{page_name} @ {width}px {scheme}: failed requests {unexpected_failed}")
                    if console_errors:
                        issues.append(f"{page_name} @ {width}px {scheme}: console errors {console_errors}")
                    await ctx.close()
        await browser.close()
        print(f"Checked {len(PAGES)} pages x {len(WIDTHS)} widths x {len(SCHEMES)} schemes")
        if issues:
            print("ISSUES FOUND:")
            for i in issues:
                print(" -", i)
        else:
            print("NO ISSUES FOUND. ALL CLEAN.")

asyncio.run(main())
