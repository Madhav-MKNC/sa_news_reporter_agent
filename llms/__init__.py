# LLM calls

import openai
from groq import Groq, RateLimitError

from utils.colored import *

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


# llm
llm = GroqLLM()

def get_llm_response(messages, model=None):
    try:
        return llm.get_llm_response(messages, model)
    except Exception as e:
        cprint(f"[ERROR in get_llm_response]: {e}", color=Colors.Text.RED)
        return ""
