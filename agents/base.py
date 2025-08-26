"""Base agent class and common utilities."""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import hashlib

@dataclass
class AgentRequest:
    """Standard agent request format."""
    prompt: str
    context: Dict[str, Any]
    provider: str
    model: str
    max_tokens: int = 2000
    temperature: float = 0.7

@dataclass
class AgentResponse:
    """Standard agent response format."""
    content: str
    usage: Dict[str, int]
    provider: str
    model: str
    timestamp: float
    request_id: str
    success: bool = True
    error: Optional[str] = None

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """Initialize agent with optional provider override.
        
        Args:
            provider: AI provider name (openai, openrouter, gemini)
            model: Model name override
        """
        self.provider = provider
        self.model = model
        self._client = None
        self._stats = {
            "requests": 0,
            "tokens_used": 0,
            "errors": 0,
            "cache_hits": 0
        }
        self._cache = {}  # Simple in-memory cache
    
    @property
    def name(self) -> str:
        """Agent name for identification."""
        return self.__class__.__name__
    
    @abstractmethod
    def process(self, request: AgentRequest) -> AgentResponse:
        """Process agent request and return response.
        
        Args:
            request: AgentRequest with prompt and context
            
        Returns:
            AgentResponse with generated content
        """
        pass
    
    def _get_client(self):
        """Get AI client for the configured provider."""
        if self._client is None:
            self._client = get_agent_client(self.provider)
        return self._client
    
    def _generate_request_id(self, request: AgentRequest) -> str:
        """Generate unique request ID."""
        request_data = f"{request.prompt}{request.provider}{request.model}{time.time()}"
        return hashlib.md5(request_data.encode()).hexdigest()[:8]
    
    def _cache_key(self, request: AgentRequest) -> str:
        """Generate cache key for request."""
        key_data = f"{request.prompt}{request.provider}{request.model}{request.temperature}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _check_cache(self, request: AgentRequest) -> Optional[AgentResponse]:
        """Check if response is cached."""
        cache_key = self._cache_key(request)
        if cache_key in self._cache:
            cached_response = self._cache[cache_key]
            # Check if cache is still valid (5 minutes)
            if time.time() - cached_response.timestamp < 300:
                self._stats["cache_hits"] += 1
                return cached_response
        return None
    
    def _cache_response(self, request: AgentRequest, response: AgentResponse):
        """Cache response."""
        cache_key = self._cache_key(request)
        self._cache[cache_key] = response
    
    def _update_stats(self, response: AgentResponse):
        """Update agent statistics."""
        self._stats["requests"] += 1
        if response.usage:
            self._stats["tokens_used"] += response.usage.get("total_tokens", 0)
        if not response.success:
            self._stats["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent usage statistics."""
        return {
            "agent": self.name,
            "provider": self.provider,
            **self._stats
        }

class AIClient(ABC):
    """Abstract AI client interface."""
    
    @abstractmethod
    def complete(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """Generate completion for prompt."""
        pass
    
    @abstractmethod
    def get_usage(self) -> Dict[str, int]:
        """Get token usage information."""
        pass

# Global registry for AI clients
_client_registry = {}
_usage_stats = {}

def register_client(provider: str, client: AIClient):
    """Register AI client for provider."""
    _client_registry[provider] = client

def get_agent_client(provider: Optional[str] = None) -> AIClient:
    """Get AI client for provider.
    
    Args:
        provider: Provider name or None for default
        
    Returns:
        AIClient instance
        
    Raises:
        ValueError: If provider not found or not configured
    """
    from cli.config import load_config
    
    config = load_config()
    
    # Use first available provider if none specified
    if not provider:
        for p in config.ai_providers:
            if p.enabled and p.api_key:
                provider = p.name
                break
    
    if not provider:
        raise ValueError("No AI provider configured")
    
    # Check if client is already registered
    if provider in _client_registry:
        return _client_registry[provider]
    
    # Get provider config
    provider_config = None
    for p in config.ai_providers:
        if p.name == provider:
            provider_config = p
            break
    
    if not provider_config or not provider_config.api_key:
        raise ValueError(f"Provider '{provider}' not configured")
    
    # Create and register client
    if provider == "openai":
        from .providers.openai import OpenAIClient
        client = OpenAIClient(
            api_key=provider_config.api_key,
            model=provider_config.model
        )
    elif provider == "openrouter":
        from .providers.openrouter import OpenRouterClient
        client = OpenRouterClient(
            api_key=provider_config.api_key,
            model=provider_config.model,
            base_url=provider_config.base_url
        )
    elif provider == "gemini":
        from .providers.gemini import GeminiClient
        client = GeminiClient(
            api_key=provider_config.api_key,
            model=provider_config.model
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")
    
    register_client(provider, client)
    return client

def get_usage_stats() -> Dict[str, Any]:
    """Get global usage statistics."""
    return _usage_stats.copy()

def update_usage_stats(agent_name: str, stats: Dict[str, Any]):
    """Update global usage statistics."""
    _usage_stats[agent_name] = stats

class MultiAgentOrchestrator:
    """Orchestrate multiple agents for complex tasks."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.agents = {}
        self.workflows = {}
    
    def register_agent(self, name: str, agent: BaseAgent):
        """Register agent with orchestrator."""
        self.agents[name] = agent
    
    def create_workflow(self, name: str, steps: List[Dict[str, Any]]):
        """Create multi-agent workflow.
        
        Args:
            name: Workflow name
            steps: List of workflow steps with agent and parameters
        """
        self.workflows[name] = steps
    
    def execute_workflow(
        self, 
        workflow_name: str, 
        initial_context: Dict[str, Any]
    ) -> List[AgentResponse]:
        """Execute multi-agent workflow.
        
        Args:
            workflow_name: Name of workflow to execute
            initial_context: Initial context data
            
        Returns:
            List of agent responses from workflow steps
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found")
        
        workflow = self.workflows[workflow_name]
        responses = []
        context = initial_context.copy()
        
        for step in workflow:
            agent_name = step["agent"]
            if agent_name not in self.agents:
                raise ValueError(f"Agent '{agent_name}' not registered")
            
            agent = self.agents[agent_name]
            
            # Build request
            request = AgentRequest(
                prompt=step["prompt"].format(**context),
                context=context,
                provider=step.get("provider", agent.provider),
                model=step.get("model", agent.model),
                max_tokens=step.get("max_tokens", 2000),
                temperature=step.get("temperature", 0.7)
            )
            
            # Execute step
            response = agent.process(request)
            responses.append(response)
            
            # Update context with response
            if response.success:
                context[f"{agent_name}_output"] = response.content
                
                # Parse any JSON outputs
                try:
                    json_data = json.loads(response.content)
                    context[f"{agent_name}_json"] = json_data
                except json.JSONDecodeError:
                    pass
            else:
                # Handle failure
                context[f"{agent_name}_error"] = response.error
        
        return responses
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        stats = {
            "registered_agents": len(self.agents),
            "workflows": len(self.workflows),
            "agents": {}
        }
        
        for name, agent in self.agents.items():
            stats["agents"][name] = agent.get_stats()
        
        return stats

# Global orchestrator instance
_orchestrator = MultiAgentOrchestrator()

def get_orchestrator() -> MultiAgentOrchestrator:
    """Get global orchestrator instance."""
    return _orchestrator