"""Log analysis agent for Android and system logs."""

import re
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from .base import BaseAgent, AgentRequest, AgentResponse

class LogAnalyzer(BaseAgent):
    """Agent for analyzing logs and identifying issues."""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """Initialize log analyzer agent."""
        super().__init__(provider, model)
        self.crash_patterns = self._load_crash_patterns()
        self.error_patterns = self._load_error_patterns()
    
    def analyze(
        self, 
        logs: str,
        log_type: str = "android",
        severity_filter: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.3
    ) -> str:
        """Analyze logs and provide insights.
        
        Args:
            logs: Log content to analyze
            log_type: Type of logs (android, system, application)
            severity_filter: Filter by severity level
            context: Additional context information
            temperature: Sampling temperature
            
        Returns:
            Analysis results and recommendations
        """
        # Pre-process logs
        processed_logs = self._preprocess_logs(logs, log_type, severity_filter)
        
        # Extract key information
        log_summary = self._extract_log_summary(processed_logs, log_type)
        
        # Build analysis request
        request = AgentRequest(
            prompt=self._build_analysis_prompt(processed_logs, log_summary, log_type, context),
            context=context or {},
            provider=self.provider or "openai",
            model=self.model or "gpt-4",
            max_tokens=3000,
            temperature=temperature
        )
        
        # Process request
        response = self.process(request)
        
        if response.success:
            return response.content
        else:
            raise RuntimeError(f"Log analysis failed: {response.error}")
    
    def _load_crash_patterns(self) -> List[Dict[str, str]]:
        """Load common crash patterns for detection."""
        return [
            {
                "pattern": r"FATAL EXCEPTION",
                "type": "fatal_exception",
                "severity": "critical",
                "description": "Fatal exception in application"
            },
            {
                "pattern": r"AndroidRuntime.*FATAL",
                "type": "android_runtime_fatal",
                "severity": "critical", 
                "description": "Android runtime fatal error"
            },
            {
                "pattern": r"SIGSEGV|SIGABRT|SIGILL",
                "type": "native_crash",
                "severity": "critical",
                "description": "Native code crash"
            },
            {
                "pattern": r"ANR in.*\n.*PID: \d+",
                "type": "anr",
                "severity": "high",
                "description": "Application Not Responding"
            },
            {
                "pattern": r"OutOfMemoryError",
                "type": "oom",
                "severity": "high",
                "description": "Out of memory error"
            },
            {
                "pattern": r"StackOverflowError",
                "type": "stack_overflow",
                "severity": "high",
                "description": "Stack overflow error"
            },
            {
                "pattern": r"Process.*\(pid \d+\) has died",
                "type": "process_death",
                "severity": "medium",
                "description": "Process terminated unexpectedly"
            }
        ]
    
    def _load_error_patterns(self) -> List[Dict[str, str]]:
        """Load common error patterns."""
        return [
            {
                "pattern": r"ERROR.*SQLiteException",
                "type": "database_error",
                "severity": "high",
                "description": "Database operation failed"
            },
            {
                "pattern": r"ERROR.*NetworkException|ConnectException",
                "type": "network_error",
                "severity": "medium",
                "description": "Network connectivity issue"
            },
            {
                "pattern": r"ERROR.*FileNotFoundException",
                "type": "file_not_found",
                "severity": "medium",
                "description": "Required file not found"
            },
            {
                "pattern": r"ERROR.*SecurityException",
                "type": "security_error",
                "severity": "high",
                "description": "Security permission denied"
            },
            {
                "pattern": r"ERROR.*OutOfBoundsException",
                "type": "bounds_error",
                "severity": "medium",
                "description": "Array or collection bounds exceeded"
            },
            {
                "pattern": r"WARN.*deprecated|WARN.*obsolete",
                "type": "deprecated_api",
                "severity": "low",
                "description": "Using deprecated APIs"
            },
            {
                "pattern": r"ERROR.*timeout|TIMEOUT",
                "type": "timeout_error",
                "severity": "medium",
                "description": "Operation timed out"
            }
        ]
    
    def _preprocess_logs(
        self, 
        logs: str, 
        log_type: str,
        severity_filter: Optional[str]
    ) -> str:
        """Preprocess logs for analysis."""
        lines = logs.split('\n')
        processed_lines = []
        
        # Filter by severity if specified
        if severity_filter:
            severity_map = {
                "error": ["E", "F"],
                "warning": ["W", "E", "F"],
                "info": ["I", "W", "E", "F"],
                "debug": ["D", "I", "W", "E", "F"],
                "verbose": ["V", "D", "I", "W", "E", "F"]
            }
            
            allowed_levels = severity_map.get(severity_filter.lower(), ["E", "F"])
            
            for line in lines:
                # Android logcat format check
                if re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+([VDIWEF])', line):
                    level = re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+([VDIWEF])', line).group(1)
                    if level in allowed_levels:
                        processed_lines.append(line)
                else:
                    # Include non-standard log format lines
                    processed_lines.append(line)
        else:
            processed_lines = lines
        
        # Limit log size for analysis (keep most recent entries)
        max_lines = 500
        if len(processed_lines) > max_lines:
            processed_lines = processed_lines[-max_lines:]
        
        return '\n'.join(processed_lines)
    
    def _extract_log_summary(self, logs: str, log_type: str) -> Dict[str, Any]:
        """Extract key information from logs."""
        lines = logs.split('\n')
        summary = {
            "total_lines": len([l for l in lines if l.strip()]),
            "time_range": self._extract_time_range(lines),
            "log_levels": self._count_log_levels(lines),
            "top_tags": self._extract_top_tags(lines),
            "crashes": self._detect_crashes(logs),
            "errors": self._detect_errors(logs),
            "warnings": self._count_warnings(lines),
            "unique_processes": self._extract_processes(lines)
        }
        
        return summary
    
    def _extract_time_range(self, lines: List[str]) -> Dict[str, str]:
        """Extract time range from logs."""
        timestamps = []
        
        for line in lines:
            # Android logcat timestamp pattern
            match = re.match(r'(\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})', line)
            if match:
                timestamps.append(match.group(1))
        
        if timestamps:
            return {
                "start": timestamps[0],
                "end": timestamps[-1],
                "duration": f"{len(timestamps)} log entries"
            }
        
        return {"start": "unknown", "end": "unknown", "duration": "unknown"}
    
    def _count_log_levels(self, lines: List[str]) -> Dict[str, int]:
        """Count log entries by level."""
        levels = {"V": 0, "D": 0, "I": 0, "W": 0, "E": 0, "F": 0}
        
        for line in lines:
            match = re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+([VDIWEF])', line)
            if match:
                level = match.group(1)
                levels[level] = levels.get(level, 0) + 1
        
        return levels
    
    def _extract_top_tags(self, lines: List[str], limit: int = 10) -> List[Tuple[str, int]]:
        """Extract most frequent log tags."""
        tag_counts = {}
        
        for line in lines:
            match = re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+\d+\s+\d+\s+[VDIWEF]\s+([^:]+):', line)
            if match:
                tag = match.group(1).strip()
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort by count and return top tags
        return sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def _detect_crashes(self, logs: str) -> List[Dict[str, Any]]:
        """Detect crashes in logs."""
        crashes = []
        
        for pattern_info in self.crash_patterns:
            matches = re.finditer(pattern_info["pattern"], logs, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                # Get surrounding context
                lines = logs.split('\n')
                match_line_idx = logs[:match.start()].count('\n')
                
                context_start = max(0, match_line_idx - 3)
                context_end = min(len(lines), match_line_idx + 10)
                context = '\n'.join(lines[context_start:context_end])
                
                crashes.append({
                    "type": pattern_info["type"],
                    "severity": pattern_info["severity"],
                    "description": pattern_info["description"],
                    "match": match.group(0),
                    "context": context,
                    "line": match_line_idx + 1
                })
        
        return crashes
    
    def _detect_errors(self, logs: str) -> List[Dict[str, Any]]:
        """Detect errors in logs."""
        errors = []
        
        for pattern_info in self.error_patterns:
            matches = re.finditer(pattern_info["pattern"], logs, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                lines = logs.split('\n')
                match_line_idx = logs[:match.start()].count('\n')
                
                errors.append({
                    "type": pattern_info["type"],
                    "severity": pattern_info["severity"],
                    "description": pattern_info["description"],
                    "match": match.group(0),
                    "line": match_line_idx + 1
                })
        
        return errors
    
    def _count_warnings(self, lines: List[str]) -> int:
        """Count warning level log entries."""
        warning_count = 0
        
        for line in lines:
            if re.match(r'.*\s+W\s+', line):
                warning_count += 1
        
        return warning_count
    
    def _extract_processes(self, lines: List[str]) -> List[str]:
        """Extract unique process names/PIDs from logs."""
        processes = set()
        
        for line in lines:
            # Extract PID from Android logcat format
            match = re.match(r'\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3}\s+(\d+)', line)
            if match:
                pid = match.group(1)
                processes.add(f"PID:{pid}")
        
        return list(processes)[:20]  # Limit to top 20
    
    def _build_analysis_prompt(
        self, 
        logs: str,
        summary: Dict[str, Any], 
        log_type: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive log analysis prompt."""
        
        prompt = f"""Analyze the following {log_type} logs and provide detailed insights and recommendations.

LOG SUMMARY:
- Total lines: {summary['total_lines']}
- Time range: {summary['time_range']['start']} to {summary['time_range']['end']}
- Log levels: {summary['log_levels']}
- Top tags: {', '.join([f"{tag}({count})" for tag, count in summary['top_tags'][:5]])}
- Crashes detected: {len(summary['crashes'])}
- Errors detected: {len(summary['errors'])}
- Warnings: {summary['warnings']}

DETECTED ISSUES:"""
        
        # Add crash information
        if summary['crashes']:
            prompt += "\n\nCRITICAL CRASHES:"
            for crash in summary['crashes'][:3]:  # Limit to top 3 crashes
                prompt += f"\n- {crash['type']}: {crash['description']} (Line {crash['line']})"
        
        # Add error information
        if summary['errors']:
            prompt += "\n\nERRORS FOUND:"
            for error in summary['errors'][:5]:  # Limit to top 5 errors
                prompt += f"\n- {error['type']}: {error['description']} (Line {error['line']})"
        
        prompt += f"""

FULL LOG DATA:
```
{logs}
```

Please provide a comprehensive analysis including:

1. **EXECUTIVE SUMMARY**
   - Overall system/app health assessment
   - Critical issues that need immediate attention
   - Risk level assessment (Low/Medium/High/Critical)

2. **DETAILED ANALYSIS**
   - Root cause analysis for crashes and errors
   - Performance indicators and bottlenecks
   - Resource usage patterns (memory, CPU, network)
   - Security concerns if any

3. **ISSUE PRIORITIZATION**
   - List issues by severity (Critical → High → Medium → Low)
   - Impact assessment for each issue
   - Recommended fix timeline

4. **ACTIONABLE RECOMMENDATIONS**
   - Specific steps to resolve critical issues
   - Code changes or configuration updates needed
   - Monitoring and prevention strategies
   - Best practices to avoid similar issues

5. **PATTERNS AND TRENDS**
   - Recurring error patterns
   - Performance degradation trends
   - Unusual activity or anomalies
   - User experience impact assessment"""
        
        # Add context-specific requirements
        if context:
            if context.get("android_app"):
                prompt += """

6. **ANDROID-SPECIFIC ANALYSIS**
   - Activity lifecycle issues
   - Memory management problems
   - UI/UX performance impacts
   - Battery optimization opportunities"""
            
            if context.get("production_environment"):
                prompt += """

7. **PRODUCTION READINESS**
   - Stability assessment
   - Scalability concerns
   - Monitoring recommendations
   - Incident response priorities"""
        
        prompt += """

Format your response with clear sections and actionable insights. Use bullet points and prioritize critical issues at the top."""
        
        return prompt
    
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process log analysis request."""
        request_id = self._generate_request_id(request)
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            analysis_content = client.complete(
                prompt=request.prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            response = AgentResponse(
                content=analysis_content,
                usage=client.get_usage(),
                provider=request.provider,
                model=request.model,
                timestamp=start_time,
                request_id=request_id,
                success=True
            )
            
            self._update_stats(response)
            return response
            
        except Exception as e:
            response = AgentResponse(
                content="",
                usage={},
                provider=request.provider,
                model=request.model,
                timestamp=start_time,
                request_id=request_id,
                success=False,
                error=str(e)
            )
            
            self._update_stats(response)
            return response
    
    def analyze_crash_logs(
        self, 
        logs: str,
        crash_type: Optional[str] = None
    ) -> str:
        """Specialized crash log analysis."""
        context = {
            "crash_analysis": True,
            "crash_type": crash_type
        }
        
        return self.analyze(
            logs, 
            log_type="android_crash",
            severity_filter="error",
            context=context,
            temperature=0.1  # Lower temperature for more consistent crash analysis
        )
    
    def analyze_anr_logs(self, logs: str) -> str:
        """Specialized ANR (Application Not Responding) analysis."""
        context = {
            "anr_analysis": True,
            "focus_areas": [
                "Main thread blocking operations",
                "UI responsiveness issues", 
                "Background task management",
                "Deadlock detection"
            ]
        }
        
        return self.analyze(
            logs,
            log_type="android_anr", 
            context=context
        )
    
    def analyze_performance_logs(
        self, 
        logs: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> str:
        """Specialized performance log analysis."""
        context = {
            "performance_analysis": True,
            "metrics": metrics,
            "focus_areas": [
                "Memory usage patterns",
                "CPU utilization",
                "Network performance",
                "UI rendering performance",
                "Battery consumption"
            ]
        }
        
        return self.analyze(
            logs,
            log_type="performance",
            context=context
        )