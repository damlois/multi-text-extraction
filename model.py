import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import asyncio

load_dotenv()

def summarize_image(image_url: str, prompt: str) -> str:
    client = InferenceClient(api_key=os.getenv("API_KEY"))

    response = client.chat_completion(
        model="meta-llama/Llama-3.2-11B-Vision-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
        max_tokens=500,
        stream=False,
    )

    response_text = ""
    if response.choices and len(response.choices) > 0:
        response_text = response.choices[0].message.content

    return response_text.strip()
