import urllib.request
import re

def get_tech_news_briefing() -> str:
    """Fetches key India, World, and Science headlines from Google News RSS feeds."""
    print("\n[📰 J.A.R.V.I.S. is compiling news digest...]")
    headlines = []
    
    # 1. Fetch Top 2 India Headlines
    try:
        india_url = "https://news.google.com/rss/search?q=India&hl=en-IN&gl=IN&ceid=IN:en"
        req = urllib.request.Request(india_url, headers={"User-Agent": "Project-JARVIS/2.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            xml = response.read().decode("utf-8")
        titles = re.findall(r"<title>(.*?)</title>", xml)
        # Grab top 2 headlines
        for t in titles[1:3]:
            title = t.split(" - ")[0].strip()
            title = title.replace("&amp;", "&").replace("&#x27;", "'").replace("&quot;", '"')
            headlines.append(f"India: {title}")
    except Exception:
        pass

    # 2. Fetch Top 2 World Headlines
    try:
        world_url = "https://news.google.com/rss/search?q=world&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(world_url, headers={"User-Agent": "Project-JARVIS/2.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            xml = response.read().decode("utf-8")
        titles = re.findall(r"<title>(.*?)</title>", xml)
        for t in titles[1:3]:
            title = t.split(" - ")[0].strip()
            title = title.replace("&amp;", "&").replace("&#x27;", "'").replace("&quot;", '"')
            headlines.append(f"World: {title}")
    except Exception:
        pass

    # 3. Fetch Top 1 Science Headline
    try:
        science_url = "https://news.google.com/rss/search?q=science&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(science_url, headers={"User-Agent": "Project-JARVIS/2.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            xml = response.read().decode("utf-8")
        titles = re.findall(r"<title>(.*?)</title>", xml)
        if len(titles) > 1:
            title = titles[1].split(" - ")[0].strip()
            title = title.replace("&amp;", "&").replace("&#x27;", "'").replace("&quot;", '"')
            headlines.append(f"Science: {title}")
    except Exception:
        pass

    if not headlines:
        return "No major headlines retrieved."
        
    return " // ".join(headlines)
