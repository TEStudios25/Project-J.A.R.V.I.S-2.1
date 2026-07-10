import os
import urllib.parse
import urllib.request

def generate_image(prompt: str) -> str:
    """
    Generates an image based on a text prompt using the state-of-the-art FLUX model.
    Saves the newly created image directly to the user's Desktop.
    Provides 100% free, unlimited generations with zero API key dependencies.
    """
    print(f"\n[🎨 J.A.R.V.I.S. is generating a photorealistic image for: '{prompt}'...]")
    
    try:
        # Encode the prompt for URL compatibility
        prompt_encoded = urllib.parse.quote(prompt.strip())
        
        # We use the state-of-the-art FLUX model for hyper-realistic renders
        url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&nologo=true&private=true&model=flux"
        
        # Request the image bytes with a standard browser User-Agent
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            image_data = response.read()
            
        # Determine save location (User's Desktop)
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        desktop_path = os.path.join(user_profile, 'Desktop')
        
        # Clean up the prompt to create a safe, readable filename
        safe_filename = "".join([c for c in prompt[:25] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_filename = safe_filename.replace(" ", "_") + "_jarvis.jpg"
        
        file_path = os.path.join(desktop_path, safe_filename)
        
        # Write the image binary data directly to disk
        with open(file_path, "wb") as f:
            f.write(image_data)
            
        return f"Successfully generated a photorealistic image and saved it to your Desktop as '{safe_filename}'."
        
    except Exception as e:
        return f"Failed to generate the image. The rendering servers might be busy. Error: {str(e)}"

# ===============================================================
# 🧪 ISOLATED TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    print("\nInitiating Visual Creation Subsystem...")
    test_prompt = "A futuristic AI core glowing with blue energy, high resolution, cinematic lighting, photorealistic"
    response = generate_image(test_prompt)
    print(f"\nResult: {response}")