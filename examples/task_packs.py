"""Task packs - predefined workflows for common Android development tasks."""

import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.code_gen import CodeGenerator
from agents.code_fix import CodeFixer
from agents.log_analyzer import LogAnalyzer

class TaskPack:
    """Base class for task packs."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.steps = []
        self.context = {}
    
    def add_step(self, name: str, func, **kwargs):
        """Add a step to the task pack."""
        self.steps.append({
            "name": name,
            "function": func,
            "kwargs": kwargs
        })
    
    def execute(self, project_path: Optional[Path] = None) -> Dict[str, Any]:
        """Execute all steps in the task pack."""
        results = {
            "task_pack": self.name,
            "project_path": str(project_path) if project_path else None,
            "steps": [],
            "success": True,
            "start_time": time.time()
        }
        
        try:
            for step in self.steps:
                step_result = self._execute_step(step, project_path)
                results["steps"].append(step_result)
                
                if not step_result["success"]:
                    results["success"] = False
                    break
                    
        except Exception as e:
            results["success"] = False
            results["error"] = str(e)
        
        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - results["start_time"]
        
        return results
    
    def _execute_step(self, step: Dict[str, Any], project_path: Optional[Path]) -> Dict[str, Any]:
        """Execute a single step."""
        step_result = {
            "name": step["name"],
            "start_time": time.time(),
            "success": False,
            "output": "",
            "error": ""
        }
        
        try:
            kwargs = step["kwargs"].copy()
            if project_path and "project_path" not in kwargs:
                kwargs["project_path"] = project_path
                
            output = step["function"](**kwargs)
            
            step_result["success"] = True
            step_result["output"] = output
            
        except Exception as e:
            step_result["error"] = str(e)
        
        step_result["end_time"] = time.time()
        step_result["duration"] = step_result["end_time"] - step_result["start_time"]
        
        return step_result

# Task Pack Implementations

def android_project_setup(project_path: Path) -> str:
    """Set up new Android project structure."""
    if not project_path.exists():
        project_path.mkdir(parents=True)
    
    # Create basic Android project structure
    dirs_to_create = [
        "app/src/main/java",
        "app/src/main/kotlin", 
        "app/src/main/res/layout",
        "app/src/main/res/values",
        "app/src/test/java",
        "app/src/androidTest/java",
        "gradle/wrapper"
    ]
    
    for dir_path in dirs_to_create:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    return f"Created Android project structure in {project_path}"

def generate_main_activity(project_path: Path) -> str:
    """Generate MainActivity for Android project."""
    generator = CodeGenerator()
    
    activity_code = generator.generate_android_activity(
        activity_name="MainActivity",
        features=[
            "Simple UI with RecyclerView",
            "ViewBinding support", 
            "ViewModel integration",
            "Basic navigation"
        ],
        use_viewbinding=True
    )
    
    # Save to project
    kotlin_dir = project_path / "app/src/main/kotlin"
    kotlin_dir.mkdir(parents=True, exist_ok=True)
    
    with open(kotlin_dir / "MainActivity.kt", "w") as f:
        f.write(activity_code)
    
    return f"Generated MainActivity.kt in {kotlin_dir}"

def generate_gradle_files(project_path: Path) -> str:
    """Generate Gradle build files."""
    generator = CodeGenerator()
    
    # App-level build.gradle
    app_gradle = generator.generate_gradle_script(
        dependencies=[
            "androidx.core:core-ktx",
            "androidx.lifecycle:lifecycle-runtime-ktx",
            "androidx.activity:activity-compose",
            "androidx.compose.ui:ui",
            "androidx.compose.ui:ui-tooling-preview",
            "androidx.compose.material3:material3"
        ],
        android_config={
            "compile_sdk": 34,
            "min_sdk": 24,
            "target_sdk": 34
        }
    )
    
    app_dir = project_path / "app"
    app_dir.mkdir(exist_ok=True)
    
    with open(app_dir / "build.gradle.kts", "w") as f:
        f.write(app_gradle)
    
    return f"Generated build.gradle.kts in {app_dir}"

def fix_android_code(project_path: Path) -> str:
    """Fix common issues in Android code."""
    fixer = CodeFixer()
    results = []
    
    # Find Kotlin and Java files
    code_files = []
    for ext in ["*.kt", "*.java"]:
        code_files.extend(project_path.rglob(ext))
    
    for file_path in code_files[:10]:  # Limit to 10 files
        try:
            with open(file_path, 'r') as f:
                original_code = f.read()
            
            fixed_code = fixer.fix(
                original_code, 
                str(file_path),
                context={"android_project": True}
            )
            
            # Save fixed code
            with open(file_path, 'w') as f:
                f.write(fixed_code)
            
            results.append(f"Fixed: {file_path.name}")
            
        except Exception as e:
            results.append(f"Error fixing {file_path.name}: {e}")
    
    return f"Fixed {len(results)} files: {', '.join(results)}"

def analyze_build_logs(project_path: Path) -> str:
    """Analyze Android build logs for issues."""
    analyzer = LogAnalyzer()
    
    # Look for build logs
    log_files = list(project_path.rglob("*.log"))
    if not log_files:
        return "No log files found for analysis"
    
    results = []
    for log_file in log_files[:3]:  # Analyze up to 3 log files
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            analysis = analyzer.analyze(
                log_content,
                log_type="build",
                context={"android_project": True}
            )
            
            results.append(f"Analyzed {log_file.name}: {len(analysis)} characters")
            
        except Exception as e:
            results.append(f"Error analyzing {log_file.name}: {e}")
    
    return f"Analyzed logs: {', '.join(results)}"

def run_android_tests(project_path: Path) -> str:
    """Run Android tests if available."""
    try:
        # Check if gradlew exists
        gradlew_path = project_path / "gradlew"
        if not gradlew_path.exists():
            return "No gradlew found - cannot run tests"
        
        # Make gradlew executable
        gradlew_path.chmod(0o755)
        
        # Run tests
        result = subprocess.run(
            [str(gradlew_path), "test"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return f"Tests passed successfully: {result.stdout[-200:]}"
        else:
            return f"Tests failed: {result.stderr[-200:]}"
            
    except subprocess.TimeoutExpired:
        return "Tests timed out after 5 minutes"
    except Exception as e:
        return f"Error running tests: {e}"

def create_codex_integration(project_path: Path) -> str:
    """Create Codex CLI integration files."""
    codex_md_content = """# Android Project Codex Integration

