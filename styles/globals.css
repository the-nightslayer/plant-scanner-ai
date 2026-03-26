import os
import base64
import json
from io import BytesIO
from PIL import Image
from groq import Groq

# Generate a small 100x100 green image
img = Image.new('RGB', (100, 100), color = 'green')
buffered = BytesIO()
img.save(buffered, format="JPEG")
base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

client = Groq(api_key="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")
model = "meta-llama/llama-4-scout-17b-16e-instruct"

prompt = '''
Analyze this plant image and provide a JSON response EXACTLY with these keys:
{
    "name": "Common name of the plant",
    "health_status": "Is it healthy? If not, what is wrong? Provide specific details.",
    "maintenance": "How to maintain it (water, light, soil).",
    "garden_suitability": "Is it good for a typical garden or indoors? Why?",
    "bee_impact": "How does it impact bees and pollinators?"
}
'''

try:
    print(f"Testing {model} with a real image...")
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    print("Success:", completion.choices[0].message.content)
except Exception as e:
    print("Error:", str(e))
