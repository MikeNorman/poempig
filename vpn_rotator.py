#!/usr/bin/env python3
"""
OpenVPN Rotator for Automated IP Switching
"""

import subprocess
import time
import random
import os
from pathlib import Path

class OpenVPNRotator:
    def __init__(self, config_dir="servers/"):
        self.config_dir = Path(config_dir)
        self.configs = list(self.config_dir.glob("*.ovpn"))
        self.current_config = None
        self.openvpn_process = None
        
        if not self.configs:
            raise FileNotFoundError(f"No .ovpn files found in {config_dir}")
        
        print(f"🔧 Found {len(self.configs)} OpenVPN configs")
        for config in self.configs:
            print(f"  - {config.name}")
    
    def get_random_config(self):
        """Get a random server config"""
        return random.choice(self.configs)
    
    def disconnect(self):
        """Disconnect current VPN"""
        if self.openvpn_process:
            self.openvpn_process.terminate()
            self.openvpn_process.wait()
        
        # Kill any remaining openvpn processes
        subprocess.run(['sudo', 'pkill', 'openvpn'], capture_output=True)
        time.sleep(1)
    
    def connect(self, config_file):
        """Connect to specific server"""
        self.disconnect()
        
        print(f"🔄 Connecting to {config_file.name}...")
        cmd = ['sudo', 'openvpn', '--config', str(config_file), '--daemon']
        
        try:
            self.openvpn_process = subprocess.Popen(cmd)
            time.sleep(3)  # Wait for connection
            
            if self.is_connected():
                self.current_config = config_file
                new_ip = self.get_current_ip()
                print(f"✅ Connected! New IP: {new_ip}")
                return True
            else:
                print(f"❌ Failed to connect to {config_file.name}")
                return False
        except Exception as e:
            print(f"❌ Error connecting: {e}")
            return False
    
    def is_connected(self):
        """Check if VPN is connected"""
        try:
            result = subprocess.run(['curl', '-s', 'https://api.ipify.org'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def get_current_ip(self):
        """Get current public IP"""
        try:
            result = subprocess.run(['curl', '-s', 'https://api.ipify.org'], 
                                  capture_output=True, timeout=5)
            return result.stdout.decode().strip()
        except:
            return "Unknown"
    
    def rotate(self):
        """Switch to random server"""
        config = self.get_random_config()
        
        # Don't switch to the same server
        if len(self.configs) > 1:
            while config == self.current_config:
                config = self.get_random_config()
        
        return self.connect(config)
    
    def cleanup(self):
        """Clean up on exit"""
        self.disconnect()

# Test the rotator
if __name__ == "__main__":
    try:
        rotator = OpenVPNRotator()
        
        print("🧪 Testing VPN rotation...")
        for i in range(3):
            print(f"\n--- Test {i+1}/3 ---")
            if rotator.rotate():
                time.sleep(2)
            else:
                print("❌ Rotation failed")
                break
        
        print("\n✅ Test complete!")
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("Please download OpenVPN configs to the 'servers/' directory")
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        if 'rotator' in locals():
            rotator.cleanup()
