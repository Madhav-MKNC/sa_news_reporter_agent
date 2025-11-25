# LLM calls

from groq import Groq, RateLimitError
from .chutes_llm import ChutesLLM, ChutesLLMError
from app.colored import cprint, Colors

import os
from dotenv import load_dotenv
load_dotenv()


class GroqLLM:
    # model = "llama3-8b-8192"
    model = "llama-3.3-70b-versatile"
    # model = "chutesai/Mistral-Small-3.1-24B-Instruct-2503"
    # model = "chutesai/Llama-4-Maverick-17B-128E-Instruct-FP8"
    # model = "chutesai/Llama-3.1-405B-FP8"
    # model = "deepseek-ai/DeepSeek-V3-0324"
    # model = "unsloth/gemma-2-9b-it"
    # model = "Qwen/Qwen3-1.7B"

    def __init__(self):
        self.api_key_turn = 0
        self.api_keys = [
            os.getenv("GROQ_API_KEY__1__BADHAT"), 
            os.getenv("GROQ_API_KEY__2__FSOCIETY"), 
            os.getenv("GROQ_API_KEY__3__ANITON"), 
            os.getenv("GROQ_API_KEY__4__MKNC_PNP"), 
            os.getenv("GROQ_API_KEY__5__SOUTH_OFFICE"), 
            os.getenv("GROQ_API_KEY__6__GAMH"), 
            os.getenv("GROQ_API_KEY__7__MADHAVAMPIRE"), 
            os.getenv("GROQ_API_KEY__8__FERB"), 
            os.getenv("GROQ_API_KEY__9__PHINEASE"), 
            os.getenv("GROQ_API_KEY__10__AKUMARK"), 
        ]
        self.api_key = self.api_keys[self.api_key_turn]
        self.client = Groq(api_key=self.api_key)

    def get_llm_response(self, messages, model=model):
        try:
            response = self.client.chat.completions.create(
                model = model or self.model,
                messages = messages,
            )
            output = response.choices[0].message.content.strip()
            return output
        except RateLimitError as RLE:
            self.api_key_turn = (self.api_key_turn + 1) % len(self.api_keys)
            self.api_key = self.api_keys[self.api_key_turn]
            self.client = Groq(api_key=self.api_key)
            cprint(f"Rate limits error: {RLE}\n\nAPI key turn: {self.api_key_turn}", color=Colors.Text.RED)
            return self.get_llm_response(messages=messages, model=model)
        except Exception as E:
            cprint(f"[error in groq.get_llm_response] {E}", color=Colors.Text.RED)
            self.api_key_turn = (self.api_key_turn + 1) % len(self.api_keys)
            self.api_key = self.api_keys[self.api_key_turn]
            self.client = Groq(api_key=self.api_key)
            cprint(f"Exception in groq.get_llm_response: {E}\n\nAPI key turn: {self.api_key_turn}", color=Colors.Text.YELLOW)
            return self.get_llm_response(messages=messages, model=model)


class ChutesAI:
    # model = "unsloth/gemma-2-9b-it"
    model = "unsloth/gemma-3-4b-it"
    # model = "Qwen/Qwen3-30B-A3B"
    # model = "nvidia/Llama-3_1-Nemotron-Ultra-253B-v1"
    # model = "microsoft/MAI-DS-R1-FP8"
    # model = "chutesai/Mistral-Small-3.1-24B-Instruct-2503"
    # model = "chutesai/Llama-4-Maverick-17B-128E-Instruct-FP8"
    # model = "deepseek-ai/DeepSeek-V3-0324"
    # model = "Qwen/Qwen3-1.7B"
    # model = "chutesai/Llama-3.1-405B-FP8"
    # model = "openai/gpt-oss-20b"

    def __init__(self):
        self.client = ChutesLLM(api_key=os.getenv("CHUTES_API_KEY"))

    def get_llm_response(self, messages, model=model):
        response = self.client.chat.completions.create(
            messages = messages,
            model = model or self.model,
            temperature = 0.7,
            # max_tokens = 1500,
            # json_mode = True
        )

        try:
            output = response['choices'][0]['message']['content'].strip()
            # cprint(json.dumps(json.loads(output), indent=4), color=CYAN)

        except ChutesLLMError as e:
            print(f"=== ChutesLLMError in chat completion ===")
            print(f"error: {e}")
            print(f"response: {response}")
            print("==========================================")
            output = ""

        except Exception as e:
            print(f"=== Exception in chat completion error ===")
            print(f"error: {e}")
            print(f"response: {response}")
            print("===========================================")
            output = ""

        return output

    # NEW (reasoning)
    def get_reasoning_response(self, messages, model="openai/gpt-oss-20b"):
        response = self.client.reasoning.create(
            messages=messages,
            model=model or "openai/gpt-oss-20b",
            temperature=0.7,
        )

        try:
            choice = (response.get("choices") or [{}])[0]
            message = choice.get("message") or {}

            content = message.get("content")
            reasoning = message.get("reasoning_content")
            text_fallback = choice.get("text")

            # Prefer normal content; else reasoning_content; else any text fallback
            if isinstance(content, str) and content.strip():
                output = content.strip()
            elif isinstance(reasoning, str) and reasoning.strip():
                output = reasoning.strip()
            elif isinstance(text_fallback, str) and text_fallback.strip():
                output = text_fallback.strip()
            else:
                output = ""

        except ChutesLLMError as e:
            print(f"=== ChutesLLMError in reasoning completion ===")
            print(f"error: {e}")
            print(f"response: {response}")
            print("==============================================")
            output = ""

        except Exception as e:
            print(f"=== Exception in reasoning completion error ===")
            print(f"error: {e}")
            print(f"response: {response}")
            print("===============================================")
            output = ""

        return output


# llm
# llm = GroqLLM()
llm = ChutesAI()

def get_llm_response(messages, model=None):
    try:
        return llm.get_llm_response(messages, model)
    except Exception as e:
        cprint(f"[ERROR in get_llm_response]: {e}", color=Colors.Text.RED)
        return ""
