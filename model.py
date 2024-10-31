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
                        "text": (
                            "Starting a new analysis, unrelated to any previous ones…"
                            f"{prompt}\n\n" if prompt else ""
                           "Analyze the image, which may include graphical elements, and provide a concise summary "
                           "based on what is clearly visible. Focus on:\n"
                           "- **Objects and Elements**: Describe specific objects, colors, shapes, and their "
                           "positions.\n"
                           "- **Data and Trends**: If there’s a graph or chart, summarize visible data points, "
                           "trends, and any relevant labels.\n"
                           "- **Avoid Assumptions**: Do not make assumptions or interpretations about unseen "
                           "elements or context. Stick to observable details only.\n"
                           "\n"
                           "Provide a clear and factual description without unverified information."
                           f"\n\n**Reminder**: Ensure the summary aligns with the additional instruction: '{prompt}'. "
                           f"If you are unable to follow this additional instruction, specify at the start of your response."
                            if prompt else ""
                        )

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


async def async_summarize_image(image_url: str, inference_prompt: str) -> str:
    loop = asyncio.get_event_loop()
    extracted_text = await loop.run_in_executor(None, summarize_image, image_url, inference_prompt)
    return extracted_text


async def process_images(image_urls, inference_prompt):
    tasks = [async_summarize_image(image_url, inference_prompt) for image_url in image_urls]

    extracted_texts = await asyncio.gather(*tasks)
    extracted_images = list(zip(image_urls, extracted_texts))

    return extracted_images