## Project Type
Android mobile application

## Key Technologies
- Kotlin for Android development
- Android Jetpack libraries
- ViewBinding for UI
- Architecture Components (ViewModel, LiveData)

## Development Guidelines
- Follow Android coding conventions
- Use Kotlin coroutines for async operations
- Implement proper error handling
- Follow Material Design principles
- Use dependency injection where appropriate

## Common Tasks
- Generate new Activities and Fragments
- Create ViewBinding configurations
- Implement proper lifecycle management
- Add proper testing coverage
"""
    
    with open(project_path / "codex.md", "w") as f:
        f.write(codex_md_content)
    
    return f"Created codex.md integration file in {project_path}"

# Predefined Task Packs

def create_android_setup_pack() -> TaskPack:
    """Task pack for setting up new Android project."""
    pack = TaskPack(
        "android-setup",
        "Set up a new Android project with basic structure and files"
    )
    
    pack.add_step("Create project structure", android_project_setup)
    pack.add_step("Generate MainActivity", generate_main_activity)
    pack.add_step("Generate Gradle files", generate_gradle_files)
    pack.add_step("Create Codex integration", create_codex_integration)
    
    return pack

def create_code_quality_pack() -> TaskPack:
    """Task pack for improving code quality."""
    pack = TaskPack(
        "code-quality",
        "Analyze and fix code quality issues in Android project"
    )
    
    pack.add_step("Fix Android code issues", fix_android_code)
    pack.add_step("Analyze build logs", analyze_build_logs)
    pack.add_step("Run tests", run_android_tests)
    
    return pack

def create_maintenance_pack() -> TaskPack:
    """Task pack for project maintenance tasks."""
    pack = TaskPack(
        "maintenance", 
        "Routine maintenance tasks for Android projects"
    )
    
    pack.add_step("Fix code issues", fix_android_code)
    pack.add_step("Update Gradle dependencies", generate_gradle_files)
    pack.add_step("Run tests", run_android_tests)
    pack.add_step("Analyze logs", analyze_build_logs)
    
    return pack

def create_ci_cd_pack() -> TaskPack:
    """Task pack for CI/CD setup."""
    pack = TaskPack(
        "ci-cd",
        "Set up CI/CD pipeline for Android project"
    )
    
    def setup_github_actions(project_path: Path) -> str:
        workflows_dir = project_path / ".github/workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        ci_yml = """name: Android CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
        
    - name: Setup Android SDK
      uses: android-actions/setup-android@v2
      
    - name: Cache Gradle packages
      uses: actions/cache@v3
      with:
        path: |
          ~/.gradle/caches
          ~/.gradle/wrapper
        key: ${{ runner.os }}-gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}
        restore-keys: |
          ${{ runner.os }}-gradle-
          
    - name: Grant execute permission for gradlew
      run: chmod +x gradlew
      
    - name: Run tests
      run: ./gradlew test
      
    - name: Build APK
      run: ./gradlew assembleDebug
