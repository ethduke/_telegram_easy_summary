# Telegram Easy Summary

A tool that creates AI-powered summaries of Telegram chat messages using Claude or Ollama models.

## Features

- Fetch messages from Telegram channels/chats
- Focus on specific users while maintaining conversation context
- Generate summaries using Claude 3.5 Sonnet (default) or Ollama models
- Analyze messages by participant with individual summaries
- Fetch only unread messages with a single flag

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure `.env` file:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_STRING_SESSION=your_session_string
   DEFAULT_TELEGRAM_CHANNEL_ID=your_default_channel_id
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

## Usage

```bash
# Basic usage with default settings
python main.py

# Custom examples
python main.py -n 200                              # Fetch 200 messages
python main.py -c @channel_name                    # Specify channel
python main.py -u @username1 @username2            # Focus on users
python main.py -o summary.txt                      # Save to file
python main.py --unread                            # Only unread messages
python main.py --model llama3                      # Use Ollama model
```

### Command Options

- `-c`, `--chat_id`: Chat ID or username (default: from config)
- `-n`, `--limit`: Max messages to fetch (default: 100)
- `-u`, `--users`: Users to focus on
- `-o`, `--output`: Output file path
- `-m`, `--model`: Model for summarization
- `--unread`: Fetch only unread messages

## Customizing Prompts

The tool uses separate markdown files for prompts located in `data/prompts/`:

- `example_prompt.md-example`: Main prompt for generating the overall conversation summary

To customize prompts:

1. Save as the relevant `.md` file in `data/prompts/`
2. Your changes will be automatically used when running the tool
3. Use template variables like `{participants}` and `{messages}` in your prompts

## Configuration

Edit `config.yaml` to change default settings like message limits, default channel, and model selection.

## License

MIT 