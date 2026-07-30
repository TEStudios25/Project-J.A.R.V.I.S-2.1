import os
import time
import google.generativeai as genai

def analyze_local_video_file(file_path: str, prompt: str = "Describe this video in detail.") -> str:
    """
    Uploads a local video file (MP4, WebM, etc.) to Gemini and analyzes its contents to answer your query.
    Use this when the user points to a local video file path.
    """
    if not os.path.exists(file_path):
        return f"Error: Local video file not found at path: {file_path}"
    
    try:
        print(f"[📹 Video Analyzer]: Uploading local file: {file_path} to Gemini API...")
        video_file = genai.upload_file(path=file_path)
        
        print("[📹 Video Analyzer]: Waiting for Gemini video processing sequence...")
        while video_file.state.name == "PROCESSING":
            time.sleep(3)
            video_file = genai.get_file(video_file.name)
            
        if video_file.state.name == "FAILED":
            raise ValueError(f"Gemini video processing error: {video_file.error.message}")
            
        print("[📹 Video Analyzer]: Gemini processing completed. Analyzing video frames...")
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content([video_file, prompt])
        
        try:
            print("[📹 Video Analyzer]: Cleaning up Gemini API cloud storage...")
            genai.delete_file(video_file.name)
        except Exception:
            pass
            
        return response.text
    except Exception as e:
        return f"Error during video analysis: {str(e)}"

def download_and_analyze_video_url(url: str, prompt: str = "Describe this video in detail.") -> str:
    """
    Downloads a video from any URL (YouTube, Instagram Reel, TikTok, Twitter, Facebook, etc.)
    using yt-dlp, uploads it to Gemini, and analyzes it to answer queries or describe it.
    Use this when the user gives you a link to a video or Reel and asks what is going on.
    """
    import yt_dlp
    
    temp_dir = os.path.join("data", "temp_downloads")
    os.makedirs(temp_dir, exist_ok=True)
    
    out_tmpl = os.path.join(temp_dir, "video_%(id)s.%(ext)s")
    
    ydl_opts = {
        'outtmpl': out_tmpl,
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    
    print(f"[📹 Video Analyzer]: Initiating download for URL: {url}...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Fallback if filename format varies
            if not os.path.exists(file_path):
                video_id = info.get("id", "")
                if video_id:
                    files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if video_id in f]
                    if files:
                        file_path = files[0]
                        
        if not os.path.exists(file_path):
            return "Error: Could not locate the downloaded video file in local storage."
            
        print(f"[📹 Video Analyzer]: Video downloaded successfully to {file_path}")
        
        # Analyze using local video analyzer
        analysis = analyze_local_video_file(file_path, prompt)
        
        # Clean up local temporary file
        try:
            os.remove(file_path)
        except Exception:
            pass
            
        return analysis
        
    except Exception as e:
        return f"Error downloading or processing video link: {str(e)}. Instagram bot protection or private account restrictions might be active."
