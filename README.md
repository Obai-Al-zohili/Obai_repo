# AI-Powered Code Repair Agent

An intelligent code repair agent that automatically detects failing tests and uses Google's Gemini AI to generate and apply fixes.

## Features

- 🤖 **CrewAI-Powered**: Uses CrewAI framework with Google Gemini for intelligent code analysis
- 🔄 **Automatic Repair**: Detects test failures, generates patches, and applies them automatically
- 📝 **Git Integration**: Commits fixes with descriptive messages
- 🎯 **Smart Parsing**: Intelligently parses pytest output to identify failing files and tests
- 📁 **Multi-file Support**: Tests and fixes all files starting with "test" in the tests/ directory
- 👥 **Agent-Based**: Uses specialized software engineering agents for code analysis and repair

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

### 3. Configure Environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash
```

### 4. Initialize Git Repository

```bash
git init
git add .
git commit -m "Initial commit"
```

## Usage

### Run the Repair Agent

```bash
python repair_agent/main.py
```

The agent will:
1. Run all tests in the `tests/` directory to detect failures
2. Parse the failure output to identify the first failing test
3. Send the failing code to Gemini AI
4. Generate a patch to fix the issue
5. Apply the patch and commit it
6. Repeat until all tests pass or max iterations reached

### Example Output

```
🤖 CrewAI: Analyzing failing test and generating patch...

╭──── 🤖 Agent Started ────╮
│                          │
│  Agent: Senior Software  │
│  Engineer                │
│                          │
│  Task: Analyze failing   │
│  test and generate       │
│  unified diff patch      │
│                          │
╰──────────────────────────╯

✅ Patch extracted successfully with markers
Patch obtained:
--- a/tests/test_math.py
+++ b/tests/test_math.py
@@ -1,4 +1,4 @@
 def add(a, b):
-    return a - b
+    return a + b
 def test_add():
     assert add(2, 3) == 5

[main abc1234] Automated fix by LLM
 1 file changed, 1 insertion(+), 1 deletion(-)
=== Iteration 2 ===
All tests passed ✅
```

## Project Structure

```
repair_agent/
├── config.py          # Configuration and environment variables
├── main.py            # Main repair agent logic
├── llm_client.py      # Gemini API integration
├── llm_client_mock.py # Mock implementation for testing
├── tester.py          # Test runner and failure parser
└── patcher.py         # Patch application logic

tests/
└── test_math.py       # Example test file

.env                   # Environment variables (create this)
requirements.txt       # Python dependencies
README.md             # This file
```

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `LLM_MODEL`: Gemini model to use (default: `gemini-2.5-flash`)

### Agent Settings

In `repair_agent/config.py`:

- `MAX_ITER`: Maximum repair iterations (default: 3)
- `PATCH_MARKER_START/END`: Markers for patch extraction

## How It Works

1. **Test Detection**: Runs pytest to identify failing tests
2. **CrewAI Analysis**: Creates a specialized software engineering agent to analyze the failure
3. **Intelligent Diagnosis**: The agent examines:
   - File contents
   - Failing test
   - Error traceback
4. **Patch Generation**: AI generates a targeted unified diff patch
5. **Patch Application**: Applies the patch using git or direct file modification
6. **Verification**: Re-runs tests to confirm the fix works

### CrewAI Agent Architecture

The repair agent uses a **Senior Software Engineer** agent with:
- **Role**: Expert in debugging and fixing code issues
- **Goal**: Analyze failing tests and generate precise code fixes
- **Backstory**: Years of experience in code analysis and repair
- **Tools**: Access to file contents, test results, and error traces

## Fallback System

The repair agent uses CrewAI with Google Gemini API. If the API fails due to quota limits or other issues, CrewAI provides detailed error reporting and retry mechanisms. Make sure you have sufficient API quota before running the agent.

### CrewAI Benefits

- **Structured Agents**: Professional agent roles and responsibilities
- **Rich UI**: Beautiful formatted output with progress tracking
- **Built-in Retry**: Automatic retry logic for API failures
- **Task Management**: Proper task definition and execution flow
- **Comprehensive Logging**: Detailed execution traces and error reporting

## Supported Models

The agent tries multiple Gemini models in order:
- `gemini-2.5-flash` (recommended, free tier)
- `gemini-flash-latest`
- `gemini-2.0-flash`
- `gemini-pro-latest`

## Troubleshooting

### API Quota Exceeded

```
❌ gemini-2.5-flash: HTTP 429
Error: You exceeded your current quota
```

**Solution**: The Gemini API has daily and per-minute rate limits on the free tier. The agent will automatically fall back to the mock implementation when quotas are exceeded. Wait for the quota to reset or upgrade to a paid plan for higher limits.

### Network Issues

```
❌ gemini-2.5-flash: Request timeout
```

**Solution**: Check your internet connection or try again later.

### Patch Application Failures

```
git apply failed: error: patch does not apply
```

**Solution**: The agent includes a fallback mechanism for simple text replacements.

## Example Test Cases

The project includes multiple test files to demonstrate the repair agent:

### `tests/test_math.py`
A simple arithmetic bug:
```python
def add(a, b):
    return a - b  # Bug: should be a + b

def test_add():
    assert add(2, 3) == 5
```

### `tests/test_cach.py`
A cache implementation with multiple bugs:
```python
class Cache:
    def get(self, key):
        # BUG: returns None even when key exists but value is falsy
        return self._store.get(key, None)

    def set(self, key, value):
        # BUG: accidentally clears the entire cache
        self._store = {}
        self._store[key] = value
```

The repair agent will automatically detect and fix both types of bugs across all test files.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.