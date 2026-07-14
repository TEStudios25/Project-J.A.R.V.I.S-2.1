import webbrowser
import urllib.parse

def open_website(site_name: str) -> str:
    """Opens common websites, custom domain extensions (.in, .org), or direct URLs in browser."""
    site_name_clean = site_name.strip()
    site_name_lower = site_name_clean.lower()
    print(f"\n[🌐 J.A.R.V.I.S. is launching {site_name_clean} in the browser...]")
    
    # 1. Direct URLs
    if site_name_lower.startswith("http://") or site_name_lower.startswith("https://"):
        url = site_name_clean
    # 2. Domains with extensions (like amazon.in, google.com)
    elif "." in site_name_lower:
        if site_name_lower.startswith("www."):
            url = f"https://{site_name_clean}"
        else:
            url = f"https://www.{site_name_clean}"
    # 3. Raw names (like instagram, youtube)
    else:
        domains = {
            "instagram": "https://www.instagram.com",
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "github": "https://www.github.com",
            "chatgpt": "https://chat.openai.com",
            "whatsapp": "https://web.whatsapp.com",
            "reddit": "https://www.reddit.com"
        }
        url = domains.get(site_name_lower, f"https://www.{site_name_lower}.com")
    
    try:
        webbrowser.open(url)
        return f"Successfully opened {url} on your screen."
    except Exception as e:
        return f"Failed to open the website. Error: {str(e)}"

def search_youtube(query: str) -> str:
    """Opens YouTube and automatically searches for the given query."""
    print(f"\n[▶️ J.A.R.V.I.S. is searching YouTube for: '{query}'...]")
    
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        webbrowser.open(url)
        return f"Successfully opened YouTube and searched for '{query}'."
    except Exception as e:
        return f"Failed to search YouTube. Error: {str(e)}"

def play_song_on_youtube(song_name: str) -> str:
    """Uses pywhatkit to open YouTube and instantly start playing the top video result."""
    print(f"\n[🎵 J.A.R.V.I.S. is buffering audio sequence: '{song_name}'...]")
    
    try:
        import pywhatkit
        pywhatkit.playonyt(song_name)
        return f"Successfully commanded the browser to play '{song_name}' on YouTube."
    except ImportError:
        return "Pywhatkit library is missing. Please run 'pip install pywhatkit'."
    except Exception as e:
        return f"Failed to play the song. Error: {str(e)}"