import webbrowser
import urllib.parse

def open_website(site_name: str) -> str:
    """Opens common websites directly in the user's default browser."""
    site_name = site_name.lower().replace(" ", "")
    print(f"\n[🌐 J.A.R.V.I.S. is launching {site_name} in the browser...]")
    
    domains = {
        "instagram": "https://www.instagram.com",
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://www.github.com",
        "chatgpt": "https://chat.openai.com",
        "whatsapp": "https://web.whatsapp.com",
        "reddit": "https://www.reddit.com"
    }
    
    url = domains.get(site_name, f"https://www.{site_name}.com")
    
    try:
        webbrowser.open(url)
        return f"Successfully opened {site_name} on your screen."
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