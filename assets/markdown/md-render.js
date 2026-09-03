/*
 * Prose-level Markdown support for static HTML pages
 * ----------------------------------------------------
 * Lets you write page copy as Markdown instead of hand-balanced HTML tags,
 * while leaving all page structure, layout and CSS classes exactly as-is.
 * Requires marked.js (marked.min.js, next to this file — vendor any version
 * of https://github.com/markedjs/marked, loaded as a <script> before this
 * file).
 *
 * HOW TO REUSE THIS ON ANOTHER PAGE
 * ----------------------------------
 * 1. Copy this whole folder (marked.min.js + this file) into your project,
 *    e.g. as assets/markdown/ — keeping the two together and separate from
 *    your other assets is what makes this drop-in portable.
 * 2. Load both before </body>, marked.min.js first:
 *      <script src="assets/markdown/marked.min.js"></script>
 *      <script src="assets/markdown/md-render.js"></script>
 * 3. Mark up your prose:
 *      - A single line/paragraph of inline Markdown (**bold**, [links](url)):
 *          <p data-md>Some **bold** text with a [link](https://example.com).</p>
 *        Works on any element that should keep its own tag (<p>, <li>, a
 *        <span> inside a larger block, etc.) — only inline markup is parsed,
 *        so it won't wrap the result in a stray <p>.
 *      - A bullet list, keeping your own <ul> and its class/styling:
 *          <ul class="feat-list" data-md-list>
 *            - First item
 *            - Second item with a [link](https://example.com)
 *          </ul>
 *        Each "- " line becomes an <li>; the <ul> itself, and whatever
 *        classes it already has, are left untouched.
 * 4. That's it — no build step. The elements' raw text is read, parsed by
 *    marked.js on page load, and swapped in as rendered HTML.
 *
 * CUSTOMIZING LINK OUTPUT
 * ------------------------
 * The block below tells marked.js how to render every link on the page:
 * external links (anything not starting with "#") automatically get
 * target="_blank" rel="noopener", and https:// links get one CSS class
 * applied so they can be styled distinctly from in-page anchors. Change or
 * delete EXTERNAL_LINK_CLASS, or the attributes below, to match your own
 * site's link conventions — this is the only project-specific part of this
 * file; everything else is generic.
 */
(function () {
  var EXTERNAL_LINK_CLASS = 'tlink'; // set to '' to skip adding a class

  marked.use({
    renderer: {
      link: function (token) {
        var href = token.href;
        var text = this.parser.parseInline(token.tokens);
        var isExternal = href.indexOf('#') !== 0;
        var isHttp = /^https?:\/\//.test(href);
        var attrs = isExternal ? ' target="_blank" rel="noopener"' : '';
        var cls = isHttp && EXTERNAL_LINK_CLASS ? ' class="' + EXTERNAL_LINK_CLASS + '"' : '';
        return '<a href="' + href + '"' + cls + attrs + '>' + text + '</a>';
      }
    }
  });

  // Inline elements: render in place, keep the element's own tag.
  document.querySelectorAll('[data-md]').forEach(function (el) {
    el.innerHTML = marked.parseInline(el.textContent.trim());
  });

  // Bullet lists: parse as a block (so "- " lines become real <li>s), then
  // graft just the <li> children onto the original <ul> — its tag, class
  // and any other attributes are left exactly as authored.
  document.querySelectorAll('[data-md-list]').forEach(function (el) {
    // Each line needs its own leading whitespace stripped (not just the
    // block's outer edges) — Markdown lists only continue past 3 spaces
    // of indentation, and HTML source indentation is usually much more.
    var source = el.textContent
      .split('\n')
      .map(function (line) { return line.trim(); })
      .filter(Boolean)
      .join('\n');
    var wrapper = document.createElement('div');
    wrapper.innerHTML = marked.parse(source);
    var parsedList = wrapper.querySelector('ul, ol');
    el.innerHTML = parsedList ? parsedList.innerHTML : wrapper.innerHTML;
  });
})();
