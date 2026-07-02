# EditFlow AI Build Bible
# Version: 1.0
# Date: July 02, 2026

## Repository Constitution

These are the laws of our codebase. Breaking them causes bugs, confusion, and failure.

### A. Coding Rules

1. **No Hallucinations**: Never import a library that doesn't exist. If you aren't sure, check pypi.org or the official docs first.
2. **Type Safety**: Use Python type hints (`def func(name: str) -> int:`). It helps catch errors early.
3. **Small Functions**: One function does one thing. If it's longer than 50 lines, break it up.
4. **Comments**: Explain why you did something, not what you did. The code shows what.
5. **Error Handling**: Never let the app crash silently. Catch errors and show a friendly message to the user.

### B. Architecture Rules

1. **Modular Design**: Keep AI logic, UI logic, and Video Processing logic in separate folders.
2. **Local First**: All heavy processing happens on the user's computer. No data leaves the PC unless the user explicitly chooses cloud features later.
3. **Lightweight Defaults**: Assume the user has only 4GB VRAM. Use small models (e.g., Whisper Tiny/Base) by default.

### C. GitHub Workflow

1. **Branching**: Use `main` for stable code. Create a new branch for every milestone (e.g., `feat/whisper-integration`).
2. **Commits**: Write clear messages. Bad: "fix stuff". Good: "Add silence detection using Librosa".
3. **Issues**: Every bug or feature starts as an Issue. Link Pull Requests to Issues.

### D. Testing Standards

1. **Unit Tests**: Test every individual function (e.g., "Does this function correctly remove silence from a dummy audio file?").
2. **Integration Tests**: Test how modules work together (e.g., "Does the AI agent correctly send commands to FFmpeg?").
3. **Manual QA**: Before marking a milestone complete, run the app and try to break it.

### E. Hallucination-Prevention Rules

1. **Verify Libraries**: Before using a library, confirm it is active and documented.
2. **Check APIs**: When using Adobe Premiere scripting, refer to the official Adobe ExtendScript Toolkit documentation. Do not guess method names.
3. **FFmpeg Commands**: Test FFmpeg commands in the terminal before putting them in Python code.
