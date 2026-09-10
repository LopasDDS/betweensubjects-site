"""Build the Between Subjects site from `episodes.json` and `notes/`.

Every page here is generated. The source of truth is the notes directory —
the same research notes each video was written from — plus the episode index
exported from the publishing tool. Editing the HTML by hand will be undone by
the next build; edit the notes or the template and re-run:

    python build.py

No dependencies beyond the standard library, so it runs anywhere.
"""

from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
NOTES = ROOT / "notes"
EPISODES_DIR = ROOT / "episodes"

BASE_URL = "https://lopasdds.github.io/betweensubjects-site/"
SITE_NAME = "Between Subjects"
TAGLINE = "What the famous psychology studies actually found."
CONTACT = "allaboutfrankel@gmail.com"

YOUTUBE_CHANNEL = "https://www.youtube.com/@betweensubjects"
FACEBOOK_PAGE = "https://www.facebook.com/1219727847900870"

PLATFORM_LABELS = {"youtube": "YouTube", "tiktok": "TikTok", "facebook": "Facebook"}

#: Paragraphs in the notes begin with a lead-in that names the section. They
#: are written as instructions to the person drafting the script, which is what
#: they are — so a few are relabelled for a reader, and the rest stand as they
#: are. Longest first, so "Limits that must be stated." wins over "Limits".
SECTION_LEADS = {
    "What this must not be heard as.": "What this does not show",
    "What should not be overstated.": "What this does not show",
    "What may not be said.": "What this does not show",
    "Limits that must be stated.": "Limits",
    "Limits worth stating.": "Limits",
    "The part that is usually left out.": "The part usually left out",
    "What the retelling leaves out.": "What the retelling leaves out",
    "What that number leaves out.": "What that number leaves out",
    "What the data actually show.": "What the data actually show",
    "What the paper reported:": "What the paper reported",
    "What the paper claimed.": "What the paper claimed",
    "What it establishes:": "What it establishes",
    "What is true:": "What is true",
    "What they compared.": "What they compared",
    "What happened next.": "What happened next",
    "What this changes.": "What this changes",
    "Why defaults work.": "Why defaults work",
    "Then the part that makes this unusual.": "The unusual part",
    "Note on illustrations:": "A note on illustrations",
}
SUMMARY_LEAD = "Accurate summary:"


def unwrap(block: str) -> str:
    """The notes are hard-wrapped for editing; the web is not."""
    return " ".join(line.strip() for line in block.splitlines() if line.strip())


def sentence_case(text: str) -> str:
    """Restore a capital after a lead-in has been lifted out into a heading.

    In the notes the section name is the start of the sentence, so "What it
    establishes: competition over..." leaves a lowercase word behind once the
    lead-in becomes an <h3>.
    """
    return text[:1].upper() + text[1:] if text else text


