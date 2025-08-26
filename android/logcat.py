"""Android logcat wrapper and log analysis tools."""

import subprocess
import re
import time
from typing import List, Dict, Optional, Iterator, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class LogLevel(Enum):
    """Android log levels."""
    VERBOSE = "V"
    DEBUG = "D"
    INFO = "I"
    WARNING = "W" 
    ERROR = "E"
    FATAL = "F"
    SILENT = "S"

@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    pid: int
    tid: int
    level: LogLevel
    tag: str
    message: str
    raw_line: str

@dataclass
class LogStats:
    """Log statistics."""
    total_lines: int
    by_level: Dict[LogLevel, int]
    by_tag: Dict[str, int]
    error_count: int
    warning_count: int
    crash_indicators: List[str]

class LogcatManager:
    """Android logcat operations manager."""
    
    def __init__(self, device_id: Optional[str] = None, adb_path: str = "adb"):
        """Initialize logcat manager.
        
        Args:
            device_id: Target device ID
            adb_path: Path to adb binary
        """
        self.device_id = device_id
        self.adb_path = adb_path
        self._log_format = "threadtime"  # Default format
    
    def _build_logcat_command(
        self, 
        filter_spec: Optional[str] = None,
        buffer: Optional[str] = None,
        since: Optional[str] = None,
        count: Optional[int] = None
    ) -> List[str]:
        """Build logcat command with options.
        
        Args:
            filter_spec: Log filter specification (tag:level)
            buffer: Log buffer (main, radio, events, system)
            since: Show logs since time/date
            count: Maximum number of lines
            
        Returns:
            Complete logcat command as list
        """
        cmd = [self.adb_path]
        
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        
        cmd.extend(["logcat", "-v", self._log_format])
        
        if buffer:
            cmd.extend(["-b", buffer])
        
        if since:
            cmd.extend(["-t", since])
        
        if count:
            cmd.extend(["-m", str(count)])
        
        if filter_spec:
            cmd.append(filter_spec)
        
        return cmd
    
    def capture(
        self, 
        duration: int = 30,
        filter_tag: Optional[str] = None,
        level: Optional[LogLevel] = None,
        buffer: Optional[str] = None,
        save_to_file: Optional[str] = None
    ) -> str:
        """Capture logs for specified duration.
        
        Args:
            duration: Capture duration in seconds
            filter_tag: Filter by specific tag
            level: Minimum log level to capture
            buffer: Log buffer to read from
            save_to_file: Save logs to file
            
        Returns:
            Captured log content as string
        """
        filter_spec = None
        if filter_tag and level:
            filter_spec = f"{filter_tag}:{level.value}"
        elif filter_tag:
            filter_spec = f"{filter_tag}:V"  # Verbose level for tag
        elif level:
            filter_spec = f"*:{level.value}"  # All tags at level
        
        cmd = self._build_logcat_command(filter_spec, buffer)
        
        try:
            # Clear existing logs first
            clear_cmd = self._build_logcat_command()
            clear_cmd.append("-c")
            subprocess.run(clear_cmd, capture_output=True)
            
            # Start capturing
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            logs = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                if process.poll() is not None:
                    break
                
                try:
                    line = process.stdout.readline()
                    if line:
                        logs.append(line.strip())
                        if save_to_file:
                            with open(save_to_file, 'a') as f:
                                f.write(line)
                except Exception:
                    break
            
            process.terminate()
            process.wait(timeout=5)
            
            return '\n'.join(logs)
            
        except Exception as e:
            raise RuntimeError(f"Failed to capture logs: {e}")
    
    def stream(
        self, 
        filter_tag: Optional[str] = None,
        level: Optional[LogLevel] = None,
        buffer: Optional[str] = None
    ) -> Iterator[str]:
        """Stream logs in real-time.
        
        Args:
            filter_tag: Filter by specific tag
            level: Minimum log level
            buffer: Log buffer to read from
            
        Yields:
            Log lines as they arrive
        """
        filter_spec = None
        if filter_tag and level:
            filter_spec = f"{filter_tag}:{level.value}"
        elif filter_tag:
            filter_spec = f"{filter_tag}:V"
        elif level:
            filter_spec = f"*:{level.value}"
        
        cmd = self._build_logcat_command(filter_spec, buffer)
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                yield line.strip()
                
        except KeyboardInterrupt:
            process.terminate()
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to stream logs: {e}")
    
    def parse_log_line(self, line: str) -> Optional[LogEntry]:
        """Parse a single log line into structured format.
        
        Args:
            line: Raw log line
            
        Returns:
            LogEntry object or None if parsing fails
        """
        # Threadtime format: MM-DD HH:MM:SS.mmm PID TID L TAG: message
        pattern = r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+([VDIWEFS])\s+([^:]+):\s*(.*)'
        
        match = re.match(pattern, line)
        if not match:
            return None
        
        timestamp, pid_str, tid_str, level_str, tag, message = match.groups()
        
        try:
            level = LogLevel(level_str)
        except ValueError:
            level = LogLevel.VERBOSE
        
        return LogEntry(
            timestamp=timestamp,
            pid=int(pid_str),
            tid=int(tid_str),
            level=level,
            tag=tag.strip(),
            message=message.strip(),
            raw_line=line
        )
    
    def analyze_logs(self, log_content: str) -> LogStats:
        """Analyze log content and generate statistics.
        
        Args:
            log_content: Raw log content
            
        Returns:
            LogStats with analysis results
        """
        lines = log_content.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        
        by_level = {level: 0 for level in LogLevel}
        by_tag = {}
        error_count = 0
        warning_count = 0
        crash_indicators = []
        
        # Common crash/error patterns
        crash_patterns = [
            r'FATAL EXCEPTION',
            r'AndroidRuntime.*FATAL',
            r'SIGSEGV',
            r'SIGABRT', 
            r'Native crash',
            r'tombstone',
            r'ANR in',
            r'Application Not Responding',
            r'OutOfMemoryError',
            r'StackOverflowError'
        ]
        
        for line in lines:
            if not line.strip():
                continue
                
            entry = self.parse_log_line(line)
            if not entry:
                continue
            
            # Count by level
            by_level[entry.level] += 1
            
            # Count by tag
            if entry.tag in by_tag:
                by_tag[entry.tag] += 1
            else:
                by_tag[entry.tag] = 1
            
            # Count errors and warnings
            if entry.level == LogLevel.ERROR:
                error_count += 1
            elif entry.level == LogLevel.WARNING:
                warning_count += 1
            
            # Check for crash indicators
            for pattern in crash_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    crash_indicators.append(line.strip())
                    break
        
        # Sort tags by frequency
        by_tag = dict(sorted(by_tag.items(), key=lambda x: x[1], reverse=True))
        
        return LogStats(
            total_lines=total_lines,
            by_level=by_level,
            by_tag=by_tag,
            error_count=error_count,
            warning_count=warning_count,
            crash_indicators=crash_indicators
        )
    
    def filter_by_package(
        self, 
        package_name: str, 
        log_content: str
    ) -> str:
        """Filter logs by package name.
        
        Args:
            package_name: Android package name
            log_content: Raw log content
            
        Returns:
            Filtered log content
        """
        # Get PID for the package
        pid_cmd = self._build_logcat_command()
        pid_cmd = [self.adb_path]
        if self.device_id:
            pid_cmd.extend(["-s", self.device_id])
        pid_cmd.extend(["shell", "pidof", package_name])
        
        try:
            result = subprocess.run(pid_cmd, capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                return ""  # Package not running
            
            pid = result.stdout.strip()
            
        except Exception:
            return ""
        
        # Filter logs by PID
        filtered_lines = []
        for line in log_content.split('\n'):
            entry = self.parse_log_line(line)
            if entry and str(entry.pid) == pid:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def get_crash_logs(self, since_minutes: int = 60) -> str:
        """Get recent crash-related logs.
        
        Args:
            since_minutes: Look back this many minutes
            
        Returns:
            Crash-related log content
        """
        since_time = f"{since_minutes}m ago"
        
        # Filter for potential crash indicators
        crash_filter = "*:E AndroidRuntime:D System.err:V"
        
        cmd = self._build_logcat_command(crash_filter, since=since_time)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""
    
    def clear_logs(self) -> bool:
        """Clear all log buffers.
        
        Returns:
            True if successful, False otherwise
        """
        cmd = self._build_logcat_command()
        cmd.append("-c")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_buffer_sizes(self) -> Dict[str, Dict[str, Any]]:
        """Get log buffer size information.
        
        Returns:
            Dictionary with buffer size info
        """
        buffers = ["main", "system", "radio", "events", "crash"]
        buffer_info = {}
        
        for buffer in buffers:
            cmd = self._build_logcat_command(buffer=buffer)
            cmd.extend(["-g"])  # Get buffer size
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # Parse output: "main: ring buffer is 256Kb (255Kb consumed), max entry is 5120b, max payload is 4068b"
                    output = result.stdout.strip()
                    size_match = re.search(r'(\d+)Kb.*\((\d+)Kb consumed\)', output)
                    if size_match:
                        buffer_info[buffer] = {
                            "total_size": f"{size_match.group(1)}Kb",
                            "used_size": f"{size_match.group(2)}Kb",
                            "available": result.returncode == 0
                        }
                    else:
                        buffer_info[buffer] = {"available": True}
                else:
                    buffer_info[buffer] = {"available": False}
            except Exception:
                buffer_info[buffer] = {"available": False}
        
        return buffer_info
    
    def export_logs(
        self, 
        output_file: str,
        format_type: str = "text",
        filter_spec: Optional[str] = None,
        since: Optional[str] = None
    ) -> bool:
        """Export logs to file.
        
        Args:
            output_file: Output file path
            format_type: Export format (text, csv, json)
            filter_spec: Log filter specification
            since: Export logs since time
            
        Returns:
            True if successful, False otherwise
        """
        cmd = self._build_logcat_command(filter_spec, since=since)
        
        try:
            if format_type == "json":
                # Custom JSON export
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    logs = []
                    for line in result.stdout.split('\n'):
                        entry = self.parse_log_line(line)
                        if entry:
                            logs.append({
                                "timestamp": entry.timestamp,
                                "pid": entry.pid,
                                "tid": entry.tid,
                                "level": entry.level.value,
                                "tag": entry.tag,
                                "message": entry.message
                            })
                    
                    import json
                    with open(output_file, 'w') as f:
                        json.dump(logs, f, indent=2)
                    return True
            else:
                # Direct export to file
                with open(output_file, 'w') as f:
                    result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=60)
                    return result.returncode == 0
        except Exception:
            return False
        
        return False