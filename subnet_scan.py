import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

def is_port_open(ip, port=5000, timeout=0.5):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False

def scan_subnet(subnet_prefix, port=5000, max_workers=100):
    ips = [f"{subnet_prefix}.{i}" for i in range(1, 255)]
    found = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ip = {executor.submit(is_port_open, ip, port): ip for ip in ips}
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                if future.result():
                    found.append(ip)
            except Exception:
                pass
    return found

if __name__ == "__main__":
    try:
        import netifaces
        gws = netifaces.gateways()
        default_iface = gws['default'][netifaces.AF_INET][1]
        ip = netifaces.ifaddresses(default_iface)[netifaces.AF_INET][0]['addr']
        subnet_prefix = '.'.join(ip.split('.')[:3])
    except Exception:
        subnet_prefix = input("Enter your subnet prefix (e.g., 192.168.1): ")
    print(f"Scanning subnet: {subnet_prefix}.0/24 ...")
    active_hosts = scan_subnet(subnet_prefix)
    print("Active hosts with port 5000 open:", active_hosts) 