def summarise(text: str, limit: int = 175) -> str:
    """A meta description, cut at a word boundary rather than mid-word."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"


def inline(text: str) -> str:
    """Escape, then restore the little formatting the notes use."""
    out = html.escape(text, quote=False)
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    # Straight quotes read as code on a page of prose.
    out = re.sub(r'"([^"]+)"', r"&ldquo;\1&rdquo;", out)
    out = out.replace("'", "&rsquo;")
    return out


def parse_notes(path: Path) -> tuple[str, str, list[tuple[str | None, str]]]:
    """Split a notes file into its title, its summary, and its sections."""
    blocks = [b for b in path.read_text(encoding="utf-8").split("\n\n") if b.strip()]
    title = unwrap(blocks[0])
    summary = ""
    sections: list[tuple[str | None, str]] = []

    for block in blocks[1:]:
        text = unwrap(block)
        if text.startswith(SUMMARY_LEAD):
            summary = sentence_case(text[len(SUMMARY_LEAD) :].strip())
            continue
        for lead, heading in SECTION_LEADS.items():
            if text.startswith(lead):
                sections.append((heading, sentence_case(text[len(lead) :].strip())))
                break
        else:
            sections.append((None, text))
    return title, summary, sections


def render_sections(sections: list[tuple[str | None, str]]) -> str:
    parts = []
    for heading, text in sections:
        if heading:
            parts.append(f"<h3>{inline(heading)}</h3>")
        parts.append(f"<p>{inline(text)}</p>")
    return "\n".join(parts)


def watch_links(links: dict[str, str], classes: str = "watch") -> str:
    if not links:
        return ""
    items = [
        f'<a class="pill" href="{html.escape(url)}" rel="noopener">'
        f"Watch on {PLATFORM_LABELS.get(key, key.title())}</a>"
        for key, url in sorted(links.items())
        if url
    ]
    return f'<p class="{classes}">' + "".join(items) + "</p>"


def pretty_date(iso: str) -> str:
    y, m, d = (int(part) for part in iso.split("-"))
    return date(y, m, d).strftime("%d %B %Y").lstrip("0")


def page(title: str, description: str, body: str, depth: int = 0) -> str:
    """The shared shell. `depth` is how many directories deep the page sits."""
    up = "../" * depth
    nav = "".join(
        f'<a href="{up}{href}">{label}</a>'
        for href, label in (
            ("index.html", "Home"),
            ("episodes.html", "Episodes"),
            ("method.html", "Method"),
            ("about.html", "About"),
        )
    )
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="stylesheet" href="{up}style.css">
<header class="site">
  <a class="brand" href="{up}index.html">{SITE_NAME}</a>
  <nav>{nav}</nav>
</header>
<main>
{body}
</main>
<footer class="site">
  <p><strong>{SITE_NAME}</strong> &mdash; {html.escape(TAGLINE)}</p>
  <p class="links">
    <a href="{up}episodes.html">Episodes</a>
    <a href="{up}method.html">Method</a>
    <a href="{up}about.html">About</a>
    <a href="{up}terms.html">Terms of Service</a>
    <a href="{up}privacy.html">Privacy Policy</a>
  </p>
  <p class="muted">Written and checked by hand against the papers named on each page.
     Corrections to <a href="mailto:{CONTACT}">{CONTACT}</a>.</p>
</footer>
</html>
"""


def build_episode(ep: dict, notes: dict) -> str:
    title, summary, sections = notes[ep["slug"]]
    body = f"""
<article class="episode">
  <p class="crumb"><a href="../episodes.html">&larr; All episodes</a></p>
  <h1>{inline(ep["title"])}</h1>
  <p class="sub">{inline(title)} &middot; published {pretty_date(ep["published"])}</p>
  {watch_links(ep["links"])}

  <blockquote class="summary">
    <p>{inline(summary)}</p>
  </blockquote>

  <h2>The angle</h2>
  <p>{inline(ep["angle"])}</p>

  <h2>The notes this episode was written from</h2>
  <p class="note">These are the working notes, unedited. Everything the video
     states as fact comes from here, and nothing else may be stated as fact.
     The sections on limits and on what the finding does <em>not</em> show are
     part of the brief, not an afterthought &mdash; see
     <a href="../method.html">the method</a>.</p>
  <div class="notes">
{render_sections(sections)}
  </div>
</article>
"""
    return page(f"{ep['title']} — {SITE_NAME}", summarise(summary), body, depth=1)


def build_episode_index(episodes: list[dict], notes: dict) -> str:
    cards = []
    for ep in reversed(episodes):
        _, summary, _ = notes[ep["slug"]]
        cards.append(
            f"""<li class="card">
  <h2><a href="episodes/{ep["slug"]}.html">{inline(ep["title"])}</a></h2>
  <p class="date">{pretty_date(ep["published"])}</p>
  <p>{inline(summary)}</p>
  {watch_links(ep["links"], "watch small")}
</li>"""
        )
    body = f"""
<h1>Episodes</h1>
<p class="sub">{len(episodes)} so far. Each page carries the research notes the
   video was written from, including the limits.</p>
<ul class="cards">
{"".join(cards)}
</ul>
"""
    return page(f"Episodes — {SITE_NAME}", "Every Between Subjects episode, with sources.", body)


