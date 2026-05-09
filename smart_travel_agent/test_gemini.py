import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

print("API KEY FOUND:", bool(API_KEY))
print("API KEY:", API_KEY[:15], "...")

try:
    from google import genai

    client = genai.Client(api_key=API_KEY)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello in one line."
    )

    print("\n===== SUCCESS =====\n")
    print(response.text)

except Exception as e:
    print("\n===== ERROR =====\n")
    print(type(e))
    print(str(e))