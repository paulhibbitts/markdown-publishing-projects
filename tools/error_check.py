import os, re, glob
from html.parser import HTMLParser

# This script lives in tools/, one level inside the site root (where
# index.html etc. actually are). Switch into the site root first so every
# relative path below works no matter where this is run from.
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PAGES = ["index.html", "contact.html", "services.html", "fully-open-source-grav-projects.html",
         "about.html", "open-source-with-a-positive-vibe.html", "testimonials.html",
         "dual-purpose-documentation-framework.html", "systems-oriented-design.html"]
# NOTE: keep this list in sync with the identical PAGES list in
# verify_all_v2.py, playwright_sweep_v2.py, and sync_boilerplate.py --
# add a new page to all four when one is created.

class PageScan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.srcs = []
        self.ids = []
        self.alt_missing = []
        self.tag_stack = []
        self.self_closing = {"img","br","hr","meta","link","input","source","area","base","col","embed","track","wbr"}

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag not in self.self_closing:
            self.tag_stack.append(tag)
        if "href" in d:
            self.hrefs.append(d["href"])
        if tag == "img":
            if "src" in d:
                self.srcs.append(d["src"])
            if "alt" not in d:
                self.alt_missing.append(d.get("src","(no src)"))
        if "id" in d:
            self.ids.append(d["id"])

    def handle_endtag(self, tag):
        if tag in self.tag_stack[::-1]:
            # pop most recent matching
            for i in range(len(self.tag_stack)-1, -1, -1):
                if self.tag_stack[i] == tag:
                    del self.tag_stack[i]
                    break

issues = []
all_ids_by_page = {}

for page in PAGES:
    with open(page, encoding="utf-8") as f:
        content = f.read()
    p = PageScan()
    p.feed(content)
    all_ids_by_page[page] = set(p.ids)

    # duplicate ids
    dupes = set([i for i in p.ids if p.ids.count(i) > 1])
    if dupes:
        issues.append(f"{page}: DUPLICATE ids {dupes}")

    # missing alt
    if p.alt_missing:
        issues.append(f"{page}: <img> missing alt attribute: {p.alt_missing}")

    # unclosed tags (rough)
    if p.tag_stack:
        issues.append(f"{page}: possibly unclosed tags {p.tag_stack}")

    for href in p.hrefs:
        if href.startswith("https://hibbittsdesign.org"):
            # same-site absolute link (e.g. the home link) -- resolve to a
            # local file just like a relative link would.
            local_path = href[len("https://hibbittsdesign.org"):].split("#")[0].lstrip("/")
            if local_path and not os.path.exists(local_path):
                issues.append(f"{page}: same-site link to '{href}' -> file '{local_path}' NOT FOUND")
            continue
        if href.startswith(("http://", "https://", "mailto:", "tel:")):
            continue
        if href.startswith("#"):
            anchor = href[1:]
            if anchor and anchor not in p.ids:
                issues.append(f"{page}: in-page anchor '#{anchor}' has no matching id on same page")
            continue
        # relative link, possibly with anchor
        if "#" in href:
            target_file, anchor = href.split("#", 1)
        else:
            target_file, anchor = href, None
        if target_file == "":
            continue
        target_path = target_file
        if not os.path.exists(target_path):
            issues.append(f"{page}: link to '{href}' -> file '{target_file}' NOT FOUND")
            continue
        if anchor and target_file.endswith(".html"):
            # need to check anchor exists in target file (parse it if not already)
            with open(target_file, encoding="utf-8") as tf:
                tcontent = tf.read()
            tp = PageScan()
            tp.feed(tcontent)
            if anchor not in tp.ids:
                issues.append(f"{page}: link '{href}' -> anchor '#{anchor}' NOT FOUND in {target_file}")

    for src in p.srcs:
        if src.startswith(("http://", "https://", "data:")):
            continue
        if not os.path.exists(src):
            issues.append(f"{page}: <img src='{src}'> NOT FOUND")

# check other asset references (css url(), script src, link href) quickly
for page in PAGES:
    with open(page, encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(r'(?:src|href)="([^"]+\.(?:js|css|png|webp|jpg|jpeg|svg|ico|woff2?|ttf))"', content):
        ref = m.group(1)
        if ref.startswith(("http://", "https://")):
            continue
        if not os.path.exists(ref):
            issues.append(f"{page}: asset reference '{ref}' NOT FOUND")

print(f"Checked {len(PAGES)} pages.")
if issues:
    print(f"ISSUES FOUND ({len(issues)}):")
    for i in issues:
        print(" -", i)
else:
    print("NO ISSUES FOUND. ALL CLEAN.")
