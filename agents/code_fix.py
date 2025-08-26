"""Code fixing and refactoring agent."""

import re
import time
from typing import Optional, Dict, Any, List, Tuple
from .base import BaseAgent, AgentRequest, AgentResponse

class CodeFixer(BaseAgent):
    """Agent for fixing and improving code using AI."""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """Initialize code fixer agent."""
        super().__init__(provider, model)
    
    def fix(
        self, 
        code: str,
        file_path: str = "",
        issues: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.1  # Very low temperature for consistent fixes
    ) -> str:
        """Fix issues in the provided code.
        
        Args:
            code: Code to fix
            file_path: File path for context
            issues: Specific issues to address
            context: Additional context information
            temperature: Sampling temperature (very low for consistent fixes)
            
        Returns:
            Fixed code as string
        """
        # Detect language from file extension or content
        language = self._detect_language(code, file_path)
        
        # Analyze code for common issues
        detected_issues = self._analyze_code_issues(code, language)
        all_issues = list(set((issues or []) + detected_issues))
        
        # Build request
        request = AgentRequest(
            prompt=self._build_fix_prompt(code, language, all_issues, file_path, context),
            context=context or {},
            provider=self.provider or "openai",
            model=self.model or "gpt-4",
            max_tokens=4000,  # More tokens for code fixing
            temperature=temperature
        )
        
        # Process request
        response = self.process(request)
        
        if response.success:
            return response.content
        else:
            raise RuntimeError(f"Code fixing failed: {response.error}")
    
    def _detect_language(self, code: str, file_path: str) -> str:
        """Detect programming language from code or file path.
        
        Args:
            code: Code content
            file_path: File path
            
        Returns:
            Detected language name
        """
        # Check file extension
        if file_path:
            ext_map = {
                ".py": "python",
                ".kt": "kotlin", 
                ".java": "java",
                ".js": "javascript",
                ".ts": "typescript",
                ".xml": "xml",
                ".json": "json",
                ".gradle": "gradle",
                ".yml": "yaml",
                ".yaml": "yaml"
            }
            
            for ext, lang in ext_map.items():
                if file_path.endswith(ext):
                    return lang
        
        # Analyze code content for language hints
        if "fun main(" in code or "class" in code and ":" in code:
            return "kotlin"
        elif "def " in code or "import " in code and "from " in code:
            return "python"
        elif "public class" in code or "private " in code:
            return "java"
        elif "function" in code or "const " in code or "let " in code:
            return "javascript"
        elif "interface " in code and ":" in code or "type " in code:
            return "typescript"
        
        return "unknown"
    
    def _analyze_code_issues(self, code: str, language: str) -> List[str]:
        """Analyze code for common issues.
        
        Args:
            code: Code to analyze
            language: Programming language
            
        Returns:
            List of detected issues
        """
        issues = []
        
        # Common issues across languages
        if not code.strip():
            issues.append("Empty or whitespace-only code")
        
        # Language-specific analysis
        if language == "python":
            issues.extend(self._analyze_python_issues(code))
        elif language == "kotlin":
            issues.extend(self._analyze_kotlin_issues(code))
        elif language == "java":
            issues.extend(self._analyze_java_issues(code))
        elif language == "javascript" or language == "typescript":
            issues.extend(self._analyze_js_issues(code))
        
        # Generic code quality issues
        if len(code.split('\n')) > 100:
            issues.append("Large file that may need refactoring")
        
        if code.count("TODO") > 0 or code.count("FIXME") > 0:
            issues.append("Contains TODO or FIXME comments")
        
        if "print(" in code or "console.log(" in code:
            issues.append("Contains debug print statements")
        
        return issues
    
    def _analyze_python_issues(self, code: str) -> List[str]:
        """Analyze Python-specific issues."""
        issues = []
        
        # PEP 8 violations
        if re.search(r'def\s+\w+\(.*\)\s*:', code) and not re.search(r'""".+"""', code):
            issues.append("Missing docstrings in function definitions")
        
        if re.search(r'except:', code):
            issues.append("Bare except clauses (should specify exception type)")
        
        if re.search(r'import \*', code):
            issues.append("Wildcard imports (import *) should be avoided")
        
        # Common Python mistakes
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 79:
                issues.append(f"Line {i+1} exceeds 79 characters")
                break  # Only report first occurrence
        
        return issues
    
    def _analyze_kotlin_issues(self, code: str) -> List[str]:
        """Analyze Kotlin-specific issues."""
        issues = []
        
        # Kotlin conventions
        if "lateinit var" in code and "private" not in code:
            issues.append("Consider making lateinit variables private")
        
        if "!!" in code:
            issues.append("Avoid null assertion operator (!!) where possible")
        
        if re.search(r'fun\s+\w+\(.*\)\s*\{', code) and "/**" not in code:
            issues.append("Missing KDoc comments for public functions")
        
        # Android-specific issues
        if "findViewById" in code and "ViewBinding" not in code:
            issues.append("Consider using ViewBinding instead of findViewById")
        
        return issues
    
    def _analyze_java_issues(self, code: str) -> List[str]:
        """Analyze Java-specific issues."""
        issues = []
        
        if re.search(r'public\s+\w+\s+\w+\(.*\)\s*\{', code) and "/**" not in code:
            issues.append("Missing JavaDoc for public methods")
        
        if "System.out.print" in code:
            issues.append("Use proper logging instead of System.out.print")
        
        if "catch (Exception" in code:
            issues.append("Catching generic Exception is too broad")
        
        return issues
    
    def _analyze_js_issues(self, code: str) -> List[str]:
        """Analyze JavaScript/TypeScript-specific issues."""
        issues = []
        
        if "var " in code:
            issues.append("Use 'let' or 'const' instead of 'var'")
        
        if "==" in code and "===" not in code:
            issues.append("Use strict equality (===) instead of loose equality (==)")
        
        if "function(" in code and "=>" not in code:
            issues.append("Consider using arrow functions for shorter syntax")
        
        return issues
    
    def _build_fix_prompt(
        self, 
        code: str,
        language: str,
        issues: List[str],
        file_path: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive code fixing prompt."""
        
        prompt = f"""Fix the following {language} code by addressing the identified issues and improving overall quality.

Original code:
```{language}
{code}
```

File path: {file_path}

Issues to address:
{chr(10).join(f'- {issue}' for issue in issues)}

Please fix the code following these guidelines:

1. **Code Quality:**
   - Fix syntax errors and bugs
   - Improve readability and maintainability
   - Follow language-specific best practices and conventions
   - Add proper error handling where missing
   - Remove debug statements and TODO comments

2. **{language.title()}-Specific Requirements:**"""
        
        # Add language-specific requirements
        if language == "python":
            prompt += """
   - Follow PEP 8 style guide
   - Add docstrings to functions and classes
   - Use proper exception handling with specific exception types
   - Organize imports according to PEP 8"""
        
        elif language == "kotlin":
            prompt += """
   - Follow Kotlin coding conventions
   - Use nullable types appropriately
   - Prefer data classes for simple data containers
   - Use extension functions where appropriate
   - Add KDoc comments for public APIs"""
        
        elif language == "java":
            prompt += """
   - Follow Google Java Style Guide
   - Add JavaDoc for public methods and classes
   - Use proper exception handling
   - Follow naming conventions
   - Organize imports properly"""
        
        elif language in ["javascript", "typescript"]:
            prompt += """
   - Use modern ES6+ syntax
   - Use const/let instead of var
   - Use strict equality (===)
   - Add proper JSDoc/TSDoc comments
   - Use arrow functions where appropriate"""
        
        # Add context-specific requirements
        if context and context.get("android_project"):
            prompt += """

3. **Android-Specific Requirements:**
   - Follow Android development best practices
   - Use ViewBinding instead of findViewById where possible
   - Implement proper lifecycle management
   - Handle configuration changes appropriately
   - Use appropriate Android Architecture Components"""
        
        prompt += """

4. **Output Requirements:**
   - Return ONLY the fixed code without explanations
   - Preserve the original functionality while fixing issues
   - Ensure the code is production-ready
   - Make minimal changes necessary to fix the issues
   - Keep the same overall structure unless refactoring is necessary

Fixed code:"""
        
        return prompt
    
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process code fixing request."""
        request_id = self._generate_request_id(request)
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            fixed_content = client.complete(
                prompt=request.prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Clean the fixed code
            cleaned_code = self._clean_fixed_code(fixed_content)
            
            response = AgentResponse(
                content=cleaned_code,
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
    
    def _clean_fixed_code(self, content: str) -> str:
        """Clean the AI-generated fixed code."""
        # Remove markdown code blocks
        lines = content.split('\n')
        cleaned_lines = []
        in_code_block = False
        found_code_start = False
        
        for line in lines:
            if line.strip().startswith('```'):
                if not found_code_start:
                    found_code_start = True
                in_code_block = not in_code_block
                continue
            
            if in_code_block or not found_code_start:
                cleaned_lines.append(line)
        
        cleaned_code = '\n'.join(cleaned_lines).strip()
        
        # Remove common response artifacts
        artifacts_to_remove = [
            "Fixed code:",
            "Here's the fixed code:",
            "The corrected code is:",
            "```",
        ]
        
        for artifact in artifacts_to_remove:
            if cleaned_code.startswith(artifact):
                cleaned_code = cleaned_code[len(artifact):].strip()
        
        return cleaned_code
    
    def refactor_for_readability(
        self, 
        code: str, 
        file_path: str = "",
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """Refactor code for better readability and maintainability."""
        focus_areas = focus_areas or [
            "Extract methods for long functions",
            "Improve variable and function names", 
            "Add appropriate comments",
            "Simplify complex expressions",
            "Remove code duplication"
        ]
        
        return self.fix(
            code, 
            file_path, 
            issues=focus_areas,
            context={"refactoring_focus": "readability"}
        )
    
    def fix_performance_issues(
        self, 
        code: str, 
        file_path: str = "",
        profiling_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Fix performance issues in code."""
        performance_issues = [
            "Optimize loops and iterations",
            "Reduce memory allocations",
            "Use efficient data structures",
            "Cache expensive operations",
            "Remove unnecessary computations"
        ]
        
        if profiling_data:
            for hotspot in profiling_data.get("hotspots", []):
                performance_issues.append(f"Optimize hotspot: {hotspot}")
        
        return self.fix(
            code, 
            file_path,
            issues=performance_issues,
            context={"optimization_focus": "performance", "profiling_data": profiling_data}
        )
    
    def modernize_code(
        self, 
        code: str, 
        file_path: str = "",
        target_version: Optional[str] = None
    ) -> str:
        """Modernize code to use latest language features and patterns."""
        language = self._detect_language(code, file_path)
        
        modernization_issues = [
            f"Update to modern {language} syntax and features",
            "Replace deprecated APIs with current alternatives",
            "Use modern design patterns and best practices",
            "Update library usage to current versions",
            "Improve type safety and null handling"
        ]
        
        context = {
            "modernization": True,
            "target_version": target_version
        }
        
        if language == "kotlin" and "android" in file_path.lower():
            modernization_issues.extend([
                "Use Jetpack Compose if appropriate",
                "Implement Kotlin Coroutines for async operations",
                "Use Android Architecture Components"
            ])
            context["android_project"] = True
        
        return self.fix(code, file_path, issues=modernization_issues, context=context)