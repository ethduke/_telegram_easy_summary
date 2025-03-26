import os
import yaml
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default summary prompt template
DEFAULT_SUMMARY_PROMPT = (
    "Analyze and summarize the following Telegram messages, identifying distinct conversation topics. "
    "For each topic, provide a concise summary. Format your response with clear topic headers. "
    "Here are the messages:\n\n{messages}"
)

# Default overall prompt template
DEFAULT_OVERALL_PROMPT = (
    "Create a very concise summary (maximum 5 sentences) of these Telegram chat messages. "
    "Focus on the most important discussions, projects mentioned, and key insights. "
    "Format your response with a brief summary and key points discussed. "
    "Here are the messages:\n\n{messages}"
)

# Default participant prompt template
DEFAULT_PARTICIPANT_PROMPT = (
    "Create a very brief summary (2-4 sentences maximum) of {participant}'s key messages in this chat. "
    "Focus only on substantive content about projects, opinions, or strategies they mentioned. "
    "Here are {participant}'s messages:\n\n{messages}"
)

def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml file with structured format."""
    try:
        with open('config.yaml', 'r') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        print("Warning: config.yaml file not found. Using default values.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml: {e}. Using default values.")
        return {}

# Load the configuration
CONFIG = load_config()

# Helper function to get environment variable with fallback to config or default
def get_env_or_config(env_key: str, config_section: str, config_key: str, default: Any = None) -> Any:
    """Get value from environment variable, structured config, or default in that order of preference"""
    env_value = os.getenv(env_key)
    if env_value:
        return env_value
    
    section = CONFIG.get(config_section, {})
    return section.get(config_key, default)

# Telegram API credentials from environment variables
try:
    TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
    if TELEGRAM_API_ID == 0:
        print("Warning: TELEGRAM_API_ID not set in environment variables")
except (TypeError, ValueError):
    print("Error: TELEGRAM_API_ID must be an integer")
    TELEGRAM_API_ID = 0

TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
if not TELEGRAM_API_HASH:
    print("Warning: TELEGRAM_API_HASH not set in environment variables")

# Get Telegram-related configs
TELEGRAM_STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION')
TELEGRAM_CHANNEL_ID = get_env_or_config(
    'DEFAULT_TELEGRAM_CHANNEL_ID', 
    'message_fetching', 
    'default_chat_id', 
    None
)

# Get message fetching settings
DEFAULT_MESSAGE_LIMIT = CONFIG.get('message_fetching', {}).get('default_limit', 100)

# Get AI model settings
OLLAMA_MODEL = CONFIG.get('ai', {}).get('model', 'llama2')
SUMMARY_PROMPT_TEMPLATE = CONFIG.get('ai', {}).get('summary_prompt', DEFAULT_SUMMARY_PROMPT)
OVERALL_PROMPT_TEMPLATE = CONFIG.get('ai', {}).get('overall_prompt', DEFAULT_OVERALL_PROMPT)
PARTICIPANT_PROMPT_TEMPLATE = CONFIG.get('ai', {}).get('participant_prompt', DEFAULT_PARTICIPANT_PROMPT)

# Telegram client configuration
def get_telegram_client_config() -> Dict[str, str]:
    """Get Telegram client configuration from config file"""
    return CONFIG.get('telegram_client', {})
