import os
import google.generativeai as genai
from PIL import ImageGrab, Image

def analyze_current_screen() -> str:
    """
    Takes a screenshot of the user's primary monitor, runs Gemini Multimodal analysis
    on the capture, acting like Google Lens, and returns a detailed intelligence explanation.
    """
    print("\n[📸 J.A.R.V.I.S. is capturing screen telemetry...]")
    try:
        # Capture screenshot
        screenshot = ImageGrab.grab()
        
        # Save to temp directory
        temp_dir = os.environ.get("TEMP", "C:\\Temp")
        os.makedirs(temp_dir, exist_ok=True)
        img_path = os.path.join(temp_dir, "jarvis_screen_capture.png")
        screenshot.save(img_path)
        
        # Load image
        img = Image.open(img_path)
        
        # Call Gemini 1.5 Flash (multimodal) to analyze the image
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "You are J.A.R.V.I.S., acting as a Google Lens agent. Analyze this screenshot of the user's monitor. "
            "Explain exactly what is on the screen. If you see code, explain the code and check for bugs/errors. "
            "If you see error messages, explain the solution. Describe active windows, text, images, or elements you see. "
            "Keep the report highly technical, informative, and structured."
        )
        response = model.generate_content([img, prompt])
        
        # Cleanup temporary image file
        try:
            os.remove(img_path)
        except Exception:
            pass
            
        return response.text
        
    except Exception as e:
        return f"Failed to capture and analyze screen. Error: {str(e)}"

def analyze_image_file(image_path: str) -> str:
    """
    Analyzes an existing image file on disk at the given absolute path.
    Uses Gemini Multimodal analysis (Google Lens-style) to explain, describe, or debug.
    """
    print(f"\n[👁️ J.A.R.V.I.S. is checking file registry: '{image_path}'...]")
    try:
        if not os.path.exists(image_path):
            return f"Error: Image file not found at {image_path}."
            
        img = Image.open(image_path)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "You are J.A.R.V.I.S., acting as a Google Lens agent. Analyze this image. "
            "Explain exactly what is in the image. Describe objects, colors, text, landscapes, code, or any visual content in detail. "
            "Keep the report highly informative and structured."
        )
        response = model.generate_content([img, prompt])
        return response.text
    except Exception as e:
        return f"Failed to analyze image file. Error: {str(e)}"

def extract_text_from_image(image_path: str = "") -> str:
    """
    Performs OCR (Optical Character Recognition) on an image file or the current screen.
    If image_path is empty, takes a screenshot of the current active screen and extracts the text.
    If image_path is provided, extracts text from that specific file.
    """
    print("\n[🔍 J.A.R.V.I.S. is executing OCR text extraction...]")
    try:
        # If no image path, capture screen
        if not image_path:
            screenshot = ImageGrab.grab()
            temp_dir = os.environ.get("TEMP", "C:\\Temp")
            os.makedirs(temp_dir, exist_ok=True)
            img_path = os.path.join(temp_dir, "jarvis_ocr_capture.png")
            screenshot.save(img_path)
            img = Image.open(img_path)
        else:
            img_path = _resolve_path(image_path)
            if not os.path.exists(img_path):
                return f"Error: Image file not found at {img_path}."
            img = Image.open(img_path)

        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "You are J.A.R.V.I.S., an advanced OCR engine. Extract all text, characters, codes, "
            "or words from this image. Keep the layout format clean, and do NOT add any conversational "
            "explanations, warnings, or metadata. Just output the extracted text verbatim."
        )
        response = model.generate_content([img, prompt])
        
        # Cleanup temporary image file
        if not image_path:
            try:
                os.remove(img_path)
            except Exception:
                pass
                
        return response.text if response.text else "No text could be extracted from the image."
    except Exception as e:
        return f"Failed to execute OCR on image. Error: {str(e)}"

# Helper function to resolve paths
def _resolve_path(filename: str) -> str:
    if os.path.isabs(filename):
        return filename
    user_profile = os.environ.get('USERPROFILE', 'C:\\')
    desktop_path = os.path.join(user_profile, 'Desktop', filename)
    if os.path.exists(desktop_path):
        return desktop_path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(project_root, filename)

