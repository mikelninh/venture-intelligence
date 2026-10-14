"""Venture Pulse 0.6: transparent public RSS change detector.

This is scheduled deterministic change detection, NOT autonomous LLM research.
A source citation proves what was published, not the business claim.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

FEEDS = {
    "HTGF News": "https://www.htgf.de/en/feed/",
    "EU-Startups": "https://www.eu-startups.com/feed/",
}
WATCHLIST = {
    "AI & Agents": ("artificial intelligence", "ai", "agent", "llm", "robotics", "automation"),
    "Climate & Energy": ("climate", "energy", "fusion", "battery", "solar", "carbon"),
    "Life Sciences": ("medtech", "medical", "biotech", "health", "drug", "clinical", "diagnostic"),
    "Early-stage funding": ("seed", "pre-seed", "funding", "raises", "investment", "venture"),
}
EVENTS = {
    "funding": ("raises", "funding", "investment", "financing", "secures", "seed round"),
    "research": ("research", "publication", "study", "clinical trial", "patent"),
    "product": ("launches", "launch", "release", "new product", "introduces"),
    "partnership": ("partnership", "partners", "collaboration", "acquisition"),
}
ACTIONS = {
    "funding": "Check the primary funding announcement: amount, investors and stage.",
    "research": "Read the original research or trial record before assessing relevance.",
    "product": "Check what materially changed for users in the company's own announcement.",
    "partnership": "Confirm the announcement with both parties and examine its scope.",
    "other": "Open the original source and decide whether further investigation is useful.",
}
MAX_BYTES = 1_500_000

def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

def child(el, key):
    for c in el:
        if c.tag.rsplit("}", 1)[-1] == key:
            return "".join(c.itertext()).strip()
    return ""

def canonical(s):
    try:
        p = urllib.parse.urlsplit(s.strip())
        if p.scheme not in ("https", "http") or not p.hostname or p.username or p.password:
            return None
        if p.hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return None
        query = [(k, v) for k, v in urllib.parse.parse_qsl(p.query)
                 if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
        return urllib.parse.urlunsplit((p.scheme, p.netloc.lower(), p.path or "/",
                                        urllib.parse.urlencode(query), ""))
    except ValueError:
        return None

def published(s):
    if not s:
        return None
    try:
        date = parsedate_to_datetime(s)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return date.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, IndexError, OverflowError):
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            return None

def parse_feed(payload, source):
    if len(payload) > MAX_BYTES:
        raise ValueError("Feed exceeds allowed size")
    tree = ET.fromstring(payload)
    output = []
    for node in tree.iter():
        if node.tag.rsplit("}", 1)[-1] not in ("item", "entry"):
            continue
        title = clean(child(node, "title"))[:250]
        link = child(node, "link")
        if not link:
            for e in node:
                if e.tag.rsplit("}", 1)[-1] == "link" and e.attrib.get("href"):
                    link = e.attrib["href"]
                    if e.attrib.get("rel", "alternate") == "alternate":
                        break
        url = canonical(link)
        if not title or not url:
            continue
        summary = clean(child(node, "description") or child(node, "summary") or child(node, "content"))[:400]
        stamp = published(child(node, "pubDate") or child(node, "published") or child(node, "updated"))
        text = (title + " " + summary).lower()
        topics = [k for k, vals in WATCHLIST.items() if any(re.search(r"(?<![a-z])" + re.escape(v), text) for v in vals)]
        event = next((k for k, vals in EVENTS.items() if any(re.search(r"(?<![a-z])" + re.escape(v), text) for v in vals)), "other")
        output.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:20],
            "fingerprint": hashlib.sha256((title + "\n" + summary).lower().encode()).hexdigest()[:20],
            "source": source, "title": title, "url": url,
            "summary": summary, "published_at": stamp,
            "topics": topics, "event": event, "priority": (6 if source == "HTGF News" else 0) + len(topics)*2 + (2 if event != "other" else 0),
            "next_action": ACTIONS[event], "claim_status": "reported_by_source",
        })
        if len(output) >= 70:
            break
    return output

def download_feed(url):
    if url not in FEEDS.values():
        raise ValueError("Feed not on allowlist")
    req = urllib.request.Request(url, headers={
        "User-Agent": "VenturePulse/0.6 (public-source research)",
        "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml",
    })
    with urllib.request.urlopen(req, timeout=14) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Feed too large")
    return data

def build_pulse(previous, feeds, now=None):
    now = now or datetime.now(timezone.utc).isoformat(timespec="seconds")
    old = previous or {}
    seen = dict(old.get("seen", {}))
    sources = dict(old.get("sources", {}))
    bootstrap = not old.get("initialized", False)
    success = 0
    errors, changes, articles = [], [], []
    for source, url in FEEDS.items():
        if source not in feeds:
            errors.append(source + ": fetch failed")
            continue
        try:
            items = parse_feed(feeds[source], source)
            if not items:
                raise ValueError("No valid linked articles")
        except (ValueError, ET.ParseError) as ex:
            errors.append(source + ": " + type(ex).__name__)
            continue
        source_first_seen = source not in old.get("sources", {})
        success += 1
        sources[source] = {"fetched_at": now, "feed_url": url, "count": len(items), "status": "ok"}
        articles.extend(items)
        for article in items:
            earlier = seen.get(article["id"])
            change = ("new_article" if earlier is None else
                      "updated_article" if earlier["fingerprint"] != article["fingerprint"] else None)
            if change and not bootstrap and not source_first_seen and article["priority"] >= 2:
                changes.append({**article, "change_type": change})
            seen[article["id"]] = {"fingerprint": article["fingerprint"], "source": source,
                                   "title": article["title"], "observed_at": now}
    if success == 0:
        raise RuntimeError("No source responded with a valid feed; previous snapshot preserved")
    # Bounded history, newest observations first.
    if len(seen) > 1000:
        seen = dict(sorted(seen.items(), key=lambda kv: kv[1]["observed_at"], reverse=True)[:1000])
    changes.sort(key=lambda x: (x["priority"], x["published_at"] or "", x["id"]), reverse=True)
    baseline = sorted(articles, key=lambda x: (x["priority"], x["published_at"] or ""), reverse=True)[:3]
    top = [{**x, "change_type": "baseline_article"} for x in baseline] if bootstrap else changes[:3]
    report = {
        "schema_version": 1, "generated_at": now, "status": "partial" if errors else "ok",
        "first_run": bootstrap, "feed_count": success, "change_count": 0 if bootstrap else len(changes),
        "items": top, "warnings": errors,
        "source_note": "Articles report publisher claims, not independently verified business facts. Changes in a feed are not confirmed events.",
        "next_best_action": top[0]["next_action"] if top else "No new relevant articles. Nothing urgent to do.",
        "autonomous_external_actions": False,
    }
    state = {"schema_version": 1, "initialized": True, "updated_at": now,
             "seen": seen, "sources": sources}
    return state, report

def refresh(state_path, output_path, downloader=download_feed):
    prior = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else None
    feeds = {}
    for name, url in FEEDS.items():
        try:
            feeds[name] = downloader(url)
        except (OSError, ValueError, TimeoutError) as ex:
            print("[pulse] " + name + ": " + type(ex).__name__)
    state, report = build_pulse(prior, feeds)
    for target, value in ((state_path, state), (output_path, report)):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", type=Path, default=Path("data/pulse/state.json"))
    ap.add_argument("--output", type=Path, default=Path("data/pulse/latest.json"))
    args = ap.parse_args()
    result = refresh(args.state, args.output)
    print(json.dumps({"status": result["status"], "change_count": result["change_count"],
                      "first_run": result["first_run"], "items": len(result["items"])}))
