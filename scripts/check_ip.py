#!/usr/bin/env python3
"""
Check and store current IP address
"""

import requests
import json
import datetime
import os

def get_current_ip():
    """Get current public IP address"""
    try:
        # Try multiple services in case one is down
        services = [
            "https://api.ipify.org",
            "https://ipinfo.io/ip",
            "https://icanhazip.com",
            "https://ifconfig.me/ip"
        ]
        
        for service in services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    print(f"✅ Got IP from {service}: {ip}")
                    return ip
            except:
                continue
        
        print("❌ Could not get IP from any service")
        return None
        
    except Exception as e:
        print(f"❌ Error getting IP: {e}")
        return None

def store_ip_info(ip):
    """Store IP information with timestamp"""
    ip_info = {
        "ip_address": ip,
        "timestamp": datetime.datetime.now().isoformat(),
        "status": "active"
    }
    
    # Store in a file
    with open("ip_history.json", "a") as f:
        f.write(json.dumps(ip_info) + "\n")
    
    # Also store current IP separately
    with open("current_ip.json", "w") as f:
        json.dump(ip_info, f, indent=2)
    
    print(f"💾 IP stored: {ip}")

def main():
    print("🔍 Checking current IP address...")
    
    ip = get_current_ip()
    if ip:
        store_ip_info(ip)
        print(f"📍 Current IP: {ip}")
    else:
        print("❌ Could not determine IP address")

if __name__ == "__main__":
    main()
