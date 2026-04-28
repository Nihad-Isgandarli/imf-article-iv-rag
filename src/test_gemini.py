"""Quick smoke test: verify that the Gemini API key works."""

import os
from dotenv import load_dotenv
import google.generativeai as genai


def main() -> None:
    """Send a simple test prompt to Gemini and print the response."""
    
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env")
        return

    
    genai.configure(api_key=api_key)

    
    model = genai.GenerativeModel("gemini-2.5-flash")

   
    prompt = "In one sentence: what is an IMF Article IV consultation report?"
    print(f"Prompt: {prompt}\n")

    response = model.generate_content(prompt)
    print(f"Response: {response.text}")


if __name__ == "__main__":
    main()