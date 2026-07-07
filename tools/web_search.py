import time
from ddgs import DDGS  # <-- NEW: Importing from the updated library!

def search_the_web(query: str) -> str:
    """Searches the internet for the absolute latest, real-time data."""
    print(f"\n[🌐 J.A.R.V.I.S. is searching the web for: {query}...]")
    
    try:
        # 🔥 THE FIX: The new library doesn't need 'with' loops. It just grabs the data instantly!
        results = DDGS().text(query, max_results=5)
            
        if not results:
            return "Error: Could not find any recent information on the web."
            
        # Compile a massive, structured "data packet" for Gemini's brain
        compiled_data = f"CURRENT LIVE SEARCH RESULTS FOR: '{query}'\n"
        compiled_data += f"Search Date: {time.strftime('%B %d, %Y')}\n\n"
        
        for i, res in enumerate(results):
            compiled_data += f"--- Source {i+1} ---\n"
            compiled_data += f"Title: {res.get('title', 'No Title')}\n"
            compiled_data += f"Snippet: {res.get('body', 'No data available.')}\n"
            compiled_data += f"Link: {res.get('href', 'No link')}\n\n"
            
        # 🔥 THE ULTIMATE OVERRIDE
        compiled_data += "SYSTEM INSTRUCTION: Read the live snippets above. Answer the user's question accurately based ONLY on this new data. Do not use your older internal memory."
        
        return compiled_data
        
    except Exception as e:
        return f"Web search failed due to connection error: {str(e)}"