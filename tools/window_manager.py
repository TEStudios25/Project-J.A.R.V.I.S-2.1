import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

def get_active_window_title() -> str:
    """
    Retrieves the title of the currently focused window on the desktop.
    Allows J.A.R.V.I.S. to know what application you are working on.
    """
    print("\n[🎯 J.A.R.V.I.S. is querying foreground focus window...]")
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "No active window detected."
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return "Untitled window active."
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        return f"The active window is currently: '{title}'."
    except Exception as e:
        return f"Failed to get active window. Error: {str(e)}"

def _press_keys(keys: list[int]):
    # Presses multiple keys in combination and releases them in reverse order
    for key in keys:
        user32.keybd_event(key, 0, 0, 0)
    for key in reversed(keys):
        user32.keybd_event(key, 0, 2, 0)

def execute_system_hotkey(command: str) -> str:
    """
    Simulates Windows hotkey shortcuts.
    command: 'close_window' (Alt+F4), 'copy_all' (Ctrl+A then Ctrl+C),
             'search' (Ctrl+F), 'switch_app' (Alt+Tab), 'lock_pc' (Win+L)
    """
    command = command.lower().strip()
    print(f"\n[⌨️ J.A.R.V.I.S. is executing hotkey macro: '{command}'...]")

    vk_control = 0x11
    vk_menu = 0x12  # Alt key
    vk_lwin = 0x5B  # Left Windows key
    vk_a = 0x41
    vk_c = 0x43
    vk_f = 0x46
    vk_f4 = 0x73
    vk_tab = 0x09
    vk_l = 0x4C

    try:
        if command == "close_window":
            _press_keys([vk_menu, vk_f4])
            return "Executed Alt+F4 to close the active window."
        elif command == "copy_all":
            # Press Ctrl+A
            _press_keys([vk_control, vk_a])
            time.sleep(0.15)
            # Press Ctrl+C
            _press_keys([vk_control, vk_c])
            return "Executed Ctrl+A and Ctrl+C to copy all active screen elements."
        elif command == "search":
            _press_keys([vk_control, vk_f])
            return "Executed Ctrl+F search shortcut."
        elif command == "switch_app":
            _press_keys([vk_menu, vk_tab])
            return "Executed Alt+Tab switcher shortcut."
        elif command == "switch_tab":
            _press_keys([vk_control, vk_tab])
            return "Executed Ctrl+Tab tab switcher shortcut."
        elif command == "lock_pc":
            ctypes.windll.user32.LockWorkStation()
            return "Executed Lock Workstation protocol."
        else:
            return f"Unknown hotkey macro command: '{command}'. Choose from 'close_window', 'copy_all', 'search', 'switch_app', 'switch_tab', 'lock_pc'."
    except Exception as e:
        return f"Failed to execute hotkey command. Error: {str(e)}"

def focus_and_control_window(app_name: str, action: str) -> str:
    """
    Finds a running desktop window/application whose title matches the app_name, 
    and performs the requested window control action.
    
    app_name: The name or part of the title of the app (e.g. 'chrome', 'VS Code', 'spotify', 'whatsapp').
    action: 'minimize', 'maximize', 'restore', 'focus' (or 'switch_to').
    """
    app_name = app_name.lower().strip()
    action = action.lower().strip()
    print(f"\n[🖥️ J.A.R.V.I.S. is targeting window '{app_name}' with action '{action}'...]")
    
    # 1. Setup user32 functions
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    GetWindowTextW = user32.GetWindowTextW
    GetWindowTextLengthW = user32.GetWindowTextLengthW
    IsWindowVisible = user32.IsWindowVisible
    
    matching_hwnds = []
    
    # 2. Enumeration callback function
    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                if app_name in title:
                    matching_hwnds.append((hwnd, buf.value))
        return True
        
    # 3. Trigger enumeration
    EnumWindows(EnumWindowsProc(foreach_window), 0)
    
    if not matching_hwnds:
        return f"Could not locate any open application matching '{app_name}'."
        
    # Select the first matching window
    hwnd, full_title = matching_hwnds[0]
    
    SW_MINIMIZE = 6
    SW_MAXIMIZE = 3
    SW_RESTORE = 9
    
    try:
        if action == "minimize":
            user32.ShowWindow(hwnd, SW_MINIMIZE)
            return f"Successfully minimized the window '{full_title}'."
        elif action == "maximize":
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
            return f"Successfully maximized the window '{full_title}'."
        elif action == "restore":
            user32.ShowWindow(hwnd, SW_RESTORE)
            return f"Successfully restored the window size of '{full_title}'."
        elif action in ["focus", "switch_to"]:
            # Restore if minimized
            user32.ShowWindow(hwnd, SW_RESTORE)
            # Try to force foreground focus
            user32.SetForegroundWindow(hwnd)
            return f"Successfully switched focus to window '{full_title}'."
        else:
            return f"Unknown window control action '{action}'. Choose from 'minimize', 'maximize', 'restore', 'focus'."
    except Exception as e:
        return f"Failed to execute action '{action}' on window '{full_title}'. Error: {str(e)}"

def scan_social_notifications() -> str:
    """
    Scans active running window titles to check for unread message counts or notification counts
    on open instances of WhatsApp Web, WhatsApp Desktop, or Instagram.
    Returns a status report summarizing unread counts.
    """
    import re
    import ctypes
    
    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    GetWindowTextW = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLengthW = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    
    notifications = []
    
    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                
                # Check for WhatsApp or Instagram in title
                is_whatsapp = "whatsapp" in title
                is_instagram = "instagram" in title
                
                if is_whatsapp or is_instagram:
                    # Look for parenthesized numbers, e.g. "(3) WhatsApp" or "(1) Instagram"
                    match = re.search(r'\((\d+)\)', title)
                    if match:
                        count = match.group(1)
                        app_name = "WhatsApp" if is_whatsapp else "Instagram"
                        notifications.append(f"{app_name}: {count} unread notifications/messages.")
        return True
        
    EnumWindows(EnumWindowsProc(foreach_window), 0)
    
    if not notifications:
        return "No unread notifications detected on WhatsApp or Instagram at this time."
    return "Social notification alert:\n- " + "\n- ".join(notifications)


