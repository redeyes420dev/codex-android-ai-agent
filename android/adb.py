"""ADB (Android Debug Bridge) wrapper and automation."""

import subprocess
import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import time

@dataclass
class CommandResult:
    """Result of executing a command."""
    success: bool
    output: str
    error: str
    exit_code: int

@dataclass  
class AndroidDevice:
    """Android device information."""
    id: str
    status: str
    model: str = "unknown"
    android_version: str = "unknown"
    api_level: str = "unknown"

class ADBManager:
    """ADB operations manager."""
    
    def __init__(self, adb_path: Optional[str] = None):
        """Initialize ADB manager.
        
        Args:
            adb_path: Custom path to adb binary
        """
        self.adb_path = adb_path or "adb"
        self._check_adb_available()
    
    def _check_adb_available(self) -> bool:
        """Check if ADB is available."""
        try:
            result = subprocess.run(
                [self.adb_path, "version"], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError("ADB not found. Please install Android SDK Platform Tools.")
    
    def _run_adb_command(
        self, 
        args: List[str], 
        device_id: Optional[str] = None,
        timeout: int = 30
    ) -> CommandResult:
        """Run ADB command with error handling.
        
        Args:
            args: ADB command arguments
            device_id: Target device ID (optional)
            timeout: Command timeout in seconds
            
        Returns:
            CommandResult with execution details
        """
        cmd = [self.adb_path]
        
        if device_id:
            cmd.extend(["-s", device_id])
            
        cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                exit_code=-1
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1
            )
    
    def list_devices(self) -> List[AndroidDevice]:
        """List connected Android devices.
        
        Returns:
            List of AndroidDevice objects
        """
        result = self._run_adb_command(["devices", "-l"])
        
        if not result.success:
            return []
        
        devices = []
        lines = result.output.split('\n')[1:]  # Skip header
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.strip().split()
            if len(parts) >= 2:
                device_id = parts[0]
                status = parts[1]
                
                # Extract model from device info
                model = "unknown"
                if len(parts) > 2:
                    device_info = " ".join(parts[2:])
                    model_match = re.search(r'model:(\S+)', device_info)
                    if model_match:
                        model = model_match.group(1)
                
                # Get additional device info
                android_version = self._get_device_property(device_id, "ro.build.version.release")
                api_level = self._get_device_property(device_id, "ro.build.version.sdk")
                
                devices.append(AndroidDevice(
                    id=device_id,
                    status=status,
                    model=model,
                    android_version=android_version,
                    api_level=api_level
                ))
        
        return devices
    
    def _get_device_property(self, device_id: str, prop_name: str) -> str:
        """Get device system property."""
        result = self._run_adb_command(["shell", "getprop", prop_name], device_id)
        return result.output if result.success else "unknown"
    
    def install_apk(
        self, 
        apk_path: str, 
        device_id: Optional[str] = None,
        replace: bool = False,
        test: bool = False
    ) -> CommandResult:
        """Install APK on device.
        
        Args:
            apk_path: Path to APK file
            device_id: Target device ID
            replace: Replace existing app
            test: Install as test APK
            
        Returns:
            CommandResult with installation details
        """
        if not Path(apk_path).exists():
            return CommandResult(
                success=False,
                output="",
                error=f"APK file not found: {apk_path}",
                exit_code=1
            )
        
        args = ["install"]
        if replace:
            args.append("-r")
        if test:
            args.append("-t")
        args.append(apk_path)
        
        return self._run_adb_command(args, device_id, timeout=120)
    
    def uninstall_package(
        self, 
        package_name: str, 
        device_id: Optional[str] = None,
        keep_data: bool = False
    ) -> CommandResult:
        """Uninstall package from device.
        
        Args:
            package_name: Package name to uninstall
            device_id: Target device ID
            keep_data: Keep app data after uninstall
            
        Returns:
            CommandResult with uninstallation details
        """
        args = ["uninstall"]
        if keep_data:
            args.append("-k")
        args.append(package_name)
        
        return self._run_adb_command(args, device_id)
    
    def shell_command(
        self, 
        command: str, 
        device_id: Optional[str] = None,
        timeout: int = 30
    ) -> CommandResult:
        """Execute shell command on device.
        
        Args:
            command: Shell command to execute
            device_id: Target device ID
            timeout: Command timeout
            
        Returns:
            CommandResult with command output
        """
        return self._run_adb_command(["shell", command], device_id, timeout)
    
    def push_file(
        self, 
        local_path: str, 
        remote_path: str,
        device_id: Optional[str] = None
    ) -> CommandResult:
        """Push file to device.
        
        Args:
            local_path: Local file path
            remote_path: Remote file path on device
            device_id: Target device ID
            
        Returns:
            CommandResult with push operation details
        """
        return self._run_adb_command(["push", local_path, remote_path], device_id)
    
    def pull_file(
        self, 
        remote_path: str, 
        local_path: str,
        device_id: Optional[str] = None
    ) -> CommandResult:
        """Pull file from device.
        
        Args:
            remote_path: Remote file path on device
            local_path: Local destination path
            device_id: Target device ID
            
        Returns:
            CommandResult with pull operation details
        """
        return self._run_adb_command(["pull", remote_path, local_path], device_id)
    
    def get_build_info(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        """Get device build information.
        
        Args:
            device_id: Target device ID
            
        Returns:
            Dictionary with build properties
        """
        important_props = [
            "ro.build.version.release",
            "ro.build.version.sdk", 
            "ro.product.model",
            "ro.product.brand",
            "ro.product.device",
            "ro.build.version.security_patch",
            "ro.build.fingerprint",
            "ro.product.cpu.abi"
        ]
        
        build_info = {}
        
        for prop in important_props:
            result = self._run_adb_command(["shell", "getprop", prop], device_id)
            key = prop.replace("ro.", "").replace("build.", "").replace("product.", "")
            build_info[key] = result.output if result.success else "unknown"
        
        return build_info
    
    def start_server(self) -> CommandResult:
        """Start ADB server."""
        return self._run_adb_command(["start-server"])
    
    def kill_server(self) -> CommandResult:
        """Kill ADB server."""
        return self._run_adb_command(["kill-server"])
    
    def wait_for_device(
        self, 
        device_id: Optional[str] = None, 
        timeout: int = 60
    ) -> bool:
        """Wait for device to be ready.
        
        Args:
            device_id: Target device ID
            timeout: Maximum wait time in seconds
            
        Returns:
            True if device is ready, False if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            devices = self.list_devices()
            
            if device_id:
                for device in devices:
                    if device.id == device_id and device.status == "device":
                        return True
            else:
                if devices and any(d.status == "device" for d in devices):
                    return True
            
            time.sleep(2)
        
        return False
    
    def get_packages(
        self, 
        device_id: Optional[str] = None,
        system_apps: bool = False,
        user_apps_only: bool = True
    ) -> List[str]:
        """Get installed packages on device.
        
        Args:
            device_id: Target device ID
            system_apps: Include system apps
            user_apps_only: Only user-installed apps
            
        Returns:
            List of package names
        """
        args = ["shell", "pm", "list", "packages"]
        
        if user_apps_only and not system_apps:
            args.append("-3")  # Third-party packages only
        
        result = self._run_adb_command(args, device_id)
        
        if not result.success:
            return []
        
        packages = []
        for line in result.output.split('\n'):
            if line.startswith("package:"):
                package_name = line.replace("package:", "").strip()
                packages.append(package_name)
        
        return packages
    
    def take_screenshot(
        self, 
        local_path: str = "screenshot.png",
        device_id: Optional[str] = None
    ) -> CommandResult:
        """Take screenshot of device screen.
        
        Args:
            local_path: Local path to save screenshot
            device_id: Target device ID
            
        Returns:
            CommandResult with screenshot operation details
        """
        remote_path = "/sdcard/cadx_screenshot.png"
        
        # Take screenshot
        screenshot_result = self._run_adb_command(
            ["shell", "screencap", "-p", remote_path], 
            device_id
        )
        
        if not screenshot_result.success:
            return screenshot_result
        
        # Pull screenshot to local
        pull_result = self.pull_file(remote_path, local_path, device_id)
        
        # Cleanup remote file
        self._run_adb_command(["shell", "rm", remote_path], device_id)
        
        return pull_result