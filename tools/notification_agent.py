import asyncio
import os
import sys
import time

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

try:
    import winsdk.windows.ui.notifications.management as listener_mgr
    import winsdk.windows.ui.notifications as notifications
except Exception:
    pass

async def _get_notifications_async():
    try:
        listener = listener_mgr.UserNotificationListener.current
        access_status = await listener.request_access_async()
        if access_status != listener_mgr.UserNotificationListenerAccessStatus.ALLOWED:
            return []
        
        toast_notifs = await listener.get_notifications_async(notifications.NotificationKinds.TOAST)
        result = []
        for n in toast_notifs:
            try:
                app = n.app_info.display_info.display_name
                binding = n.notification.visual.get_binding(notifications.KnownNotificationBindings.toast_generic)
                text_str = ""
                if binding:
                    elements = binding.get_text_elements()
                    texts = [e.text for e in elements if e.text]
                    text_str = " | ".join(texts)
                result.append({"app": app, "text": text_str})
            except Exception:
                pass
        return result
    except Exception:
        return []

def get_active_app_notifications_native() -> list[dict]:
    """
    Natively queries Windows Toast Notification service via winsdk.
    Returns a list of dictionaries with 'app' and 'text'.
    """
    try:
        # Create a new event loop for background query
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_get_notifications_async())
    except Exception as e:
        print(f"[Winsdk Notification Error]: {e}")
        # Return fallback using powershell if native fails
        from tools.notification_reader import get_windows_notifications_ps
        return get_windows_notifications_ps()

def reply_to_active_notification(app_name: str, reply_text: str) -> str:
    """
    Sends a reply to an active chat notification (like WhatsApp, Discord, or Mail)
    by focusing its application window and submitting the message autonomously.
    """
    print(f"\n[📬 Notification Hub]: Dispatching reply to '{app_name}'...")
    import win32gui
    import win32con
    
    # Check if app is Mail (Email)
    if any(k in app_name.lower() for k in ["mail", "outlook", "email", "gmail"]):
        from tools.email_tool import reply_to_email
        return reply_to_email(reply_text)

    # Else, simulate key press reply for desktop apps (WhatsApp, Discord, etc.)
    target_hwnds = []
    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            if app_name.lower() in title:
                target_hwnds.append(hwnd)
                
    win32gui.EnumWindows(enum_windows_callback, None)
    
    if not target_hwnds:
        return f"Could not find any open window for application: '{app_name}' to send a reply."
        
    hwnd = target_hwnds[0]
    
    try:
        import ctypes
        user32 = ctypes.windll.user32
        
        # Restore and focus window
        user32.ShowWindow(hwnd, win32con.SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.5)
        
        # Use system media clipboard setter
        from tools.system_media import set_clipboard_content
        set_clipboard_content(reply_text)
        time.sleep(0.1)
        
        # Press Ctrl+V then Enter
        vk_control = 0x11
        vk_v = 0x56
        vk_return = 0x0D
        
        # Helper to press combination
        def _press(keys):
            for k in keys:
                user32.keybd_event(k, 0, 0, 0)
            for k in reversed(keys):
                user32.keybd_event(k, 0, 2, 0)
                
        _press([vk_control, vk_v])
        time.sleep(0.2)
        _press([vk_return])
        
        return f"Dispatched voice reply to {app_name}: '{reply_text}'"
    except Exception as e:
        return f"Failed to send reply to '{app_name}'. Error: {str(e)}"

if __name__ == "__main__":
    print(get_active_app_notifications_native())
