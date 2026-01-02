# llm_client.py

import os
from crewai import Agent, Task, Crew, LLM
import config
import re

def call_llm_propose_patch(file_path: str, file_contents: str, failing_test: str, trace: str) -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    # Configure Gemini LLM for CrewAI
    gemini_llm = LLM(
        model="gemini/gemini-2.5-flash",
        api_key=config.GEMINI_API_KEY
    )

    # Create a code repair agent
    code_repair_agent = Agent(
        role="Senior Software Engineer",
        goal="Analyze failing tests and generate precise code fixes",
        backstory="""You are an expert software engineer with years of experience in debugging 
        and fixing code issues. You excel at analyzing test failures and creating minimal, 
        targeted fixes that address the root cause of the problem.""",
        llm=gemini_llm,
        verbose=True
    )

    # Create the repair task
    repair_task = Task(
        description=f"""
        Analyze this failing test and generate a unified diff patch to fix it.

        **Failing Test:** {failing_test}
        
        **Error Traceback:**
        {trace}
        
        **File Path:** {file_path}
        
        **Current File Contents:**
        ```
        {file_contents}
        ```
        
        **Instructions:**
        1. Analyze WHY the test "{failing_test}" is failing
        2. Identify the exact code that needs to be changed
        3. Generate a minimal unified diff patch that fixes ONLY this specific issue
        4. Format your response with the patch markers exactly as shown below
        
        **Required Output Format:**
        {config.PATCH_MARKER_START}
        --- a/{file_path}
        +++ b/{file_path}
        @@ -start_line,line_count +start_line,line_count @@
         unchanged_line
        -line_to_remove
        +line_to_add
         unchanged_line
        {config.PATCH_MARKER_END}
        
        Make sure your patch is complete and addresses the root cause of the test failure.
        """,
        agent=code_repair_agent,
        expected_output=f"A unified diff patch wrapped between {config.PATCH_MARKER_START} and {config.PATCH_MARKER_END} markers"
    )

    # Create and run the crew
    crew = Crew(
        agents=[code_repair_agent],
        tasks=[repair_task],
        verbose=True
    )

    try:
        print("🤖 CrewAI: Analyzing failing test and generating patch...")
        result = crew.kickoff()
        
        # Extract the patch from the result
        response_text = str(result)
        print(f"📝 CrewAI Response received (length: {len(response_text)})")
        
        # Try to extract patch with markers
        m = re.search(rf"{config.PATCH_MARKER_START}\s*(.*?)\s*{config.PATCH_MARKER_END}", response_text, re.S)
        if m:
            patch_content = m.group(1).strip()
            print("✅ Patch extracted successfully with markers")
            return patch_content
        
        # Try to extract diff block without markers
        diff_match = re.search(r'```diff\s*(.*?)\s*```', response_text, re.S)
        if diff_match:
            patch_content = diff_match.group(1).strip()
            print("✅ Patch extracted from diff block")
            return patch_content
        
        # Try to find any unified diff pattern
        diff_pattern = re.search(r'(--- a/.*?\n\+\+\+ b/.*?\n@@.*?@@.*?)(?=\n\n|\n```|\Z)', response_text, re.S)
        if diff_pattern:
            patch_content = diff_pattern.group(1).strip()
            print("✅ Patch extracted from unified diff pattern")
            return patch_content
        
        # If no patch found, show the response for debugging
        print("⚠️  No valid patch found in response")
        print("Response preview:")
        print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
        raise RuntimeError("No valid patch found in CrewAI response")
        
    except Exception as e:
        print(f"❌ CrewAI execution failed: {e}")
        raise RuntimeError(f"CrewAI failed to generate patch: {e}")