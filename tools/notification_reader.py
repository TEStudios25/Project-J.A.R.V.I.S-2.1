import os
import sys
import subprocess
import json
import re

if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

def get_windows_notifications_ps() -> list[dict]:
    """
    Attempts to fetch active Windows Toast Notifications using PowerShell WinRT API.
    """
    ps_script = """
    [Windows.UI.Notifications.Management.UserNotificationListener, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
    [Windows.UI.Notifications.KnownNotificationBindings, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
    try {
        $listener = [Windows.UI.Notifications.Management.UserNotificationListener]::Current
        $status = $listener.RequestAccessAsync().GetAwaiter().GetResult()
        if ($status -eq "Allowed") {
            $notifs = $listener.GetNotificationsAsync([Windows.UI.Notifications.NotificationKinds]::Toast).GetAwaiter().GetResult()
            $result = @()
            foreach ($n in $notifs) {
                $app = $n.AppInfo.DisplayInfo.DisplayName
                $binding = $n.Notification.Visual.GetBinding([Windows.UI.Notifications.KnownNotificationBindings]::ToastGeneric)
                if ($binding) {
                    $elements = $binding.GetTextElements()
                    $textList = @()
                    foreach ($e in $elements) { $textList += $e.Text }
                    $textStr = $textList -join " | "
                    $result += @{ app = $app; text = $textStr }
                }
            }
            $result | ConvertTo-Json -Compress
        } else {
            Write-Output "ACCESS_DENIED"
        }
    } catch {
        Write-Output "ERROR"
    }
    """
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=8
        )
        output = proc.stdout.strip()
        if output and not output.startswith("ACCESS_DENIED") and not output.startswith("ERROR"):
            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]
            return data
    except Exception:
        pass
    return []

def get_active_app_notifications() -> str:
    """
    Reads active desktop notifications (WhatsApp Web, Discord, Mail, System alerts)
    and summarizes them in natural conversational format.
    """
    print("\n[📬 J.A.R.V.I.S. is reading system notifications...]")
    
    # 1. Try WinRT Notification Listener
    notifs = get_windows_notifications_ps()
    if notifs:
        lines = []
        for n in notifs[:5]:
            app = n.get("app", "Application")
            text = n.get("text", "New alert")
            lines.append(f"• {app}: {text}")
        return f"You have {len(notifs)} active notifications, Mr. Pranav:\n" + "\n".join(lines)

    # 2. Fallback: Window & Badge inspection via pygetwindow / win32gui
    app_alerts = []
    try:
        import win32gui
        def enum_windows_callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    # Check for unread message indicators in title (e.g. "(3) WhatsApp", "(1) Discord")
                    match = re.search(r'\(([\d]+)\)\s*(WhatsApp|Discord|Instagram|Gmail|Mail|Telegram|Slack|Chrome)', title, re.IGNORECASE)
                    if match:
                        count = match.group(1)
                        app = match.group(2)
                        app_alerts.append(f"{count} unread message(s) on {app}")
                    elif any(k in title.lower() for k in ["whatsapp", "discord", "outlook", "telegram"]) and ("new message" in title.lower() or "notification" in title.lower()):
                        app_alerts.append(f"Active notification on {title}")
        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception:
        pass

    if app_alerts:
        return "Here are your active app notifications:\n" + "\n".join(f"- {a}" for a in app_alerts)

    return "Your notification tray is currently clean, Mr. Pranav. No unread alerts detected."

if __name__ == "__main__":
    print(get_active_app_notifications())
