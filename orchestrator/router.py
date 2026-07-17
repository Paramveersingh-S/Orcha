import os
import yaml
import requests
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from .budget_tracker import BudgetTracker

load_dotenv()

class ModelRouter:
    def __init__(self, registry_path="orchestrator/provider_registry.yaml"):
        with open(registry_path, "r") as f:
            self.registry = yaml.safe_load(f)["providers"]
        self.budget_tracker = BudgetTracker()

    def get_headers(self, provider: str) -> dict:
        auth_env_var = self.registry[provider]["auth_env_var"]
        api_key = os.getenv(auth_env_var)
        if not api_key:
            raise ValueError(f"Missing API key for {provider}. Expected {auth_env_var}")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenRouter specific headers
        if provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/Paramveersingh-S/Orcha"
            headers["X-Title"] = "Autonomous Venture Factory"
            
        return headers

    def _get_fallback_chain(self, task_type: str) -> List[Dict[str, str]]:
        # Hardcoded task types based on spec 6.2
        chains = {
            "high_volume": [
                {"provider": "groq", "model": "llama-3.1-8b-instant"},
                {"provider": "openrouter", "model": "google/gemini-2.0-flash-lite-preview-02-05:free"},
                {"provider": "gemini", "model": "gemini-2.0-flash-lite-preview-02-05"}
            ],
            "reasoning_heavy": [
                {"provider": "openrouter", "model": "deepseek/deepseek-r1-distill-llama-70b:free"},
                {"provider": "groq", "model": "llama-3.3-70b-versatile"},
                {"provider": "gemini", "model": "gemini-2.0-flash"}
            ],
            "long_context": [
                {"provider": "gemini", "model": "gemini-2.0-flash"},
                {"provider": "openrouter", "model": "google/gemini-2.0-flash-lite-preview-02-05:free"}
            ],
            "code_generation": [
                {"provider": "openrouter", "model": "qwen/qwen-2.5-coder-32b-instruct:free"},
                {"provider": "groq", "model": "llama-3.3-70b-versatile"}
            ]
        }
        return chains.get(task_type, chains["reasoning_heavy"])

    def route(self, task_type: str, messages: List[Dict[str, str]], **kwargs) -> str:
        candidates = self._get_fallback_chain(task_type)
        
        for candidate in candidates:
            provider = candidate["provider"]
            model = candidate["model"]
            
            # Skip if near cap (budget tracker)
            if self.budget_tracker.is_near_cap(provider):
                print(f"Skipping {provider} as it is near cap.")
                continue

            try:
                base_url = self.registry[provider]["base_url"]
                headers = self.get_headers(provider)
                
                payload = {
                    "model": model,
                    "messages": messages,
                    **kwargs
                }

                # Google Gemini uses a different endpoint structure via OpenAI compat
                if provider == "gemini":
                    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

                response = requests.post(
                    base_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.budget_tracker.log_usage(provider)
                    return data["choices"][0]["message"]["content"]
                
                elif response.status_code == 429:
                    print(f"Rate limited on {provider} ({model}). Trying next candidate...")
                    continue
                else:
                    print(f"Error {response.status_code} from {provider} ({model}): {response.text}")
                    continue

            except Exception as e:
                print(f"Exception calling {provider} ({model}): {e}")
                continue
                
        raise Exception(f"All candidates failed for task_type: {task_type}")

# Example usage for manual test
if __name__ == "__main__":
    router = ModelRouter()
    print("Testing router with high_volume task...")
    try:
        response = router.route("high_volume", [{"role": "user", "content": "What is the capital of France? Reply in one word."}])
        print(f"Response: {response.strip()}")
        print(f"Budget Summary: {router.budget_tracker.get_summary()}")
    except Exception as e:
        print(f"Router test failed: {e}")