def build_home(episodes: list[dict], notes: dict) -> str:
    latest = []
    for ep in list(reversed(episodes))[:6]:
        _, summary, _ = notes[ep["slug"]]
        latest.append(
            f"""<li class="card">
  <h3><a href="episodes/{ep["slug"]}.html">{inline(ep["title"])}</a></h3>
  <p class="date">{pretty_date(ep["published"])}</p>
  <p>{inline(summary)}</p>
</li>"""
        )
    body = f"""
<section class="hero">
  <h1>{SITE_NAME}</h1>
  <p class="lede">{html.escape(TAGLINE)}</p>
  <p>Short videos about psychology and behavioural science research &mdash; what
     the well-known studies actually found, and where the popular retelling
     departs from the record. The Stanford prison guards, Milgram&rsquo;s fourth
     prod, the Dunning-Kruger chart that is not in the Dunning-Kruger paper.</p>
  <p class="watch">
    <a class="pill" href="{YOUTUBE_CHANNEL}" rel="noopener">YouTube</a>
    <a class="pill" href="{FACEBOOK_PAGE}" rel="noopener">Facebook</a>
  </p>
</section>

<section>
  <h2>Why the retelling drifts</h2>
  <p>A finding gets simpler every time it is repeated. The qualifier goes first,
     then the sample size, then the condition that made it work. What is left is
     a clean story that the paper does not support &mdash; and it is usually the
     version that gets taught.</p>
  <p>These videos go back to what was actually measured. Often the real finding
     is stranger than the myth: Milgram ran more than twenty variations and the
     prod that sounded most like a direct order was the one nobody obeyed;
     Robbers Cave worked on the second attempt, after the first collapsed
     because the boys had been allowed to become friends first.</p>
  <p>Just as often the correction cuts the other way. The Kitty Genovese story
     is mostly wrong and the bystander effect is real anyway. Saying so is the
     point &mdash; <a href="method.html">how each episode is checked</a>.</p>
</section>

<section>
  <h2>Latest episodes</h2>
  <ul class="cards">
{"".join(latest)}
  </ul>
  <p><a href="episodes.html">All {len(episodes)} episodes &rarr;</a></p>
</section>
"""
    return page(SITE_NAME, TAGLINE, body)


def build_method(episodes: list[dict]) -> str:
    body = f"""
<h1>Method</h1>
<p class="sub">How an episode gets made, and what it is not allowed to say.</p>

<h2>Nothing is stated as fact unless it is in the notes</h2>
<p>Each episode starts as a page of research notes: what the study did, how many
   people were in it, what it measured, what it found, and where that has since
   been corrected or failed to replicate. Those notes are the only material the
   script may state as fact. A number, a date, a name or a result that is not in
   them cannot appear in the video.</p>
<p>The notes are published alongside every episode, so the check is available to
   anyone who wants to make it. Start with
   <a href="episodes/robbers-cave.html">Robbers Cave</a> or
   <a href="episodes/power-posing.html">power posing</a>.</p>

<h2>The limits are part of the brief</h2>
<p>Every set of notes carries a section on what the finding does <em>not</em>
   show. That section exists because the failure mode of this format is not
   inventing things &mdash; it is telling a true story that leaves the viewer
   with a false impression.</p>
<p>Some examples of what that rules out. The false-memory research does not show
   that people who report abuse should be doubted, and the episode may not imply
   it. The Stanford prison experiment being badly run does not mean situations
   never shape behaviour. Ego depletion failing to replicate does not mean
   self-control is a myth. Each of those is written into the notes before a
   script exists.</p>

<h2>Qualifiers survive the edit</h2>
<p>The strongest pull on a short video is toward the flatter, louder claim.
   &ldquo;Measures more than willpower&rdquo; wants to become &ldquo;isn&rsquo;t
   a willpower test&rdquo;; that is a different and bigger claim, and it is the
   one a viewer would remember. Titles and scripts are held to the hedge the
   research actually carries.</p>

<h2>Corrections</h2>
<p>If something here is wrong, write to
   <a href="mailto:{CONTACT}">{CONTACT}</a> and say which episode and what the
   record says. Corrections go on the episode page.</p>

<h2>How the videos are made</h2>
<p>The narration is synthesised speech, and the footage is generated rather than
   filmed &mdash; typically one continuous shot of an object from the study, or a
   texture with no claim to being a real place. No image on this channel is
   presented as documentary footage of the research it accompanies. Everything
   that matters is in the words.</p>
<p>Publishing to {len(episodes)} episodes&rsquo; worth of accounts is handled by
   an in-house tool, which is what the <a href="terms.html">terms</a> and
   <a href="privacy.html">privacy policy</a> describe. It posts only to accounts
   this channel owns.</p>
"""
    return page(f"Method — {SITE_NAME}", "How each episode is researched and checked.", body)


