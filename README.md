# 🐦 TwineWriter - AI Twitter Content Agent

**TwineWriter** is an intelligent LangGraph-based agent that crafts engaging Twitter content with automatic thread splitting and human-in-the-loop review.

## 🖼️ Screenshots

### Streamlit Web UI
![TwineWriter UI](/public/images/twinewriterui.png)

*Beautiful web interface for creating Twitter content - edit, preview, and export with ease!*

## ✨ Features

- 🎨 **Beautiful Streamlit UI** - Modern web interface with live editing
- 🤖 **Multiple LLM Support** - OpenAI, Anthropic, or Ollama (local)
- 🆓 **Free Option** - Use Ollama for local, private, unlimited generation
- ✂️ **Automatic Thread Splitting** - Intelligently splits long content into coherent threads
- 👤 **Human-in-the-Loop Review** - Edit, approve, or request revisions before posting
- 🎯 **Multiple Tone Styles** - Professional, educational, witty, marketing, storytelling, casual
- 📊 **Structured JSON Output** - Ready for Twitter API integration
- 💾 **Export Functionality** - Download as JSON for API integration
- 🔄 **Revision Loop** - Iterative refinement based on your feedback

## 🏗️ Architecture

TwineWriter uses a **LangGraph state machine** with the following nodes:

```
┌─────────────────────────────────────────────────────────────┐
│                        Input Node                            │
│              (Receives topic, tone, content)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Content Generation Node                      │
│            (LLM drafts tweet/thread content)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Length Checker Node                        │
│           (Checks if content fits in 280 chars)              │
└─────────────────────┬──────────────────┬────────────────────┘
                      │                  │
           ≤280 chars │                  │ >280 chars
                      │                  │
                      ▼                  ▼
              ┌──────────────┐   ┌──────────────────┐
              │ Single Tweet │   │ Thread Splitter  │
              └──────┬───────┘   │      Node        │
                     │            └────────┬─────────┘
                     │                     │
                     └──────────┬──────────┘
                                │
                                ▼
              ┌─────────────────────────────────────┐
              │      Human Review Node              │
              │   (Edit, Approve, or Revise)        │
              └──────┬──────────────────┬───────────┘
                     │                  │
              Approve│           Revise │
                     │                  │
                     ▼                  ▼
         ┌──────────────────┐   ┌──────────────────┐
         │ Finalizer Node   │   │  Revision Node   │
         │ (Output JSON)    │   │  (Re-generate)   │
         └──────────────────┘   └────────┬─────────┘
                                          │
                                          └────┐
                                               │
                                    (Loop back to Length Checker)
```

## 📦 Installation

> **⚡ Quick Start**: See [QUICKSTART.md](QUICKSTART.md) for 2-minute setup guide!

