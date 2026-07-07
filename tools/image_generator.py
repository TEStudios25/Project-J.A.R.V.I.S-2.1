import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

def generate_image(prompt: str) -> str:
    """
    Generates an image based on a text prompt using the Hugging Face API.
    Saves the newly created image directly to the user's Desktop.
    """
    print(f"\n[🎨 J.A.R.V.I.S. is generating an image for: '{prompt}'...]")
    
    # Load the token from the .env file
    load_dotenv()
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    if not hf_token:
        return "Error: HUGGINGFACE_TOKEN is missing from the .env file."
        
    try:
        # We are using Stable Diffusion XL for high-quality, fast generation
        client = InferenceClient("stabilityai/stable-diffusion-xl-base-1.0", token=hf_token)
        
        # Call the API to create the image
        image = client.text_to_image(prompt)
        
        # Determine save location (User's Desktop)
        user_profile = os.environ.get('USERPROFILE', 'C:\\')
        desktop_path = os.path.join(user_profile, 'Desktop')
        
        # Clean up the prompt to create a safe, readable filename
        safe_filename = "".join([c for c in prompt[:20] if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        safe_filename = safe_filename.replace(" ", "_") + "_jarvis.png"
        
        file_path = os.path.join(desktop_path, safe_filename)
        
        # Save the image physically to the hard drive
        image.save(file_path)
        
        return f"Successfully generated the image and saved it to your Desktop as '{safe_filename}'."
        
    except Exception as e:
        return f"Failed to generate the image. The HuggingFace servers might be busy. Error: {str(e)}"

# ===============================================================
# 🧪 ISOLATED TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    print("\nInitiating Visual Creation Subsystem...")
    
    # Let's test it with a highly detailed prompt
    test_prompt = "A futuristic AI core glowing with blue energy, high resolution, cinematic lighting"
    
    response = generate_image(test_prompt)
    print(f"\nResult: {response}")