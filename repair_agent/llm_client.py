# llm_client.py

import google.generativeai as genai
import re
import config

def call_llm_propose_patch(file_path: str, file_contents: str, failing_test: str, trace: str) -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Configure Gemini
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.MODEL)

    system = (
        "You are an expert software engineer. Given a failing test, file contents and a traceback, "
        "propose a minimal fix. Return ONLY a unified-diff patch wrapped between markers."
    )
    user = f"""
Failing test: {failing_test}
Traceback:
{trace}

File path: {file_path}
File contents:
{file_contents}

Provide a minimal fix. Output exactly:
{config.PATCH_MARKER_START}
<unified-diff text>
{config.PATCH_MARKER_END}
"""

    prompt = f"{system}\n\n{user}"
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1200,
                temperature=0.0,
            )
        )
        text = response.text
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini API: {e}")
    
    m = re.search(rf"{config.PATCH_MARKER_START}\s*(.*?)\s*{config.PATCH_MARKER_END}", text, re.S)
    if not m:
        raise RuntimeError("Did not receive patch between markers. Response:\n" + text)
    return m.group(1).strip()