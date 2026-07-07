import os
import cv2
import numpy as np
import pytesseract

class ImageAnalyzer:
    def __init__(self):
        # Set your exact hardcoded Tesseract path
        pytesseract.pytesseract.tesseract_cmd = r"D:\Tesseract\tesseract.exe"
        # Just a silent terminal print, NOT spoken out loud
        print("[🧠 Image Analyzer module initialized and ready.]")

    def analyze_image(self, image_path: str) -> str:
        """
        Analyzes a local image file for text, human faces/eyes, shapes, and hex colors.
        Returns a comprehensive intelligence report string to the AI Brain.
        """
        print(f"\n[👁️ J.A.R.V.I.S. is analyzing image at: '{image_path}'...]")
        
        try:
            if not image_path or not isinstance(image_path, str):
                return "[ERROR] Invalid file path matrix provided."

            if not os.path.exists(image_path):
                return f"[ERROR] Could not find any image file at '{image_path}'."

            image = cv2.imread(image_path)
            if image is None:
                return f"[ERROR] OpenCV could not read or decode image at '{image_path}'."

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # === 1. TEXT ANALYSIS (OCR) ===
            gray_ocr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            text = pytesseract.image_to_string(gray_ocr).strip()
            text_info = text if text else "[No readable text detected]"

            # === 2. OBJECT DETECTION ===
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            eyes = eye_cascade.detectMultiScale(gray, 1.3, 5)

            obj_info = []
            if len(faces) > 0:
                obj_info.append(f"{len(faces)} face(s)")
            if len(eyes) > 0:
                obj_info.append(f"{len(eyes)} eye(s)")
            if not obj_info:
                obj_info.append("No predefined objects (faces/eyes) detected")

            # === 3. SHAPE DETECTION ===
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            shape_stats = {}
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 300: 
                    peri = cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                    vertices = len(approx)
                    shape_name = "Unidentified"

                    if vertices == 3: shape_name = "Triangle"
                    elif vertices == 4:
                        x, y, w, h = cv2.boundingRect(approx)
                        ar = w / float(h)
                        shape_name = "Square" if 0.95 < ar < 1.05 else "Rectangle"
                    elif vertices == 5: shape_name = "Pentagon"
                    elif vertices == 6: shape_name = "Hexagon"
                    elif vertices > 6: shape_name = "Circle"

                    shape_stats[shape_name] = shape_stats.get(shape_name, 0) + 1

            shape_info = ", ".join([f"{v} {k}(s)" for k, v in shape_stats.items()]) if shape_stats else "No significant geometric shapes detected"

            # === 4. COLOR ANALYSIS ===
            avg_color = np.mean(image, axis=(0, 1)).astype(int)
            avg_hex = '#%02x%02x%02x' % tuple(avg_color[::-1])

            # === FINAL COMPILED TELEMETRY ===
            report = f"""
🧩 J.A.R.V.I.S. IMAGE ANALYSIS REPORT
────────────────────────────────────────
📍 Targeted Path: {image_path}

🧠 EXTRACTED TEXT MATRIX:
{text_info}

🎯 BIOMETRIC/OBJECT DETECTIONS:
{', '.join(obj_info)}

📐 GEOMETRIC SHAPES IDENTIFIED:
{shape_info}

🎨 LIGHTING & COLOR BALANCE:
Average RGB Core: {tuple(int(c) for c in avg_color)}
Hex Signature: {avg_hex}

✅ Optical Diagnostic Array Completed successfully.
"""
            # Silent terminal log, then returning ONLY text!
            print("[📊 Image Analysis Complete.]")
            return report.strip()

        except pytesseract.TesseractNotFoundError:
            return "[IMAGE ANALYSIS ERROR] The Tesseract binary engine was not found at D:\\Tesseract\\tesseract.exe. Please verify installation."
        except Exception as e:
            return f"[IMAGE ANALYSIS ERROR] System failure during execution: {str(e)}"

# ===============================================================
# 🧪 ISOLATED STANDALONE TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    print("\nInitiating Optical Core Telemetry diagnostics...")
    analyzer = ImageAnalyzer()
    
    test_card = "vision_diagnostic_card.png"
    img = np.zeros((200, 400, 3), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (200, 150), (0, 255, 0), -1)
    cv2.putText(img, "JARVIS 2.0", (220, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imwrite(test_card, img)
    
    analysis_results = analyzer.analyze_image(test_card)
    print(analysis_results)
    
    try: os.remove(test_card)
    except: pass