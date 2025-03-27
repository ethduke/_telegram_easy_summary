# Telegram Easy Summary

A Python tool that fetches messages from Telegram chats or channels and generates AI-powered summaries using Claude 3.5 Sonnet or Ollama models.

## Features

- Fetch messages from any Telegram channel or group chat
- Focus on messages from specific users while maintaining conversation context
- Generate concise AI-powered summaries using Claude 3.5 Sonnet (default) or locally hosted Ollama models
- Analyze messages by participant, providing quick individual summaries for each user
- Configurable through `config.yaml`

## Prerequisites

- Python 3.7+
- Telegram API credentials (API ID and API Hash)
- Telegram session string
- Anthropic API key for Claude 3.5 (default model)
- [Ollama](https://ollama.ai/) installed and running if using Ollama models

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/telegram-easy-summary.git
   cd telegram-easy-summary
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your `.env` file with required API credentials:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_STRING_SESSION=your_session_string
   TELEGRAM_CHANNEL_ID=your_default_channel_id
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

5. (Optional) Customize settings in `config.yaml`

## Getting Started

### Setting up a Telegram Session

To use this tool, you need a Telegram session string. You can generate one by running the main script without a session string, which will prompt you to log in.

### Basic Usage

Run the basic analyzer:
```
python main.py
```

Specify the number of messages to fetch:
```
python main.py -n 200
```

Specify a different chat ID:
```
python main.py -c @channel_name
```

Focus on specific users:
```
python main.py -u @username1 @username2
```

Save the output to a file:
```
python main.py -o summary.txt
```

### Command Line Options

- `-c`, `--chat_id`: Telegram chat ID or username (default: from config)
- `-n`, `--limit`: Maximum number of messages to fetch (default: 100)
- `-u`, `--users`: List of users to focus on (optional)
- `-o`, `--output`: Output file path (optional, output to console if not specified)
- `-s`, `--summarize`: Enable/disable summarization (default: enabled)
- `-m`, `--model`: Model to use for summarization (default: claude-3-5-sonnet, can be set to an Ollama model name)

## Example Output

Below is an example of the output you might receive when running the summarizer:

```
**Summary of Telegram Chat Messages**
The Telegram chat predominantly revolves around discussions of a specific blockchain project, with participants sharing updates, technical details, and coordination plans. Several users are actively engaged in development tasks, discussing implementation challenges and potential solutions.

**Key Points Discussed:**
1. User1 presented a demo of the project's integration with a specific blockchain platform, receiving positive feedback from other participants.
2. User2 raised concerns about current transaction handling methods and proposed improvements to the smart contract architecture.
3. User3 shared updates on a specific integration timeline and requested testing assistance from the team.

**Participant Summaries:**

User1: Actively developing the core modules for the main project and focusing on blockchain integration. Shared technical documentation and resolved several blockers that team members reported in previous meetings.

User2: Primarily focused on smart contract architecture and security aspects. Raised important questions about transaction validation procedures and contributed several pull requests addressing memory optimization issues.

User3: Coordinating integration between multiple projects, providing regular progress updates and sharing resources with the team. Mentioned upcoming deadlines and requested specific testing scenarios from other participants.

## Configuration

You can customize the behavior of the tool by editing the `config.yaml` file:

- `DEFAULT_MESSAGE_LIMIT`: Default number of messages to fetch
- `DEFAULT_TELEGRAM_CHANNEL_ID`: Default channel to analyze
- `DEFAULT_MODEL`: Default model to use for summarization (claude-3-5-sonnet by default)
- `OLLAMA_MODEL`: Default Ollama model to use if using Ollama
- `SUMMARY_PROMPT_TEMPLATE`: Prompt Template for generating summaries
- `telegram_client`: Telegram client configuration options

## Advanced Usage

### Custom Prompts

You can customize the prompts used for summarization by editing the `SUMMARY_PROMPT_TEMPLATE` in `config.yaml`. This allows you to tailor the output format and focus of the summaries to your specific needs.

### Programmatic Use

You can import and use the `TelegramMessageAnalyzer` class in your own Python scripts:

```python
from model.message_analyzer import TelegramMessageAnalyzer
import asyncio

async def example():
    analyzer = TelegramMessageAnalyzer(api_id, api_hash, session_string)
    await analyzer.start()
    
    messages, chat_title = await analyzer.fetch_messages(chat_id, limit=100)
    conversations = analyzer.organize_messages_by_conversation(messages)
    
    # Do something with the conversations
    
    await analyzer.disconnect()

asyncio.run(example())
```

## License

MIT 