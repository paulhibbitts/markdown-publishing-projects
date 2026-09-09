import os, re, json
from html.parser import HTMLParser
import xml.etree.ElementTree as ET

# This script lives in tools/, one level inside the site root (where
# index.html etc. actually are). Switch into the site root first so every
# relative path below works no matter where this is run from -- a terminal
# opened in tools/, in the site root, or anywhere else.
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAGES = ["index.html", "contact.html", "services.html", "fully-open-source-grav-projects.html",
         "about.html", "open-source-with-a-positive-vibe.html", "testimonials.html",
         "dual-purpose-documentation-framework.html", "systems-oriented-design.html"]
# NOTE: keep this list in sync with the identical PAGES list in
# error_check.py, playwright_sweep_v2.py, and sync_boilerplate.py --
# add a new page to all four when one is created.

VOID = {"meta","link","img","br","hr","input","source","area","base","col","embed","param","track","wbr"}

class Balancer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []
    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):
        pass
    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"extra closing </{tag}>")
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        else:
            if tag in self.stack:
                while self.stack and self.stack[-1] != tag:
                    self.errors.append(f"mismatched: expected </{self.stack[-1]}> got </{tag}>")
                    self.stack.pop()
                if self.stack:
                    self.stack.pop()
            else:
                self.errors.append(f"unexpected closing </{tag}> with no matching open")

print("=== TAG BALANCE ===")
all_ok = True
for p in PAGES:
    html = open(p, encoding="utf-8").read()
    b = Balancer()
    b.feed(html)
    if b.stack or b.errors:
        all_ok = False
        print(f"{p}: FAIL stack={b.stack} errors={b.errors}")
    else:
        print(f"{p}: OK")

print("\n=== JSON-LD ===")
for p in PAGES:
    html = open(p, encoding="utf-8").read()
    scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not scripts:
        print(f"{p}: (none)")
        continue
    for s in scripts:
        try:
            json.loads(s)
            print(f"{p}: OK ({len(s)} chars)")
        except Exception as e:
            all_ok = False
            print(f"{p}: FAIL {e}")

print("\n=== SITEMAP ===")
try:
    tree = ET.parse("sitemap.xml")
    root = tree.getroot()
    locs = [el.text for el in root.iter() if el.tag.endswith("loc")]
    print(f"OK, {len(locs)} urls:")
    for l in locs:
        print(" ", l)
except Exception as e:
    all_ok = False
    print(f"FAIL {e}")

print("\n=== LINK / ANCHOR AUDIT ===")
href_re = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>', re.I)
tag_re = re.compile(r'<a\s+([^>]*)href="([^"]+)"([^>]*)>', re.I)
notion_hits = []
for p in PAGES:
    html = open(p, encoding="utf-8").read()
    ids = set(re.findall(r'id="([^"]+)"', html))
    for m in tag_re.finditer(html):
        pre, href, post = m.groups()
        attrs = pre + post
        if "notion" in href.lower():
            notion_hits.append((p, href))
        if href.startswith("https://hibbittsdesign.org"):
            # same-site absolute link (e.g. the home link) -- behaves like an
            # internal relative link: navigates in place, no target=_blank.
            if 'target="_blank"' in attrs:
                print(f"{p}: same-site link should not have target=_blank: {href}")
                all_ok = False
            local_path = href[len("https://hibbittsdesign.org"):].split("#")[0].lstrip("/")
            if local_path and not os.path.exists(local_path):
                print(f"{p}: same-site link target missing: {href}")
                all_ok = False
        elif href.startswith("http"):
            if 'target="_blank"' not in attrs or 'rel="noopener"' not in attrs:
                print(f"{p}: external link missing target/rel: {href}")
                all_ok = False
        elif href.startswith("#"):
            anchor = href[1:]
            if anchor and anchor not in ids:
                print(f"{p}: in-page anchor #{anchor} has no matching id")
                all_ok = False
            if 'target="_blank"' in attrs:
                print(f"{p}: anchor link should not have target=_blank: {href}")
                all_ok = False
        elif href.startswith("mailto:"):
            if 'target="_blank"' in attrs:
                print(f"{p}: mailto link should not have target=_blank: {href}")
                all_ok = False
        else:
            # internal relative link. Links to another page on the site
            # navigate in place (no target=_blank); links straight to an
            # asset file (e.g. a full-size image) are a "view/zoom" pattern,
            # not page navigation, so target=_blank is expected there.
            target = href.split("#")[0]
            is_asset_link = bool(re.search(r'\.(?!html$)[a-zA-Z0-9]+$', target))
            if 'target="_blank"' in attrs and not is_asset_link:
                print(f"{p}: internal link should not have target=_blank: {href}")
                all_ok = False
            if is_asset_link and 'target="_blank"' not in attrs:
                print(f"{p}: internal asset link should have target=_blank: {href}")
                all_ok = False
            if target and not os.path.exists(target):
                print(f"{p}: internal link target missing: {href}")
                all_ok = False

if notion_hits:
    all_ok = False
    print("NOTION LINKS FOUND:", notion_hits)
else:
    print("No notion.com / notion.site / notion-related hrefs found across all pages. OK")

print("\n=== SHARED BOILERPLATE CONSISTENCY ===")
# The header/nav block and the footer block are meant to be byte-identical
# across every page (they're hand-copied, not templated/included). This
# catches accidental drift early -- e.g. a wording or entity fix applied to
# one page's footer but missed on another -- rather than relying on someone
# noticing visually. If a divergence is ever intentional, update PAGES-aware
# logic here rather than deleting this check.
header_re = re.compile(r'<header class="site-head">.*?</header>', re.S)
footer_re = re.compile(r'<footer>.*?</footer>', re.S)
ref_page = PAGES[0]
ref_html = open(ref_page, encoding="utf-8").read()
ref_header_m = header_re.search(ref_html)
ref_footer_m = footer_re.search(ref_html)
ref_header = ref_header_m.group(0) if ref_header_m else None
ref_footer = ref_footer_m.group(0) if ref_footer_m else None
if ref_header is None:
    all_ok = False
    print(f"{ref_page}: FAIL could not find <header class=\"site-head\"> block")
if ref_footer is None:
    all_ok = False
    print(f"{ref_page}: FAIL could not find <footer> block")

boilerplate_ok = True
for p in PAGES:
    html = open(p, encoding="utf-8").read()
    hm = header_re.search(html)
    fm = footer_re.search(html)
    h = hm.group(0) if hm else None
    f = fm.group(0) if fm else None
    if h is None:
        all_ok = False
        boilerplate_ok = False
        print(f"{p}: FAIL no <header class=\"site-head\"> block found")
    elif ref_header is not None and h != ref_header:
        all_ok = False
        boilerplate_ok = False
        print(f"{p}: FAIL header block differs from {ref_page}")
    if f is None:
        all_ok = False
        boilerplate_ok = False
        print(f"{p}: FAIL no <footer> block found")
    elif ref_footer is not None and f != ref_footer:
        all_ok = False
        boilerplate_ok = False
        print(f"{p}: FAIL footer block differs from {ref_page}")
if boilerplate_ok:
    print(f"OK, header and footer blocks byte-identical across all {len(PAGES)} pages")

print("\n=== OVERALL:", "PASS" if all_ok else "FAIL", "===")
