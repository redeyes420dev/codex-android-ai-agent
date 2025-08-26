"""Android development commands."""

import typer
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from pathlib import Path

android_app = typer.Typer(help="🤖 Android development automation commands")
console = Console()

@android_app.command()
def devices(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """List connected Android devices."""
    try:
        from android.adb import ADBManager
        adb = ADBManager()
        devices = adb.list_devices()
        
        if json_output:
            import json
            console.print(json.dumps(devices))
        else:
            if not devices:
                console.print("❌ No devices found")
                return
                
            table = Table(title="📱 Connected Android Devices")
            table.add_column("Device ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Model", style="yellow")
            
            for device in devices:
                table.add_row(
                    device.get("id", "unknown"),
                    device.get("status", "unknown"),
                    device.get("model", "unknown")
                )
            console.print(table)
            
    except ImportError:
        console.print("❌ Android module not available")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@android_app.command()
def logcat(
    device: Optional[str] = typer.Option(None, "--device", "-d", help="Target device ID"),
    filter_tag: Optional[str] = typer.Option(None, "--filter", "-f", help="Filter by tag"),
    analyze: bool = typer.Option(False, "--analyze", help="AI-powered log analysis"),
    save: Optional[Path] = typer.Option(None, "--save", help="Save logs to file")
):
    """Capture and analyze Android logs."""
    try:
        from android.logcat import LogcatManager
        from agents.log_analyzer import LogAnalyzer
        
        logcat = LogcatManager(device_id=device)
        
        if analyze:
            console.print("🤖 Starting AI-powered log analysis...")
            analyzer = LogAnalyzer()
            logs = logcat.capture(filter_tag=filter_tag, duration=30)
            analysis = analyzer.analyze(logs)
            console.print(analysis)
        else:
            console.print(f"📱 Capturing logs from device: {device or 'default'}")
            if filter_tag:
                console.print(f"🔍 Filter: {filter_tag}")
            
            logs = logcat.stream(filter_tag=filter_tag)
            for log_line in logs:
                if save:
                    with open(save, 'a') as f:
                        f.write(log_line + '\n')
                console.print(log_line)
                
    except ImportError as e:
        console.print(f"❌ Required modules not available: {e}")
    except KeyboardInterrupt:
        console.print("\n⏹️  Log capture stopped")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@android_app.command()
def install(
    apk_path: Path = typer.Argument(..., help="Path to APK file"),
    device: Optional[str] = typer.Option(None, "--device", "-d", help="Target device ID"),
    replace: bool = typer.Option(False, "--replace", "-r", help="Replace existing app"),
    test: bool = typer.Option(False, "--test", "-t", help="Install as test APK")
):
    """Install APK on Android device."""
    try:
        from android.adb import ADBManager
        
        if not apk_path.exists():
            console.print(f"❌ APK file not found: {apk_path}")
            return
            
        adb = ADBManager()
        console.print(f"📱 Installing {apk_path.name}...")
        
        result = adb.install_apk(
            str(apk_path), 
            device_id=device,
            replace=replace,
            test=test
        )
        
        if result.success:
            console.print("✅ APK installed successfully")
        else:
            console.print(f"❌ Installation failed: {result.error}")
            
    except ImportError:
        console.print("❌ Android ADB module not available")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@android_app.command()
def shell(
    command: str = typer.Argument(..., help="Shell command to execute"),
    device: Optional[str] = typer.Option(None, "--device", "-d", help="Target device ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Execute shell command on Android device."""
    try:
        from android.adb import ADBManager
        
        adb = ADBManager()
        result = adb.shell_command(command, device_id=device)
        
        if json_output:
            import json
            console.print(json.dumps({
                "command": command,
                "success": result.success,
                "output": result.output,
                "error": result.error
            }))
        else:
            if result.success:
                console.print(result.output)
            else:
                console.print(f"❌ Command failed: {result.error}")
                
    except ImportError:
        console.print("❌ Android ADB module not available")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@android_app.command()
def build_info(
    device: Optional[str] = typer.Option(None, "--device", "-d", help="Target device ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Get Android device build information."""
    try:
        from android.adb import ADBManager
        
        adb = ADBManager()
        build_info = adb.get_build_info(device_id=device)
        
        if json_output:
            import json
            console.print(json.dumps(build_info))
        else:
            table = Table(title="📱 Device Build Information")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="white")
            
            for key, value in build_info.items():
                table.add_row(key, str(value))
            console.print(table)
            
    except ImportError:
        console.print("❌ Android ADB module not available")
    except Exception as e:
        console.print(f"❌ Error: {e}")

@android_app.command()
def fastboot(
    action: str = typer.Argument(..., help="Fastboot action (flash, boot, reboot, etc.)"),
    target: Optional[str] = typer.Argument(None, help="Target partition or file"),
    device: Optional[str] = typer.Option(None, "--device", "-d", help="Target device ID")
):
    """Execute fastboot commands."""
    try:
        from android.fastboot import FastbootManager
        
        fastboot = FastbootManager()
        console.print(f"⚡ Executing fastboot {action}...")
        
        result = fastboot.execute(action, target, device_id=device)
        
        if result.success:
            console.print("✅ Fastboot command completed")
            if result.output:
                console.print(result.output)
        else:
            console.print(f"❌ Fastboot failed: {result.error}")
            
    except ImportError:
        console.print("❌ Fastboot module not available")
    except Exception as e:
        console.print(f"❌ Error: {e}")