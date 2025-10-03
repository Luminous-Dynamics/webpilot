# 🤖 Claude Development Companion

## The Real-Time Feedback Loop for Human-AI Development

The Claude Development Companion creates a **real feedback loop** between you and Claude during development. Claude can see your screen, run your code, test your apps, and iterate with you in real-time.

## 🎯 What Problem Does This Solve?

**Before**: 
- You describe a bug to Claude
- Claude guesses what might be wrong
- You try the suggestion
- It doesn't work because Claude couldn't see the actual problem
- Repeat...

**After**:
- You show Claude your actual screen
- Claude runs tests in your actual environment  
- Results are immediately visible to both
- Iterate until it works
- Everything is verified and documented

## ✨ Core Features

### 1. Screen Capture with Annotations
```python
companion.show_me("The error I'm seeing")
# Claude can now see exactly what you see
```

### 2. Command Execution with Verification
```python
companion.verify("npm test", should_contain="passing")
# Claude knows if the test actually passed
```

### 3. Dev Server Lifecycle Management
```python
companion.start_server("npm run dev", port=3000)
# Claude can manage your dev servers
```

### 4. Web App Testing
```python
companion.test_web("http://localhost:3000", tests=[...])
# Claude can interact with your running app
```

### 5. Complete Feedback Loop
```python
companion.feedback_loop(
    code_file="app.py",
    test_command="pytest",
    dev_server={'command': 'python app.py', 'port': 5000},
    web_url="http://localhost:5000"
)
# Everything connected in one loop
```

## 🚀 Quick Start

### Installation
```bash
pip install selenium pillow mss
```

### Basic Usage

#### Interactive Mode
```bash
python companion.py
```

This opens an interactive menu where you can:
- Show Claude your screen
- Run commands
- Start/stop servers
- Test web apps
- Run feedback loops

#### Quick Test
```bash
python companion.py --test
```

#### Feedback Example
```bash
python feedback_example.py
```

### In Your Code
```python
from claude_companion import ClaudeCompanion

with ClaudeCompanion() as companion:
    # Show Claude what you're working on
    companion.show_me("My broken component")
    
    # Run your test
    result = companion.run("npm test")
    
    # Claude sees the result and can help debug
    if not result['success']:
        companion.capture(annotation="Test failure output")
```

## 🔄 The Feedback Loop in Action

```python
# 1. You write code
companion.show_me("New feature code")

# 2. Claude suggests a test
test_result = companion.run("python test_feature.py")

# 3. If it fails, Claude can see why
if not test_result['success']:
    companion.capture(annotation="Error details")
    
# 4. You fix based on Claude's suggestion
companion.show_me("Fixed code")

# 5. Verify the fix
companion.verify("python test_feature.py", should_contain="OK")

# 6. Document success
companion.capture(annotation="Feature working!")
```

## 📁 Project Structure

```
claude_companion.py      # Main companion class
companion.py            # Interactive CLI
feedback_example.py     # Demo scenarios
.claude-companion/      # Session data
  ├── screens/         # Screenshots
  ├── outputs/         # Command outputs
  ├── tests/          # Test results
  └── feedback/       # Feedback loops
```

## 🎮 Interactive Commands

| Command | What it does | Why Claude needs it |
|---------|-------------|-------------------|
| `show_me()` | Captures screen | See exactly what you see |
| `run()` | Executes commands | Test suggestions immediately |
| `verify()` | Runs with checks | Know if fixes work |
| `start_server()` | Manages servers | Test full applications |
| `test_web()` | Browser automation | Interact with your UI |
| `feedback_loop()` | Full cycle | Complete context |

## 💡 Real Use Cases

### Debugging Together
```python
companion.show_me("The error message")
companion.run("python app.py --debug")
companion.capture(annotation="Stack trace")
# Claude now has full context to help
```

### Testing Claude's Suggestions
```python
# Claude suggests: "Try changing line 42"
companion.show_me("Line 42 before change")
# You make the change
companion.show_me("Line 42 after change")
companion.verify("python app.py", should_contain="Success")
```

### Web Development
```python
companion.start_server("npm run dev", port=3000)
companion.test_web("http://localhost:3000", [
    {"action": "screenshot", "name": "homepage"},
    {"action": "click", "element": "Login"},
    {"action": "verify", "text": "Dashboard"}
])
```

## 🔍 What Gets Captured

Each session creates:
- **Screenshots** with annotations showing what Claude should look at
- **Command outputs** with exit codes and timing
- **Test results** with pass/fail status
- **Server logs** from dev servers
- **Session JSON** with complete history

## 🎯 Best Practices

1. **Annotate screenshots** - Tell Claude what to focus on
2. **Use verify()** - Don't just run, verify expectations
3. **Save sessions** - Keep history of what worked
4. **Clean up** - Use context manager or cleanup()

## 🚫 Limitations

- Requires PIL and mss for screen capture
- Dev server management is Unix-like OS only
- Browser automation needs Selenium + driver

## 🎉 The Magic

The real magic is the **feedback loop**:

```
You code → Claude sees → Claude suggests → 
You test → Claude verifies → Iterate until perfect
```

No more guessing. No more "try this and let me know." Just real-time collaboration where both you and Claude can see exactly what's happening.

## 📝 Example Session

```bash
$ python companion.py

🤖 Claude Development Companion
📁 Workspace: /home/user/my-project

1. 📸 Show me your screen
> 1
What should I look at? The failing test
✅ Screenshot saved

2. 🏃 Run a command  
> 2
Command to run: pytest test_auth.py
❌ 1 test failed

3. 🔄 Full feedback loop
> 7
...
✅ Feedback loop complete!
```

## 🔮 Future Enhancements

- [ ] Git integration (show diffs)
- [ ] Log file monitoring
- [ ] Performance profiling
- [ ] Docker container management
- [ ] Remote development support

## 📄 License

MIT - Build amazing things together with Claude!

---

*"The best debugging happens when both developer and AI can see the same thing."*