TwineWriter uses **[uv](https://github.com/astral-sh/uv)** - an extremely fast Python package manager.

### Quick Start (with uv)

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/Sonatrix/twinewriter.git
cd twinewriter

# Install dependencies (creates .venv automatically)
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### Alternative: Traditional pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package
pip install -e .
```

### Required API Keys

At least one of:
- `OPENAI_API_KEY` - For GPT-4 (recommended)
- `ANTHROPIC_API_KEY` - For Claude (fallback)

## 🚀 Usage

### Streamlit Web UI (Recommended)

```bash
# Run the web interface
uv run streamlit run app.py

# Or use the Makefile
make ui
```

Open your browser to `http://localhost:8501` and enjoy the visual interface!

### CLI Mode

```bash
# Using uv
uv run twinewriter

# Or directly with Python
uv run python twinewriter.py
```

The interactive CLI will prompt you for:
- **Topic**: What to write about
- **Tone**: Style of the content (professional, educational, witty, etc.)
- **Base Content**: (Optional) Pre-written content to expand

### Programmatic Usage

```python
from twinewriter import run_twinewriter

result = run_twinewriter(
    topic="The future of AI agents",
    tone="educational",
    base_content=""
)

print(result)  # JSON output ready for Twitter API
```

### Streamlit UI Features

- 🎨 **Beautiful Interface**: Modern, responsive design
- ✏️ **Live Editing**: Edit tweets directly in the browser
- 📊 **Real-time Stats**: Character count, tweet count
- 💾 **JSON Export**: Download content for API integration
- 👁️ **Preview Mode**: View mode and edit mode toggle
- 🎯 **Visual Feedback**: Color-coded character limits
- 🦙 **LLM Selection**: Choose OpenAI, Anthropic, or Ollama

### Example CLI Session

```
🐦 TwineWriter - AI Twitter Content Agent
==================================================================

📥 INPUT NODE: Processing user request...
   Topic: Why LangGraph is a game-changer for AI agents
   Tone: educational
   Max length: 280 chars

✍️  CONTENT GENERATION NODE: Drafting content...
   Generated 542 characters
   Preview: LangGraph is revolutionizing how we build AI agents...

📏 LENGTH CHECKER NODE: Analyzing content length...
   Content length: 542 chars
   Max tweet length: 280 chars
   ⚠️  Exceeds limit - will need thread splitting

✂️  THREAD SPLITTER NODE: Creating thread structure...
   ✅ Split into 3 tweets
      [1] 1/3 LangGraph is revolutionizing how we build AI... (278 chars)
      [2] 2/3 Unlike traditional sequential pipelines... (265 chars)
      [3] 3/3 This makes it perfect for complex workflows... (254 chars)

👤 HUMAN REVIEW NODE: Awaiting human feedback...

======================================================================
GENERATED CONTENT:
======================================================================

[1] 1/3 LangGraph is revolutionizing how we build AI...
[2] 2/3 Unlike traditional sequential pipelines...
[3] 3/3 This makes it perfect for complex workflows...

======================================================================
OPTIONS:
  [a] Approve and finalize
  [e] Edit a specific tweet
  [r] Request complete revision with feedback
  [q] Quit without saving
======================================================================

Your choice: a
✅ Content approved!

🎯 FINALIZER NODE: Preparing final output...
   ✅ Final JSON ready!
   Total tweets: 3

======================================================================
✅ FINAL OUTPUT (JSON):
======================================================================
{
  "status": "approved",
  "timestamp": "2025-11-05T11:50:00.123456",
  "topic": "Why LangGraph is a game-changer for AI agents",
  "tone": "educational",
  "thread": [
    {
      "index": 1,
      "content": "1/3 LangGraph is revolutionizing...",
      "char_count": 278
    },
    ...
  ],
  "total_tweets": 3,
  "is_thread": true
}
```

## 🤖 LLM Options

TwineWriter supports three LLM providers:

| Provider | Cost | Quality | Privacy | Setup |
|----------|------|---------|---------|-------|
| **OpenAI** | $$ | ⭐⭐⭐⭐⭐ | Cloud | API Key |
| **Anthropic** | $$ | ⭐⭐⭐⭐⭐ | Cloud | API Key |
| **Ollama** | Free | ⭐⭐⭐⭐ | Local | Install |

### Using Ollama (Free & Local)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# Configure TwineWriter
USE_OLLAMA=true
OLLAMA_MODEL=llama3.2
```

## 🎨 Tone Styles

- **professional** - Formal, business-appropriate
- **educational** - Informative, teaching-focused
- **witty** - Clever, humorous, playful
- **marketing** - Promotional, persuasive
- **storytelling** - Narrative-driven, engaging
- **casual** - Conversational, friendly

## 🔧 Advanced Features

### Human Review Options

During review, you can:

1. **[a] Approve** - Accept content and generate final JSON
2. **[e] Edit** - Modify specific tweets in the thread
3. **[r] Revise** - Request AI to regenerate with your feedback
4. **[q] Quit** - Cancel without saving

### Thread Numbering

Threads are automatically numbered in the format `1/3`, `2/3`, `3/3` to show position and total count.

### Smart Splitting

The thread splitter:
- Preserves sentence boundaries
- Maintains logical flow
- Keeps character count under 280 (with numbering)
- Handles long words by splitting at word boundaries

## 📊 Output Format

```json
{
  "status": "approved",
  "timestamp": "2025-11-05T11:50:00.123456",
  "topic": "Your topic",
  "tone": "professional",
  "thread": [
    {
      "index": 1,
      "content": "Tweet content here...",
      "char_count": 250
    }
  ],
  "total_tweets": 1,
  "is_thread": false
}
```

## 🛠️ Development

### Using Makefile

```bash
make install   # Install dependencies
make ui        # Run Streamlit web UI
make run       # Run CLI version
make example   # Run examples
make lint      # Lint with ruff
make format    # Format with black
make clean     # Clean cache files
```

### Manual Commands

```bash
# Install dev dependencies
uv sync --extra dev

# Run linting
uv run ruff check .

# Format code
uv run black .

# Add new dependencies
uv add <package-name>
```

## 🔮 Future Enhancements

- [ ] Direct Twitter API integration for posting
- [ ] Image attachment support
- [ ] Hashtag suggestions
- [ ] Engagement prediction
- [ ] A/B testing multiple versions
- [ ] Scheduled posting
- [ ] Analytics tracking

## 📝 License

MIT License - feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Please visit our [GitHub repository](https://github.com/Sonatrix/twinewriter) to:
- Open issues or submit pull requests
- View detailed documentation
- Access installation guides
- Find example code and usage patterns
- Join the community

For quick setup, check out our [Quick Start Guide](https://github.com/Sonatrix/twinewriter/blob/master/QUICKSTART.md).

---

Built with ❤️ using [LangGraph](https://langchain-ai.github.io/langgraph/) and [uv](https://github.com/astral-sh/uv)

---

📚 [View on GitHub](https://github.com/Sonatrix/twinewriter) | 📖 [Documentation](https://github.com/Sonatrix/twinewriter/wiki) | 🚀 [Quick Start](https://github.com/Sonatrix/twinewriter/blob/master/QUICKSTART.md)
