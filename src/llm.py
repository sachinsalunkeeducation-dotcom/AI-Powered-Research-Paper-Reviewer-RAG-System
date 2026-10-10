
import os

from groq import Groq


class LLMService:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing. "
                "Set it in your environment before starting the app."
            )

        self.client = Groq(api_key=api_key)

    def generate(self, system_prompt, user_prompt):
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2500,
        )

        return response.choices[0].message.content
