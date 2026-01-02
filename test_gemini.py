#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    try:
        response = model.generate_content("Hello, can you respond with 'Gemini is working!'?")
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)
else:
    print("No API key found")