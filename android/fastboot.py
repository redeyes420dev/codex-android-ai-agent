"""Fastboot wrapper for Android device flashing and recovery."""

import subprocess
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FastbootResult:
    """Result of fastboot operation."""
    success: bool
    output: str
    error: str
    exit_code: int

@dataclass
class FastbootDevice:
    """Fastboot device information."""
    id: str
    status: str

class FastbootManager:
    """Fastboot operations manager."""
    
    def __init__(self, fastboot_path: Optional[str] = None):
        """Initialize fastboot manager.
        
        Args:
            fastboot_path: Custom path to fastboot binary
        """
        self.fastboot_path = fastboot_path or "fastboot"
        self._check_fastboot_available()
    
    def _check_fastboot_available(self) -> bool:
        """Check if fastboot is available."""
        try:
            result = subprocess.run(
                [self.fastboot_path, "--version"], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError("Fastboot not found. Please install Android SDK Platform Tools.")
    
    def _run_fastboot_command(
        self, 
        args: List[str], 
        device_id: Optional[str] = None,
        timeout: int = 60
    ) -> FastbootResult:
        """Run fastboot command with error handling.
        
        Args:
            args: Fastboot command arguments
            device_id: Target device ID (optional)
            timeout: Command timeout in seconds
            
        Returns:
            FastbootResult with execution details
        """
        cmd = [self.fastboot_path]
        
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
            
            return FastbootResult(
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
                exit_code=result.returncode
            )
            
        except subprocess.TimeoutExpired:
            return FastbootResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                exit_code=-1
            )
        except Exception as e:
            return FastbootResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1
            )
    
    def list_devices(self) -> List[FastbootDevice]:
        """List devices in fastboot mode.
        
        Returns:
            List of FastbootDevice objects
        """
        result = self._run_fastboot_command(["devices"])
        
        if not result.success:
            return []
        
        devices = []
        lines = result.output.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                device_id = parts[0]
                status = parts[1]
                
                devices.append(FastbootDevice(
                    id=device_id,
                    status=status
                ))
        
        return devices
    
    def flash_partition(
        self, 
        partition: str, 
        image_path: str,
        device_id: Optional[str] = None
    ) -> FastbootResult:
        """Flash partition with image file.
        
        Args:
            partition: Partition name (boot, recovery, system, etc.)
            image_path: Path to image file
            device_id: Target device ID
            
        Returns:
            FastbootResult with flash operation details
        """
        if not Path(image_path).exists():
            return FastbootResult(
                success=False,
                output="",
                error=f"Image file not found: {image_path}",
                exit_code=1
            )
        
        return self._run_fastboot_command(
            ["flash", partition, image_path], 
            device_id,
            timeout=300  # 5 minutes for flashing
        )
    
    def boot_image(
        self, 
        image_path: str,
        device_id: Optional[str] = None
    ) -> FastbootResult:
        """Boot from image without flashing.
        
        Args:
            image_path: Path to boot image
            device_id: Target device ID
            
        Returns:
            FastbootResult with boot operation details
        """
        if not Path(image_path).exists():
            return FastbootResult(
                success=False,
                output="",
                error=f"Image file not found: {image_path}",
                exit_code=1
            )
        
        return self._run_fastboot_command(["boot", image_path], device_id)
    
    def erase_partition(
        self, 
        partition: str,
        device_id: Optional[str] = None
    ) -> FastbootResult:
        """Erase partition.
        
        Args:
            partition: Partition name to erase
            device_id: Target device ID
            
        Returns:
            FastbootResult with erase operation details
        """
        return self._run_fastboot_command(["erase", partition], device_id)
    
    def format_partition(
        self, 
        partition: str,
        device_id: Optional[str] = None
    ) -> FastbootResult:
        """Format partition.
        
        Args:
            partition: Partition name to format
            device_id: Target device ID
            
        Returns:
            FastbootResult with format operation details
        """
        return self._run_fastboot_command(["format", partition], device_id)
    
    def reboot(
        self, 
        target: str = "system",
        device_id: Optional[str] = None
    ) -> FastbootResult:
        """Reboot device.
        
        Args:
            target: Reboot target (system, bootloader, recovery, fastboot)
            device_id: Target device ID
            
        Returns:
            FastbootResult with reboot operation details
        """
        valid_targets = ["system", "bootloader", "recovery", "fastboot"]
        
        if target == "system":
            return self._run_fastboot_command(["reboot"], device_id)
        elif target in valid_targets:
            return self._run_fastboot_command(["reboot", target], device_id)
        else:
            return FastbootResult(
                success=False,
                output="",
                error=f"Invalid reboot target: {target}. Valid targets: {valid_targets}",
                exit_code=1
            )
    
    def get_device_info(self, device_id: Optional[str] = None) -> Dict[str, str]:
        """Get device information.
        
        Args:
            device_id: Target device ID
            
        Returns:
            Dictionary with device information
        """
        info_vars = [
            "product",
            "version",
            "version-bootloader", 
            "version-baseband",
            "serialno",
            "secure",
            "unlocked",
            "max-download-size"
        ]
        
        device_info = {}
        
        for var in info_vars:
            result = self._run_fastboot_command(["getvar", var], device_id)
            if result.success:
                # Fastboot getvar output is in stderr
                output = result.error if result.error else result.output
                
                # Parse output: "variable: value"
                for line in output.split('\n'):
                    if f"{var}:" in line:
                        value = line.split(':', 1)[1].strip()
                        device_info[var] = value
                        break
                else:
                    device_info[var] = "unknown"
            else:
                device_info[var] = "unknown"
        
        return device_info
    
    def unlock_bootloader(self, device_id: Optional[str] = None) -> FastbootResult:
        """Unlock bootloader.
        
        Warning: This will wipe user data!
        
        Args:
            device_id: Target device ID
            
        Returns:
            FastbootResult with unlock operation details
        """
        return self._run_fastboot_command(["flashing", "unlock"], device_id)
    
    def lock_bootloader(self, device_id: Optional[str] = None) -> FastbootResult:
        """Lock bootloader.
        
        Warning: This will wipe user data!
        
        Args:
            device_id: Target device ID
            
        Returns:
            FastbootResult with lock operation details
        """
        return self._run_fastboot_command(["flashing", "lock"], device_id)
    
    def oem_command(
        self, 
        command: str,
        device_id: Optional[str] = None
    ) -> FastbootResult:
        """Execute OEM-specific command.
        
        Args:
            command: OEM command to execute
            device_id: Target device ID
            
        Returns:
            FastbootResult with OEM command details
        """
        return self._run_fastboot_command(["oem", command], device_id)
    
    def flash_all(
        self, 
        zip_path: str,
        device_id: Optional[str] = None,
        wipe_user_data: bool = False
    ) -> FastbootResult:
        """Flash all partitions from flashall package.
        
        Args:
            zip_path: Path to flashall zip package
            device_id: Target device ID  
            wipe_user_data: Wipe user data during flash
            
        Returns:
            FastbootResult with flash-all operation details
        """
        if not Path(zip_path).exists():
            return FastbootResult(
                success=False,
                output="",
                error=f"Flashall package not found: {zip_path}",
                exit_code=1
            )
        
        args = ["update", zip_path]
        if wipe_user_data:
            args.insert(1, "-w")  # Insert -w flag before update
        
        return self._run_fastboot_command(
            args, 
            device_id,
            timeout=600  # 10 minutes for full flash
        )
    
    def wait_for_device(
        self, 
        device_id: Optional[str] = None, 
        timeout: int = 60
    ) -> bool:
        """Wait for device to be ready in fastboot mode.
        
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
                    if device.id == device_id:
                        return True
            else:
                if devices:
                    return True
            
            time.sleep(2)
        
        return False
    
    def execute(
        self, 
        action: str, 
        target: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> FastbootResult:
        """Execute generic fastboot action.
        
        Args:
            action: Fastboot action (flash, boot, reboot, etc.)
            target: Action target (partition name, file path, etc.)
            device_id: Target device ID
            
        Returns:
            FastbootResult with action details
        """
        if action == "devices":
            result = self._run_fastboot_command(["devices"], device_id)
            return result
        elif action == "reboot":
            return self.reboot(target or "system", device_id)
        elif action == "flash" and target:
            # Parse "partition:image" format
            if ":" in target:
                partition, image = target.split(":", 1)
                return self.flash_partition(partition, image, device_id)
            else:
                return FastbootResult(
                    success=False,
                    output="",
                    error="Flash target must be in format 'partition:image_path'",
                    exit_code=1
                )
        elif action == "boot" and target:
            return self.boot_image(target, device_id)
        elif action == "erase" and target:
            return self.erase_partition(target, device_id)
        else:
            # Generic command execution
            args = [action]
            if target:
                args.append(target)
            return self._run_fastboot_command(args, device_id)