"""
LLM Wrapper for unified model interactions
Supports Ollama and other LLM providers
"""

import asyncio
import time
import requests
from typing import List, Dict, Any, Optional
import ollama
from ollama import Options

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.configuration import LLMConfig, OutputFormat


class LLMWrapper:
    """
    Unified wrapper for LLM interactions
    Handles retries, timeouts, and error recovery
    """
    
    def __init__(self):
        self.available_models: List[str] = []
        self.model_info: Dict[str, Dict[str, Any]] = {}
        # Configure Ollama host - default to localhost for local development
        self.ollama_host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Configure ollama client with the host
        self.ollama_client = ollama.Client(host=self.ollama_host)
        
    async def initialize(self):
        """Initialize LLM wrapper and check available models"""
        await self._refresh_available_models()
    
    async def _refresh_available_models(self):
        """Refresh list of available models"""
        try:
            # Try using the ollama Python client first
            models_response = self.ollama_client.list()
            self.available_models = [model["name"] for model in models_response["models"]]
            
            # Store model info
            for model in models_response["models"]:
                self.model_info[model["name"]] = {
                    "size": model.get("size", 0),
                    "digest": model.get("digest", ""),
                    "modified_at": model.get("modified_at", ""),
                    "details": model.get("details", {})
                }
            
            # If no models available, log but don't auto-pull
            if not self.available_models:
                print("No models available. Users can pull models via the API or CLI.")
                
        except Exception as e:
            print(f"Warning: Could not refresh available models with ollama client: {e}")
            # Fallback to HTTP API
            try:
                ollama_url = f"{self.ollama_host}/api/tags"
                response = requests.get(ollama_url, timeout=10)
                response.raise_for_status()
                models_response = response.json()
                
                self.available_models = [model["name"] for model in models_response["models"]]
                
                # Store model info
                for model in models_response["models"]:
                    self.model_info[model["name"]] = {
                        "size": model.get("size", 0),
                        "digest": model.get("digest", ""),
                        "modified_at": model.get("modified_at", ""),
                        "details": model.get("details", {})
                    }
                    
                # If no models available, log but don't auto-pull
                if not self.available_models:
                    print("No models available. Users can pull models via the API or CLI.")
                    
            except Exception as e2:
                print(f"Warning: Both ollama client and HTTP API failed: {e2}")
                self.available_models = []
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return self.available_models.copy()
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        return self.model_info.get(model_name, {})
    
    async def ensure_model_available(self, model_name: str) -> bool:
        """Ensure model is available, pull if necessary"""
        if model_name in self.available_models:
            return True
        
        try:
            print(f"Pulling model: {model_name}")
            self.ollama_client.pull(model_name)
            await self._refresh_available_models()
            return model_name in self.available_models
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False
    
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        llm_config: LLMConfig,
        output_format: OutputFormat = None
    ) -> str:
        """
        Generate response using configured LLM
        """
        # Ensure model is available
        if not await self.ensure_model_available(llm_config.model_name):
            raise ValueError(f"Model {llm_config.model_name} is not available")
        
        # Determine output format
        format_str = None
        if output_format == OutputFormat.JSON:
            format_str = "json"
        elif output_format is None:
            # Check if any message suggests JSON output
            content_text = " ".join([msg.get("content", "") for msg in messages])
            if "json" in content_text.lower() or "JSON" in content_text:
                format_str = "json"
        
        # Configure options
        options = Options(
            temperature=llm_config.temperature,
            top_k=llm_config.top_k,
            top_p=llm_config.top_p,
            num_ctx=llm_config.num_ctx,
            num_predict=llm_config.max_tokens,
            repeat_penalty=llm_config.repeat_penalty,
            seed=llm_config.seed,
            mirostat_tau=llm_config.mirostat_tau
        )
        
        # Attempt generation with retries
        for attempt in range(llm_config.max_retries):
            try:
                response = await asyncio.wait_for(
                    self._call_ollama(
                        model_name=llm_config.model_name,
                        messages=messages,
                        options=options,
                        format_str=format_str
                    ),
                    timeout=llm_config.timeout
                )
                
                content = response["message"]["content"]
                
                if not content.strip():
                    raise ValueError("Empty response from model")
                
                return content
                
            except asyncio.TimeoutError:
                print(f"Attempt {attempt + 1}: Request timed out")
                if attempt == llm_config.max_retries - 1:
                    raise Exception(f"Request timed out after {llm_config.max_retries} attempts")
                
            except Exception as e:
                print(f"Attempt {attempt + 1}: {str(e)}")
                if attempt == llm_config.max_retries - 1:
                    raise Exception(f"Failed after {llm_config.max_retries} attempts: {str(e)}")
                
                # Wait before retry
                await asyncio.sleep(min(2 ** attempt, 10))
        
        raise Exception("Failed to generate response")
    
    async def _call_ollama(
        self, 
        model_name: str, 
        messages: List[Dict[str, str]], 
        options: Options,
        format_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make async call to Ollama"""
        # Ollama client is synchronous, so we need to run it in thread pool
        loop = asyncio.get_event_loop()
        
        def _sync_call():
            return self.ollama_client.chat(
                model=model_name,
                messages=messages,
                options=options,
                format=format_str,
                keep_alive="5m"  # Keep model loaded for 5 minutes
            )
        
        return await loop.run_in_executor(None, _sync_call)
    
    async def generate_batch(
        self, 
        batch_messages: List[List[Dict[str, str]]], 
        llm_config: LLMConfig,
        output_format: OutputFormat = None,
        max_concurrent: int = 3
    ) -> List[str]:
        """
        Generate responses for a batch of message lists
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def _generate_single(messages):
            async with semaphore:
                return await self.generate(messages, llm_config, output_format)
        
        tasks = [_generate_single(messages) for messages in batch_messages]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    def validate_context_length(self, messages: List[Dict[str, str]], llm_config: LLMConfig) -> bool:
        """Validate that messages fit within context window"""
        total_text = " ".join([msg.get("content", "") for msg in messages])
        estimated_tokens = self.estimate_tokens(total_text)
        
        # Leave some room for the response
        max_input_tokens = llm_config.num_ctx - (llm_config.max_tokens or 512)
        
        return estimated_tokens <= max_input_tokens
    
    def truncate_messages(self, messages: List[Dict[str, str]], llm_config: LLMConfig) -> List[Dict[str, str]]:
        """Truncate messages to fit within context window"""
        if self.validate_context_length(messages, llm_config):
            return messages
        
        # Keep system message and last user message, truncate middle content
        if len(messages) < 2:
            return messages
        
        system_msg = messages[0] if messages[0]["role"] == "system" else None
        user_msg = messages[-1] if messages[-1]["role"] == "user" else None
        
        if not user_msg:
            return messages
        
        truncated = []
        if system_msg:
            truncated.append(system_msg)
        
        # Calculate available space
        max_input_tokens = llm_config.num_ctx - (llm_config.max_tokens or 512)
        system_tokens = self.estimate_tokens(system_msg["content"]) if system_msg else 0
        user_tokens = self.estimate_tokens(user_msg["content"])
        
        available_for_user = max_input_tokens - system_tokens
        
        if user_tokens > available_for_user:
            # Truncate user message
            target_chars = available_for_user * 4  # Approximate chars per token
            truncated_content = user_msg["content"][:target_chars] + "... [truncated]"
            user_msg = {"role": "user", "content": truncated_content}
        
        truncated.append(user_msg)
        return truncated
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of LLM service"""
        try:
            # Try to get model list
            models_response = self.ollama_client.list()
            
            # Try a simple generation with a small model if available
            test_successful = False
            if self.available_models:
                try:
                    test_config = LLMConfig(
                        model_name=self.available_models[0],
                        temperature=0.0,
                        max_tokens=10,
                        timeout=10
                    )
                    
                    test_messages = [
                        {"role": "user", "content": "Say 'OK'"}
                    ]
                    
                    response = await self.generate(test_messages, test_config)
                    test_successful = len(response.strip()) > 0
                    
                except:
                    pass
            
            return {
                "status": "healthy" if test_successful else "limited",
                "available_models": len(self.available_models),
                "test_generation": test_successful,
                "models": self.available_models
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "available_models": 0,
                "test_generation": False,
                "models": []
            }