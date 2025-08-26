"""Android device management and automation."""

import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from .adb import ADBManager, AndroidDevice
from .fastboot import FastbootManager, FastbootDevice

@dataclass
class DeviceCapabilities:
    """Device capabilities and features."""
    root_access: bool = False
    bootloader_unlocked: bool = False
    fastboot_available: bool = False
    usb_debugging: bool = False
    wireless_debugging: bool = False
    developer_options: bool = False

@dataclass
class ExtendedDeviceInfo:
    """Extended device information."""
    basic_info: AndroidDevice
    capabilities: DeviceCapabilities
    battery_level: Optional[int] = None
    screen_resolution: Optional[str] = None
    density: Optional[str] = None
    total_memory: Optional[str] = None
    available_storage: Optional[str] = None
    wifi_connected: bool = False
    mobile_data: bool = False

class DeviceManager:
    """Comprehensive Android device management."""
    
    def __init__(self, adb_path: Optional[str] = None, fastboot_path: Optional[str] = None):
        """Initialize device manager.
        
        Args:
            adb_path: Custom path to adb binary
            fastboot_path: Custom path to fastboot binary
        """
        self.adb = ADBManager(adb_path)
        self.fastboot = FastbootManager(fastboot_path)
        self._device_cache = {}
        self._cache_expiry = 300  # 5 minutes
    
    def discover_devices(self, include_fastboot: bool = True) -> Dict[str, ExtendedDeviceInfo]:
        """Discover all connected Android devices.
        
        Args:
            include_fastboot: Also check for fastboot devices
            
        Returns:
            Dictionary mapping device IDs to ExtendedDeviceInfo
        """
        discovered = {}
        
        # Get ADB devices
        adb_devices = self.adb.list_devices()
        for device in adb_devices:
            if device.status == "device":  # Only fully connected devices
                extended_info = self._get_extended_device_info(device)
                discovered[device.id] = extended_info
        
        # Get fastboot devices if requested
        if include_fastboot:
            try:
                fastboot_devices = self.fastboot.list_devices()
                for fb_device in fastboot_devices:
                    if fb_device.id not in discovered:
                        # Create basic info for fastboot-only device
                        basic_info = AndroidDevice(
                            id=fb_device.id,
                            status="fastboot",
                            model="unknown",
                            android_version="unknown",
                            api_level="unknown"
                        )
                        
                        capabilities = DeviceCapabilities(
                            fastboot_available=True,
                            bootloader_unlocked=True  # Assume unlocked if in fastboot
                        )
                        
                        discovered[fb_device.id] = ExtendedDeviceInfo(
                            basic_info=basic_info,
                            capabilities=capabilities
                        )
            except Exception:
                # Fastboot not available or no devices
                pass
        
        return discovered
    
    def _get_extended_device_info(self, device: AndroidDevice) -> ExtendedDeviceInfo:
        """Get extended information for a device.
        
        Args:
            device: Basic AndroidDevice info
            
        Returns:
            ExtendedDeviceInfo with capabilities and details
        """
        cache_key = f"{device.id}_{int(time.time() // self._cache_expiry)}"
        
        if cache_key in self._device_cache:
            return self._device_cache[cache_key]
        
        capabilities = self._detect_capabilities(device.id)
        
        # Get additional device properties
        battery_level = self._get_battery_level(device.id)
        screen_info = self._get_screen_info(device.id)
        memory_info = self._get_memory_info(device.id)
        network_info = self._get_network_info(device.id)
        
        extended_info = ExtendedDeviceInfo(
            basic_info=device,
            capabilities=capabilities,
            battery_level=battery_level,
            screen_resolution=screen_info.get("resolution"),
            density=screen_info.get("density"),
            total_memory=memory_info.get("total"),
            available_storage=memory_info.get("available"),
            wifi_connected=network_info.get("wifi", False),
            mobile_data=network_info.get("mobile", False)
        )
        
        self._device_cache[cache_key] = extended_info
        return extended_info
    
    def _detect_capabilities(self, device_id: str) -> DeviceCapabilities:
        """Detect device capabilities.
        
        Args:
            device_id: Device ID to check
            
        Returns:
            DeviceCapabilities object
        """
        capabilities = DeviceCapabilities()
        
        # Check root access
        su_result = self.adb.shell_command("su -c 'id'", device_id)
        capabilities.root_access = su_result.success and "uid=0" in su_result.output
        
        # Check USB debugging (if we're connected, it's enabled)
        capabilities.usb_debugging = True
        
        # Check developer options
        dev_options_result = self.adb.shell_command(
            "settings get global development_settings_enabled", 
            device_id
        )
        capabilities.developer_options = (
            dev_options_result.success and dev_options_result.output.strip() == "1"
        )
        
        # Check wireless debugging (API 30+)
        if int(self.adb._get_device_property(device_id, "ro.build.version.sdk")) >= 30:
            wireless_result = self.adb.shell_command(
                "settings get global adb_wifi_enabled", 
                device_id
            )
            capabilities.wireless_debugging = (
                wireless_result.success and wireless_result.output.strip() == "1"
            )
        
        # Check bootloader lock status
        bootloader_result = self.adb.shell_command("getprop ro.boot.veritymode", device_id)
        capabilities.bootloader_unlocked = (
            bootloader_result.success and "disabled" in bootloader_result.output.lower()
        )
        
        # Check fastboot availability (try to reboot to fastboot and back)
        # Note: This is potentially disruptive, so we'll be conservative
        capabilities.fastboot_available = capabilities.bootloader_unlocked
        
        return capabilities
    
    def _get_battery_level(self, device_id: str) -> Optional[int]:
        """Get battery level percentage."""
        result = self.adb.shell_command("dumpsys battery | grep level", device_id)
        
        if result.success:
            try:
                # Parse "level: 85" format
                level_line = result.output.split('\n')[0]
                level = int(level_line.split(':')[1].strip())
                return level
            except (IndexError, ValueError):
                pass
        
        return None
    
    def _get_screen_info(self, device_id: str) -> Dict[str, str]:
        """Get screen resolution and density information."""
        info = {}
        
        # Get screen size
        size_result = self.adb.shell_command("wm size", device_id)
        if size_result.success and "Physical size:" in size_result.output:
            try:
                size_line = [l for l in size_result.output.split('\n') if "Physical size:" in l][0]
                resolution = size_line.split(': ')[1].strip()
                info["resolution"] = resolution
            except (IndexError, ValueError):
                pass
        
        # Get density
        density_result = self.adb.shell_command("wm density", device_id)
        if density_result.success and "Physical density:" in density_result.output:
            try:
                density_line = [l for l in density_result.output.split('\n') if "Physical density:" in l][0]
                density = density_line.split(': ')[1].strip()
                info["density"] = f"{density}dpi"
            except (IndexError, ValueError):
                pass
        
        return info
    
    def _get_memory_info(self, device_id: str) -> Dict[str, str]:
        """Get memory and storage information."""
        info = {}
        
        # Get RAM info
        meminfo_result = self.adb.shell_command("cat /proc/meminfo | grep MemTotal", device_id)
        if meminfo_result.success:
            try:
                # Parse "MemTotal:        3916000 kB" format
                mem_line = meminfo_result.output.strip()
                mem_kb = int(mem_line.split()[1])
                mem_gb = round(mem_kb / 1024 / 1024, 1)
                info["total"] = f"{mem_gb}GB RAM"
            except (IndexError, ValueError):
                pass
        
        # Get storage info
        storage_result = self.adb.shell_command("df /data | tail -1", device_id)
        if storage_result.success:
            try:
                # Parse df output
                fields = storage_result.output.split()
                available_kb = int(fields[3])
                available_gb = round(available_kb / 1024 / 1024, 1)
                info["available"] = f"{available_gb}GB available"
            except (IndexError, ValueError):
                pass
        
        return info
    
    def _get_network_info(self, device_id: str) -> Dict[str, bool]:
        """Get network connectivity information."""
        info = {"wifi": False, "mobile": False}
        
        # Check WiFi
        wifi_result = self.adb.shell_command("dumpsys wifi | grep 'Wi-Fi is'", device_id)
        if wifi_result.success and "enabled" in wifi_result.output:
            info["wifi"] = True
        
        # Check mobile data
        mobile_result = self.adb.shell_command("settings get global mobile_data", device_id)
        if mobile_result.success and mobile_result.output.strip() == "1":
            info["mobile"] = True
        
        return info
    
    def setup_device_for_development(
        self, 
        device_id: str,
        enable_wifi_debugging: bool = False,
        install_tools: bool = False
    ) -> Dict[str, bool]:
        """Setup device for development with optimal settings.
        
        Args:
            device_id: Target device ID
            enable_wifi_debugging: Enable wireless ADB debugging
            install_tools: Install additional development tools
            
        Returns:
            Dictionary with setup results
        """
        results = {}
        
        # Enable developer options (should already be enabled)
        dev_result = self.adb.shell_command(
            "settings put global development_settings_enabled 1", 
            device_id
        )
        results["developer_options"] = dev_result.success
        
        # Enable USB debugging (should already be enabled)
        usb_result = self.adb.shell_command(
            "settings put global adb_enabled 1", 
            device_id
        )
        results["usb_debugging"] = usb_result.success
        
        # Enable wireless debugging if requested and supported
        if enable_wifi_debugging:
            wifi_result = self.adb.shell_command(
                "settings put global adb_wifi_enabled 1", 
                device_id
            )
            results["wifi_debugging"] = wifi_result.success
        
        # Disable animations for faster testing
        animation_settings = [
            "settings put global window_animation_scale 0.0",
            "settings put global transition_animation_scale 0.0", 
            "settings put global animator_duration_scale 0.0"
        ]
        
        animation_results = []
        for setting in animation_settings:
            result = self.adb.shell_command(setting, device_id)
            animation_results.append(result.success)
        
        results["disable_animations"] = all(animation_results)
        
        # Stay awake while charging
        awake_result = self.adb.shell_command(
            "settings put global stay_on_while_plugged_in 3", 
            device_id
        )
        results["stay_awake"] = awake_result.success
        
        # Install development tools if requested
        if install_tools:
            # This would install APKs for development tools
            # Implementation depends on what tools are needed
            results["install_tools"] = True  # Placeholder
        
        return results
    
    def backup_device_settings(
        self, 
        device_id: str, 
        output_file: str
    ) -> bool:
        """Backup device settings and configuration.
        
        Args:
            device_id: Device ID to backup
            output_file: Output file path for backup
            
        Returns:
            True if successful, False otherwise
        """
        try:
            device_info = self.discover_devices()[device_id]
            
            # Get system settings
            settings_result = self.adb.shell_command(
                "settings list system", 
                device_id
            )
            
            global_settings_result = self.adb.shell_command(
                "settings list global", 
                device_id
            )
            
            secure_settings_result = self.adb.shell_command(
                "settings list secure", 
                device_id
            )
            
            backup_data = {
                "timestamp": time.time(),
                "device_info": asdict(device_info),
                "system_settings": settings_result.output.split('\n') if settings_result.success else [],
                "global_settings": global_settings_result.output.split('\n') if global_settings_result.success else [],
                "secure_settings": secure_settings_result.output.split('\n') if secure_settings_result.success else []
            }
            
            with open(output_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return True
            
        except Exception:
            return False
    
    def restore_device_settings(
        self, 
        device_id: str, 
        backup_file: str
    ) -> Dict[str, bool]:
        """Restore device settings from backup.
        
        Args:
            device_id: Device ID to restore to
            backup_file: Backup file path
            
        Returns:
            Dictionary with restore results
        """
        results = {"system": False, "global": False, "secure": False}
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            # Restore system settings
            for setting in backup_data.get("system_settings", []):
                if '=' in setting:
                    key, value = setting.split('=', 1)
                    result = self.adb.shell_command(
                        f"settings put system {key} '{value}'", 
                        device_id
                    )
                    if result.success:
                        results["system"] = True
            
            # Restore global settings (be careful with these)
            safe_global_settings = [
                "window_animation_scale",
                "transition_animation_scale", 
                "animator_duration_scale",
                "stay_on_while_plugged_in"
            ]
            
            for setting in backup_data.get("global_settings", []):
                if '=' in setting:
                    key, value = setting.split('=', 1)
                    if key in safe_global_settings:
                        result = self.adb.shell_command(
                            f"settings put global {key} '{value}'", 
                            device_id
                        )
                        if result.success:
                            results["global"] = True
            
            return results
            
        except Exception:
            return results
    
    def monitor_device_health(
        self, 
        device_id: str, 
        duration: int = 300
    ) -> Dict[str, Any]:
        """Monitor device health metrics over time.
        
        Args:
            device_id: Device to monitor
            duration: Monitoring duration in seconds
            
        Returns:
            Health monitoring results
        """
        start_time = time.time()
        samples = []
        
        while time.time() - start_time < duration:
            sample = {
                "timestamp": time.time(),
                "battery_level": self._get_battery_level(device_id),
                "memory_info": self._get_memory_info(device_id),
                "network_info": self._get_network_info(device_id)
            }
            
            # Check for thermal throttling
            thermal_result = self.adb.shell_command(
                "cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | head -1", 
                device_id
            )
            if thermal_result.success and thermal_result.output:
                try:
                    temp_millic = int(thermal_result.output.strip())
                    temp_celsius = temp_millic / 1000
                    sample["temperature"] = temp_celsius
                except (ValueError, IndexError):
                    pass
            
            samples.append(sample)
            time.sleep(30)  # Sample every 30 seconds
        
        return {
            "device_id": device_id,
            "duration": duration,
            "samples": samples,
            "summary": self._analyze_health_samples(samples)
        }
    
    def _analyze_health_samples(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze health monitoring samples."""
        if not samples:
            return {}
        
        battery_levels = [s.get("battery_level") for s in samples if s.get("battery_level")]
        temperatures = [s.get("temperature") for s in samples if s.get("temperature")]
        
        summary = {}
        
        if battery_levels:
            summary["battery"] = {
                "initial": battery_levels[0],
                "final": battery_levels[-1],
                "change": battery_levels[-1] - battery_levels[0],
                "average": sum(battery_levels) / len(battery_levels)
            }
        
        if temperatures:
            summary["thermal"] = {
                "max_temp": max(temperatures),
                "avg_temp": sum(temperatures) / len(temperatures),
                "overheating_risk": max(temperatures) > 60  # Basic threshold
            }
        
        return summary