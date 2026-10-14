from backend.app.pulse import build_pulse, parse_feed, canonical, FEEDS
import pytest

def feed(items):
    return ('<rss version="2.0"><channel>'+''.join('<item><title>'+title+'</title><link>'+url+'</link><description>'+desc+'</description></item>' for title,url,desc in items)+'</channel></rss>').encode()
A=("Berlin AI startup raises seed", "https://example.org/a?utm_source=whatever", "European AI investment")
B=("Battery startup launches energy product","https://example.org/b","Energy storage product")
C=("Biotech publishes research","https://example.org/c","Clinical medtech research")

def test_parser_citations_and_trackers():
    a=parse_feed(feed([A]),"EU-Startups")
    assert len(a)==1 and a[0]["url"]=="https://example.org/a"
    assert "AI & Agents" in a[0]["topics"] and a[0]["claim_status"]=="reported_by_source"

def test_bootstrap_does_not_claim_new():
    _,r=build_pulse(None,{"EU-Startups":feed([A,B,C])})
    assert r["first_run"] and r["change_count"]==0 and len(r["items"])==3
    assert all(i["change_type"]=="baseline_article" for i in r["items"])

def test_second_run_no_change():
    state,_=build_pulse(None,{"EU-Startups":feed([A])})
    _,r=build_pulse(state,{"EU-Startups":feed([A])})
    assert r["items"]==[] and r["change_count"]==0

def test_new_and_updated():
    state,_=build_pulse(None,{"EU-Startups":feed([A])})
    state,r=build_pulse(state,{"EU-Startups":feed([A,B])})
    assert r["change_count"]==1 and r["items"][0]["change_type"]=="new_article"
    changed=(A[0].replace("seed","series A"),A[1],A[2])
    _,r=build_pulse(state,{"EU-Startups":feed([changed,B])})
    assert r["change_count"]==1 and r["items"][0]["change_type"]=="updated_article"

def test_new_feed_after_outage_is_baselined():
    state,_=build_pulse(None,{"EU-Startups":feed([A])})
    _,r=build_pulse(state,{"EU-Startups":feed([A]),"HTGF News":feed([C])})
    assert r["change_count"]==0

def test_no_feeds_fails_closed():
    state,_=build_pulse(None,{"EU-Startups":feed([A])})
    with pytest.raises(RuntimeError): build_pulse(state,{})

def test_max_three():
    state,_=build_pulse(None,{"EU-Startups":feed([A])})
    batch=[(f"AI startup raises seed {i}",f"https://example.org/startup/{i}","new funding") for i in range(8)]
    _,r=build_pulse(state,{"EU-Startups":feed(batch)})
    assert len(r["items"])==3 and r["change_count"]==8 and not r["autonomous_external_actions"]

def test_unsafe_urls_and_xml_limit():
    assert canonical("javascript:alert(1)") is None
    with pytest.raises(ValueError):parse_feed(b"x"*1_500_001,"EU-Startups")

def test_atom():
    xml=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>AI funding</title><link href="https://example.org/atom" rel="alternate"/><summary>Seed</summary></entry></feed>'
    assert parse_feed(xml,"EU-Startups")[0]["url"]=="https://example.org/atom"
