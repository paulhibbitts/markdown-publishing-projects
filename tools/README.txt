HibbittsDesign.org — maintenance scripts
=========================================

This tools/ folder lives inside the site itself, but it is blocked from
web access by tools/.htaccess (which denies all HTTP requests to this
folder and everything in it) and excluded from crawling by the
"Disallow: /tools/" line in the site's robots.txt. Nothing in here is
part of the published site -- it's just stored alongside it for
convenience. Don't remove tools/.htaccess.

SETUP
-----
1. You need Python 3 installed (macOS/Linux usually have it already; on
   Windows, install from python.org and make sure "Add to PATH" is checked).
2. That's it for the three scripts below -- no other install needed. They
   work out of a terminal wherever this folder happens to be (the site
   root, a local copy, wherever), because each one locates the site root
   relative to its own location rather than assuming a particular folder
   you launched the terminal from.

THE THREE YOU CAN RUN RIGHT AWAY (no extra installs needed)
-------------------------------------------------------------
  python3 tools/verify_all_v2.py
      Checks the whole site for real problems: unbalanced HTML tags,
      broken structured data, sitemap mismatches, broken/misconfigured
      links, and whether the header/nav, footer, and Google Analytics
      snippet are still identical across all nine pages. Prints PASS or
      FAIL with details.

  python3 tools/sync_boilerplate.py
      If you ever want to change the wording in the site's shared header/
      nav or footer, or update the Google Analytics snippet (e.g. a new
      tracking ID), WITHOUT going through a Claude session: edit
      tools/partials/header.html, tools/partials/footer.html, or
      tools/partials/analytics.html directly (plain HTML, no special
      syntax), then run this script from anywhere. It pushes your edit
      out to all nine live HTML pages automatically and tells you which
      pages it changed. Run verify_all_v2.py afterward to double-check
      everything still matches.

  python3 tools/error_check.py
      A second, independent static check, focused on things
      verify_all_v2.py doesn't cover: duplicate id="..." attributes,
      <img> tags missing alt text, roughly-unclosed tags, broken
      relative links/anchors, and missing image/CSS/JS/font file
      references. Like verify_all_v2.py, this is pure text/HTML
      parsing -- no browser involved, despite the name.

All three work the same way from the site's root folder
(`python3 tools/verify_all_v2.py`) or from inside tools/ itself
(`cd tools && python3 verify_all_v2.py`).

THE ONE THAT NEEDS EXTRA SETUP (optional — a real browser, not just Python)
------------------------------------------------------------------------
  tools/playwright_sweep_v2.py
      Needs the Playwright package and a downloaded browser:
        pip3 install playwright
        python3 -m playwright install chromium
      Then: python3 tools/playwright_sweep_v2.py
      Loads every page in a real headless browser at three widths
      (desktop/tablet/phone) and both light/dark mode, and checks for
      actual console errors, layout overflow (something spilling off
      the edge of the screen), and a heuristic for stray Markdown
      syntax that leaked into rendered HTML instead of being converted.
      It does NOT save screenshots or any image files -- it's a
      programmatic check, not a visual diff, and just prints a report.
      Heaviest setup of the four — most useful after visual changes.

A NOTE ON THE PAGES LIST
-------------------------
Each script has its own hardcoded list of the site's nine page filenames
near the top (a "PAGES = [...]" line). If a tenth page ever gets added to
the site, that list needs updating in all four scripts — each one has a
comment reminding you (and any future Claude session) of that.