def build_about(episodes: list[dict]) -> str:
    body = f"""
<h1>About</h1>
<p class="sub">{html.escape(TAGLINE)}</p>

<p>{SITE_NAME} is a small independent channel publishing short videos on
   psychology and behavioural science. It takes its name from the experimental
   design where each participant sees only one condition &mdash; you compare
   between subjects, never within one.</p>

<p>The channel covers the studies everyone has heard of, and the gap between
   what they found and what they are quoted as finding. There are
   {len(episodes)} episodes so far, published to YouTube, TikTok and Facebook.
   Every one of them has a page here with its sources and its limits.</p>

<h2>Where to watch</h2>
<p class="watch">
  <a class="pill" href="{YOUTUBE_CHANNEL}" rel="noopener">YouTube</a>
  <a class="pill" href="{FACEBOOK_PAGE}" rel="noopener">Facebook</a>
</p>

<h2>Contact</h2>
<p>Corrections, questions and requests: <a href="mailto:{CONTACT}">{CONTACT}</a>.
   Corrections are the ones that get answered first.</p>

<h2>Reading</h2>
<p>Where an episode rests on a book rather than a paper, the book is named in the
   notes on that episode&rsquo;s page &mdash; Gina Perry&rsquo;s
   <em>The Lost Boys</em> for Robbers Cave, Thibault Le Texier&rsquo;s archival
   work on the Stanford prison experiment, Kevin Cook on the Genovese case.
   Everything else is journal literature, cited by author and year.</p>
"""
    return page(f"About — {SITE_NAME}", "About the Between Subjects channel.", body)


#: The legal pages are hand-written prose that the generator only wraps. They
#: live as fragments in `pages/` so there is one shell for the whole site
#: rather than two that drift apart.
LEGAL_PAGES = {
    "terms": ("Terms of Service", "Terms of service for the Between Subjects publishing tool."),
    "privacy": ("Privacy Policy", "Privacy policy for the Between Subjects publishing tool."),
}


def build_legal(slug: str) -> str:
    title, description = LEGAL_PAGES[slug]
    body = (ROOT / "pages" / f"{slug}.html").read_text(encoding="utf-8")
    return page(f"{title} — {SITE_NAME}", description, body)


def build_sitemap(episodes: list[dict]) -> str:
    """Every page, so the episodes are discoverable without crawling the index."""
    today = date.today().isoformat()
    entries = [(path, today) for path in ("", "episodes.html", "method.html", "about.html")]
    entries += [(f"episodes/{ep['slug']}.html", ep["published"]) for ep in episodes]
    entries += [(f"{slug}.html", "2026-09-03") for slug in LEGAL_PAGES]

    urls = "\n".join(
        f"  <url><loc>{BASE_URL}{path}</loc><lastmod>{when}</lastmod></url>"
        for path, when in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )


def main() -> None:
    episodes = json.loads((ROOT / "episodes.json").read_text(encoding="utf-8"))
    notes = {path.stem: parse_notes(path) for path in sorted(NOTES.glob("*.md"))}

    missing = [ep["slug"] for ep in episodes if ep["slug"] not in notes]
    if missing:
        raise SystemExit(f"episodes with no notes file: {', '.join(missing)}")

    # The summary is the lede on the episode page and the blurb on every index.
    # Without it the page ships an empty quote block, which is exactly the kind
    # of hole that goes unnoticed until someone else finds it.
    unsummarised = [slug for slug, (_, summary, _) in notes.items() if not summary]
    if unsummarised:
        raise SystemExit(
            "notes with no 'Accurate summary:' paragraph: " + ", ".join(sorted(unsummarised))
        )

    EPISODES_DIR.mkdir(exist_ok=True)
    written = 0
    for ep in episodes:
        target = EPISODES_DIR / f"{ep['slug']}.html"
        target.write_text(build_episode(ep, notes), encoding="utf-8")
        written += 1

    (ROOT / "index.html").write_text(build_home(episodes, notes), encoding="utf-8")
    (ROOT / "episodes.html").write_text(build_episode_index(episodes, notes), encoding="utf-8")
    (ROOT / "method.html").write_text(build_method(episodes), encoding="utf-8")
    (ROOT / "about.html").write_text(build_about(episodes), encoding="utf-8")
    for slug in LEGAL_PAGES:
        (ROOT / f"{slug}.html").write_text(build_legal(slug), encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(build_sitemap(episodes), encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n", encoding="utf-8"
    )

    top = 4 + len(LEGAL_PAGES)
    print(f"built {written} episode pages + {top} top-level pages, sitemap and robots.txt")


if __name__ == "__main__":
    main()
