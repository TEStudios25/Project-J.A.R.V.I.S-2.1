import psutil
import subprocess

def get_cpu_usage() -> str:
    """Returns the current CPU usage percentage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    return f"CPU: {cpu_percent}%"

def get_ram_usage() -> str:
    """Returns the current RAM usage and available memory."""
    ram = psutil.virtual_memory()
    percent = ram.percent
    available_gb = round(ram.available / (1024 ** 3), 2)
    total_gb = round(ram.total / (1024 ** 3), 2)
    return f"RAM: {percent}% ({available_gb}GB free of {total_gb}GB)"

def get_disk_usage() -> str:
    """Returns the main OS drive storage stats."""
    try:
        disk = psutil.disk_usage('C:\\')
        percent = disk.percent
        free_gb = round(disk.free / (1024 ** 3), 2)
        total_gb = round(disk.total / (1024 ** 3), 2)
        return f"Disk: {percent}% used ({free_gb}GB free of {total_gb}GB)"
    except Exception as e:
        return f"Disk: Unable to read drive C:\\ ({str(e)})"

def get_wifi_status() -> str:
    """Returns basic network activity (data sent/received)."""
    net = psutil.net_io_counters()
    sent_mb = round(net.bytes_sent / (1024 ** 2), 2)
    recv_mb = round(net.bytes_recv / (1024 ** 2), 2)
    return f"Network: {sent_mb}MB Sent / {recv_mb}MB Received since boot."

def get_gpu_status() -> str:
    """Dynamically detects NVIDIA or Intel/AMD GPUs and their Load %."""
    # 1. Try NVIDIA first
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            return f"GPU: {gpu.name} | Load: {round(gpu.load * 100, 1)}% | Temp: {gpu.temperature}°C"
    except ImportError:
        pass # Skip if GPUtil isn't installed or no NVIDIA card is found
    
    # 2. The Hack: Fallback to Windows PowerShell for Intel HD Graphics
    import subprocess
    try:
        # Ask Windows for the GPU Name quietly
        name_req = subprocess.check_output(
            ["wmic", "path", "Win32_VideoController", "get", "name"], 
            text=True, 
            creationflags=0x08000000  # Prevents empty CMD windows from flashing
        )
        names = [line.strip() for line in name_req.split('\n') if line.strip() and "Name" not in line]
        gpu_name = names[0] if names else "Intel HD Graphics"

        # Ask Windows Performance Counters for the GPU 3D Engine Load
        ps_cmd = (
            'powershell "((Get-Counter \'\\GPU Engine(*engtype_3D)\\Utilization Percentage\' '
            '-ErrorAction SilentlyContinue).CounterSamples | Measure-Object -Property CookedValue -Sum).Sum"'
        )
        load_req = subprocess.check_output(ps_cmd, shell=True, text=True).strip()
        
        # Parse the output into a clean percentage
        if load_req and load_req.replace('.', '', 1).isdigit():
            load_percent = round(float(load_req), 1)
            return f"GPU: {gpu_name} | Load: {load_percent}%"
        else:
            return f"GPU: {gpu_name} | Load: 0.0% (Idle)"
            
    except Exception as e:
        return f"GPU: Intel Graphics | Status: Online (OS blocking telemetry)"
    
def get_battery_status() -> str:
    """Returns battery percentage and plug status."""
    battery = psutil.sensors_battery()
    if not battery:
        return "Battery: Desktop mode (AC Power)"
    plugged = "Charging" if battery.power_plugged else "Discharging"
    return f"Battery: {battery.percent}% ({plugged})"

def get_full_system_report() -> str:
    """Compiles all hardware stats into a single diagnostic report."""
    report = (
        f"--- 💻 SYSTEM PERFORMANCE REPORT ---\n"
        f"1. {get_cpu_usage()}\n"
        f"2. {get_ram_usage()}\n"
        f"3. {get_gpu_status()}\n"
        f"4. {get_disk_usage()}\n"
        f"5. {get_wifi_status()}\n"
        f"6. {get_battery_status()}\n"
        f"------------------------------------"
    )
    return report

# ===============================================================
# 🧪 ISOLATED TESTING BLOCK
# ===============================================================
if __name__ == "__main__":
    print("\n[J.A.R.V.I.S.] Scanning hardware telemetry...\n")
    print(get_full_system_report())