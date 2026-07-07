import subprocess

def ping_network_device(ip_address: str) -> str:
    """
    Sends a network ping request to a local device IP address (e.g. your phone at 192.168.1.50) 
    to see if it is currently connected to your Wi-Fi network.
    """
    ip_address = ip_address.strip()
    print(f"\n[📡 J.A.R.V.I.S. is pinging device: {ip_address}...]")
    try:
        # Pings once (-n 1 on Windows) with 1000ms timeout
        res = subprocess.run(
            f"ping -n 1 -w 1000 {ip_address}", 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            creationflags=0x08000000
        )
        if res.returncode == 0:
            return f"Device {ip_address} is online and responding to network pings."
        else:
            return f"Device {ip_address} is offline or unreachable on the current Wi-Fi network."
    except Exception as e:
        return f"Failed to ping network device. Error: {str(e)}"
