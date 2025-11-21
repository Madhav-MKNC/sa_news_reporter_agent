"""
curl -X POST \
                https://llm.chutes.ai/v1/chat/completions \
                -H "Authorization: Bearer $CHUTES_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d '  {
    "model": "chutesai/Llama-4-Maverick-17B-128E-Instruct-FP8",
    "messages": [
      {
        "role": "user",
        "content": "Tell me a 250 word story."
      }
    ],
    "stream": true,
    "max_tokens": 1024,
    "temperature": 0.7
  }'
"""


import requests
import json
from typing import Optional, Dict, Any


class ChutesLLMConfig:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat_completion_url = "https://llm.chutes.ai/v1/chat/completions"


class ChutesLLMError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class Completions:
    def __init__(self, config: ChutesLLMConfig):
        self.config = config

    def create(self, **kwargs) -> Dict[str, Any]:
        """
        Create a chat completion request similar to OpenAI's interface
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        model = kwargs.get("model", '') or "chutesai/Llama-4-Maverick-17B-128E-Instruct-FP8"
        messages = kwargs.get("messages", [])
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 150)
        stream = kwargs.get("stream", False)

        # try:
        # Prepare the request payload
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if kwargs.get('debug', False):
            print(f"Making request to: {self.config.chat_completion_url}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(
            f"{self.config.chat_completion_url}",
            headers=headers,
            json=payload
        )

        if kwargs.get('debug', False):
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")

        try:
            response_json = response.json()
            if kwargs.get('debug', False):
                print(f"Response body: {json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            if kwargs.get('debug', False):
                print(f"Raw response text: {response.text}")
            raise ChutesLLMError("Failed to decode API response")

        if response.status_code >= 400:
            error_detail = response_json.get('detail', 'Unknown error')
            raise ChutesLLMError(
                f"API request failed: {error_detail}",
                status_code=response.status_code,
                response=response_json
            )

        return response_json


class Chat:
    def __init__(self, config: ChutesLLMConfig):
        self.completions = Completions(config)


class ChutesLLM:
    def __init__(self, api_key: str):
        self.config = ChutesLLMConfig(api_key=api_key)
        self.chat = Chat(self.config)