"""
        
        with open(workflows_dir / "ci.yml", "w") as f:
            f.write(ci_yml)
        
        return f"Created GitHub Actions CI workflow in {workflows_dir}"
    
    pack.add_step("Setup GitHub Actions", setup_github_actions)
    pack.add_step("Run initial tests", run_android_tests)
    
    return pack

# Registry of all available task packs
AVAILABLE_TASK_PACKS = {
    "android-setup": create_android_setup_pack,
    "code-quality": create_code_quality_pack,
    "maintenance": create_maintenance_pack,
    "ci-cd": create_ci_cd_pack
}

def list_available_packs() -> List[Dict[str, str]]:
    """List all available task packs."""
    packs = []
    for name, creator_func in AVAILABLE_TASK_PACKS.items():
        pack = creator_func()
        packs.append({
            "name": name,
            "description": pack.description
        })
    return packs

def execute_task_pack(pack_name: str, project_path: Optional[Path] = None) -> Dict[str, Any]:
    """Execute a task pack by name."""
    if pack_name not in AVAILABLE_TASK_PACKS:
        return {
            "success": False,
            "error": f"Task pack '{pack_name}' not found. Available packs: {list(AVAILABLE_TASK_PACKS.keys())}"
        }
    
    try:
        pack = AVAILABLE_TASK_PACKS[pack_name]()
        return pack.execute(project_path)
    except Exception as e:
        return {
            "success": False,
            "error": f"Error executing task pack '{pack_name}': {e}"
        }

def create_custom_task_pack(
    name: str,
    description: str, 
    steps: List[Dict[str, Any]]
) -> TaskPack:
    """Create a custom task pack from step definitions."""
    pack = TaskPack(name, description)
    
    for step_def in steps:
        step_name = step_def["name"]
        step_func = step_def["function"]
        step_kwargs = step_def.get("kwargs", {})
        
        pack.add_step(step_name, step_func, **step_kwargs)
    
    return pack

if __name__ == "__main__":
    # Demo execution
    print("Available Task Packs:")
    for pack in list_available_packs():
        print(f"- {pack['name']}: {pack['description']}")
    
    # Execute a sample task pack
    if len(sys.argv) > 1:
        pack_name = sys.argv[1]
        project_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()
        
        print(f"\nExecuting task pack: {pack_name}")
        result = execute_task_pack(pack_name, project_path)
        print(json.dumps(result, indent=2, default=str))