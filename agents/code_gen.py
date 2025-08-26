"""Code generation agent."""

import time
from typing import Optional, Dict, Any
from .base import BaseAgent, AgentRequest, AgentResponse

class CodeGenerator(BaseAgent):
    """Agent for generating code using AI."""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """Initialize code generator agent."""
        super().__init__(provider, model)
    
    def generate(
        self, 
        prompt: str, 
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.2  # Lower temperature for code generation
    ) -> str:
        """Generate code based on prompt and language.
        
        Args:
            prompt: Code generation prompt
            language: Programming language
            context: Additional context information
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower for more deterministic code)
            
        Returns:
            Generated code as string
        """
        # Build request
        request = AgentRequest(
            prompt=self._build_code_prompt(prompt, language, context),
            context=context or {},
            provider=self.provider or "openai",
            model=self.model or "gpt-4",
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Check cache first
        cached_response = self._check_cache(request)
        if cached_response:
            return cached_response.content
        
        # Process request
        response = self.process(request)
        
        if response.success:
            return response.content
        else:
            raise RuntimeError(f"Code generation failed: {response.error}")
    
    def _build_code_prompt(
        self, 
        prompt: str, 
        language: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive code generation prompt.
        
        Args:
            prompt: User's code request
            language: Target programming language
            context: Additional context
            
        Returns:
            Complete prompt for code generation
        """
        language_specifics = {
            "python": {
                "style": "Follow PEP 8 style guide",
                "imports": "Use standard library when possible, add imports at the top",
                "docs": "Include docstrings for functions and classes",
                "error_handling": "Use try-except blocks for error handling"
            },
            "kotlin": {
                "style": "Follow Kotlin coding conventions",
                "imports": "Use appropriate Android/Kotlin imports",
                "docs": "Include KDoc comments for public APIs", 
                "error_handling": "Use Result types or exception handling"
            },
            "java": {
                "style": "Follow Google Java Style Guide",
                "imports": "Organize imports properly",
                "docs": "Include JavaDoc for public methods",
                "error_handling": "Use proper exception handling"
            },
            "javascript": {
                "style": "Use modern ES6+ syntax",
                "imports": "Use ES6 imports/exports",
                "docs": "Include JSDoc comments",
                "error_handling": "Use try-catch and proper error handling"
            },
            "typescript": {
                "style": "Use TypeScript best practices with strict types",
                "imports": "Use proper TypeScript imports with types",
                "docs": "Include TSDoc comments with type information",
                "error_handling": "Use proper error handling with types"
            }
        }
        
        lang_info = language_specifics.get(language, language_specifics["python"])
        
        base_prompt = f"""Generate {language} code for the following request:

{prompt}

Requirements:
1. {lang_info['style']}
2. {lang_info['imports']}
3. {lang_info['docs']}
4. {lang_info['error_handling']}
5. Include error handling and edge cases
6. Make code production-ready and maintainable
7. Add comments explaining complex logic
8. Follow security best practices
"""
        
        # Add context if provided
        if context:
            if "existing_code" in context:
                base_prompt += f"\n\nExisting code context:\n```{language}\n{context['existing_code']}\n```"
            
            if "android_project" in context and context["android_project"]:
                base_prompt += "\n\nThis is for an Android project. Follow Android development best practices."
            
            if "libraries" in context:
                base_prompt += f"\n\nPreferred libraries to use: {', '.join(context['libraries'])}"
            
            if "patterns" in context:
                base_prompt += f"\n\nArchitectural patterns to follow: {', '.join(context['patterns'])}"
        
        base_prompt += f"\n\nGenerate only the {language} code without explanations. The code should be complete and ready to use."
        
        return base_prompt
    
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process code generation request.
        
        Args:
            request: AgentRequest with prompt and context
            
        Returns:
            AgentResponse with generated code
        """
        request_id = self._generate_request_id(request)
        start_time = time.time()
        
        try:
            client = self._get_client()
            
            generated_content = client.complete(
                prompt=request.prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Post-process generated code
            cleaned_code = self._clean_generated_code(generated_content)
            
            response = AgentResponse(
                content=cleaned_code,
                usage=client.get_usage(),
                provider=request.provider,
                model=request.model,
                timestamp=start_time,
                request_id=request_id,
                success=True
            )
            
            # Cache successful response
            self._cache_response(request, response)
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
    
    def _clean_generated_code(self, content: str) -> str:
        """Clean and format generated code.
        
        Args:
            content: Raw generated content
            
        Returns:
            Cleaned code
        """
        # Remove markdown code blocks if present
        lines = content.split('\n')
        cleaned_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block or not content.startswith('```'):
                cleaned_lines.append(line)
        
        # Join and clean up
        cleaned_code = '\n'.join(cleaned_lines).strip()
        
        # Remove common AI response artifacts
        artifacts_to_remove = [
            "Here's the code:",
            "Here is the code:",
            "The code is:",
            "```python",
            "```kotlin", 
            "```java",
            "```javascript",
            "```typescript",
            "```",
        ]
        
        for artifact in artifacts_to_remove:
            if cleaned_code.startswith(artifact):
                cleaned_code = cleaned_code[len(artifact):].strip()
        
        return cleaned_code
    
    def generate_android_activity(
        self, 
        activity_name: str,
        features: list,
        use_viewbinding: bool = True,
        use_fragments: bool = False
    ) -> str:
        """Generate Android Activity code.
        
        Args:
            activity_name: Name of the activity class
            features: List of features to include
            use_viewbinding: Whether to use view binding
            use_fragments: Whether to include fragment support
            
        Returns:
            Generated Kotlin Activity code
        """
        prompt = f"""Create an Android Activity named {activity_name} with the following features:
{chr(10).join(f'- {feature}' for feature in features)}

Requirements:
- Use Kotlin
- {'Use ViewBinding' if use_viewbinding else 'Use findViewById'}
- {'Include Fragment support' if use_fragments else 'No fragments needed'}
- Follow Android Architecture Components patterns
- Include proper lifecycle management
- Add error handling
"""
        
        context = {
            "android_project": True,
            "libraries": ["androidx.appcompat", "androidx.lifecycle"],
            "patterns": ["MVVM", "ViewBinding" if use_viewbinding else "findViewById"]
        }
        
        return self.generate(prompt, "kotlin", context)
    
    def generate_gradle_script(
        self, 
        dependencies: list,
        android_config: Dict[str, Any]
    ) -> str:
        """Generate Gradle build script.
        
        Args:
            dependencies: List of dependencies to include
            android_config: Android-specific configuration
            
        Returns:
            Generated Gradle script
        """
        prompt = f"""Generate an Android app-level build.gradle file with:

Dependencies to include:
{chr(10).join(f'- {dep}' for dep in dependencies)}

Android configuration:
- compileSdkVersion: {android_config.get('compile_sdk', 34)}
- minSdkVersion: {android_config.get('min_sdk', 24)}
- targetSdkVersion: {android_config.get('target_sdk', 34)}
- versionCode: {android_config.get('version_code', 1)}
- versionName: {android_config.get('version_name', '1.0')}

Use Kotlin DSL format and latest Gradle practices."""
        
        context = {
            "android_project": True,
            "libraries": ["gradle", "android-gradle-plugin"]
        }
        
        return self.generate(prompt, "kotlin", context)
    
    def generate_test_class(
        self, 
        class_to_test: str,
        test_scenarios: list,
        test_type: str = "unit"
    ) -> str:
        """Generate test class for given class.
        
        Args:
            class_to_test: Name of class to test
            test_scenarios: List of test scenarios
            test_type: Type of tests (unit, integration, ui)
            
        Returns:
            Generated test code
        """
        test_framework = {
            "unit": "JUnit 5 with Mockk",
            "integration": "JUnit 5 with TestContainers", 
            "ui": "Espresso with JUnit 4"
        }.get(test_type, "JUnit 5")
        
        prompt = f"""Generate a {test_type} test class for {class_to_test} using {test_framework}.

Test scenarios to cover:
{chr(10).join(f'- {scenario}' for scenario in test_scenarios)}

Requirements:
- Use appropriate testing annotations
- Include setup and teardown methods
- Mock external dependencies
- Test both success and failure cases
- Follow testing best practices
- Include descriptive test method names
"""
        
        context = {
            "libraries": ["junit", "mockk", "espresso"] if test_type == "ui" else ["junit", "mockk"],
            "patterns": ["AAA (Arrange-Act-Assert)", "Given-When-Then"]
        }
        
        return self.generate(prompt, "kotlin", context)