# LLM utils

import openai
import os
from utils.colored import *

from dotenv import load_dotenv
load_dotenv()


# Inference
class OpenAI:
    # model = "gpt-4"
    model = 'gpt-4o-mini'

    def __init__(self):
        self.client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))

    def get_llm_response(self, messages, model=model):
        response = self.client.chat.completions.create(
            model = model or self.model,
            messages = messages,
            temperature = 0
        )
        output = response.choices[0].message.content.strip()
        return output


# Using inference
llm = OpenAI()

def get_llm_response(messages, model=None):
    try:
        return llm.get_llm_response(messages, model)
    except Exception as e:
        cprint(f"[ERROR in get_llm_response]: {e}", color=RED)
        return ""


