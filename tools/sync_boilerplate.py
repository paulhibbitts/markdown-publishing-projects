"""
sync_boilerplate.py — single source of truth for the header/nav block, the
footer block, and the Google Analytics snippet that are hand-copied into
all nine pages.

The site itself stays plain, dependency-free static HTML with every block
fully inlined on every page (no client-side includes -- this site's own
convention is that body content must exist in the raw HTML for crawlers and
no-JS visitors, and that applies just as much to nav/footer chrome). What
this script removes is the *editing* toil: instead of hand-changing the
header, footer, or analytics snippet on nine files and hoping none get
missed, edit ONE file in partials/ and run this script to push it out
everywhere.

Workflow for any header, footer, or analytics text/markup change going forward:
  1. Edit tools/partials/header.html, tools/partials/footer.html, or
     tools/partials/analytics.html (exact HTML that goes between
     <header class="site-head">...</header>, <footer>...</footer>, or
     <!-- GOOGLE ANALYTICS START -->...<!-- GOOGLE ANALYTICS END -->,
     inclusive of those tags/markers).
  2. Run: python3 sync_boilerplate.py
  3. Run verify_all_v2.py -- its "SHARED BOILERPLATE CONSISTENCY" check
     will confirm all nine pages now match the partials.

Safe to run any time, including with no partial changes -- pages that
already match are left untouched (no spurious diffs), and it prints exactly
which pages it modified.
"""
import os, re

# This script lives in tools/, one level inside the site root (where
# index.html etc. actually are); partials/ is its own sibling subfolder
# inside tools/, not at the site root. Resolve both locations from this
# script's own path so it works no matter where it's run from.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SITE_ROOT = os.path.dirname(_SCRIPT_DIR)
_PARTIALS_DIR = os.path.join(_SCRIPT_DIR, "partials")

PAGES = ["index.html", "contact.html", "services.html", "fully-open-source-grav-projects.html",
         "about.html", "open-source-with-a-positive-vibe.html", "testimonials.html",
         "dual-purpose-documentation-framework.html", "systems-oriented-design.html"]
# NOTE: keep this list in sync with the identical PAGES list in
# verify_all_v2.py, error_check.py, and playwright_sweep_v2.py --
# add a new page to all four when one is created.

header_re = re.compile(r'<header class="site-head">.*?</header>', re.S)
footer_re = re.compile(r'<footer>.*?</footer>', re.S)
analytics_re = re.compile(r'<!-- GOOGLE ANALYTICS START.*?GOOGLE ANALYTICS END -->', re.S)

with open(os.path.join(_PARTIALS_DIR, "header.html"), encoding="utf-8") as fh:
    new_header = fh.read().strip()
with open(os.path.join(_PARTIALS_DIR, "footer.html"), encoding="utf-8") as fh:
    new_footer = fh.read().strip()
with open(os.path.join(_PARTIALS_DIR, "analytics.html"), encoding="utf-8") as fh:
    new_analytics = fh.read().strip()

changed = []
unchanged = []
missing = []
for p in PAGES:
    page_path = os.path.join(_SITE_ROOT, p)
    with open(page_path, encoding="utf-8") as fh:
        html = fh.read()

    if not header_re.search(html) or not footer_re.search(html) or not analytics_re.search(html):
        missing.append(p)
        continue

    updated = header_re.sub(lambda m: new_header, html, count=1)
    updated = footer_re.sub(lambda m: new_footer, updated, count=1)
    updated = analytics_re.sub(lambda m: new_analytics, updated, count=1)

    if updated != html:
        with open(page_path, "w", encoding="utf-8") as fh:
            fh.write(updated)
        changed.append(p)
    else:
        unchanged.append(p)

print(f"Updated ({len(changed)}):", changed if changed else "(none)")
print(f"Already matched ({len(unchanged)}):", unchanged if unchanged else "(none)")
if missing:
    print(f"WARNING -- no <header class=\"site-head\">, <footer>, or GOOGLE ANALYTICS block found in ({len(missing)}):", missing)
