import asyncio
import time
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

async def track_playback():
    sessions = await MediaManager.request_async()
    print("Tracking playback status. Play and pause YouTube to observe values...")
    for _ in range(15):
        current_session = sessions.get_current_session()
        if current_session:
            info = current_session.get_playback_info()
            if info:
                print(f"[{time.strftime('%H:%M:%S')}] App: {current_session.source_app_user_model_id} | Status: {info.playback_status}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] No playback info.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] No active session.")
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(track_playback())
