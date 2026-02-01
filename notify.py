# notify.py
"""
Standalone notification script for Flowly
Run this via Windows Task Scheduler for background notifications
"""
import sys
from pathlib import Path
import json
from datetime import date

# Check if notification already shown today
def check_already_shown():
    last_notif_file = Path("last_notification.txt")
    today = date.today().isoformat()
    
    if last_notif_file.exists():
        with open(last_notif_file, 'r') as f:
            last_date = f.read().strip()
            if last_date == today:
                return True  # Already showed today
    
    # Mark as shown today
    with open(last_notif_file, 'w') as f:
        f.write(today)
    
    return False

# Show Windows notification
def show_notification():
    try:
        # Try using win10toast (lightweight)
        from win10toast import ToastNotifier
        
        # Load custom message from settings
        settings_file = Path("settings.json")
        message = "Time to check your habits! 🎯"
        
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                message = settings.get("notification_message", message)
        
        toaster = ToastNotifier()
        toaster.show_toast(
            "Flowly Reminder",
            message,
            icon_path=None,  # Optional: add icon path
            duration=10,  # Show for 10 seconds
            threaded=False
        )
        
    except ImportError:
        # Fallback: Use Windows built-in notification
        import subprocess
        
        settings_file = Path("settings.json")
        message = "Time to check your habits!"
        
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                message = settings.get("notification_message", message)
        
        # PowerShell command for Windows notification
        ps_script = f'''
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

        $template = @"
        <toast>
            <visual>
                <binding template="ToastText02">
                    <text id="1">Flowly Reminder</text>
                    <text id="2">{message}</text>
                </binding>
            </visual>
        </toast>
"@

        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml($template)
        $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Flowly").Show($toast)
        '''
        
        subprocess.run(["powershell", "-Command", ps_script], 
                      capture_output=True, 
                      creationflags=subprocess.CREATE_NO_WINDOW)

if __name__ == "__main__":
    # Check if already shown today
    if check_already_shown():
        sys.exit(0)  # Already showed, exit silently
    
    # Show notification
    show_notification()