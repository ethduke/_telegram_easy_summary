#!/usr/bin/env python3
"""
Telegram Message Analyzer

This script fetches and analyzes messages from Telegram chats, with options to:
1. Focus on specific users' messages
2. Preserve conversation context
3. Generate AI-powered summaries using Ollama

Usage:
  python main.py -c CHANNEL_ID -u USERNAME1 USERNAME2 -n 200 -o output.md -f markdown
"""

import asyncio
import logging
import argparse
import sys
from typing import Union, Optional, List, Dict, Any, Tuple
from ollama import AsyncClient
from utils.config import (
    TELEGRAM_API_ID, 
    TELEGRAM_API_HASH, 
    TELEGRAM_STRING_SESSION,
    TELEGRAM_CHANNEL_ID,
    OLLAMA_MODEL,
    SUMMARY_PROMPT_TEMPLATE,
    OVERALL_PROMPT_TEMPLATE,
    PARTICIPANT_PROMPT_TEMPLATE,
    DEFAULT_MESSAGE_LIMIT
)
from utils.formatters import (
    format_results,
    write_output
)
from model.message_analyzer import TelegramMessageAnalyzer

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def generate_summary_with_ollama(
    messages_text: str, 
    model: str = OLLAMA_MODEL, 
    prompt_template: str = SUMMARY_PROMPT_TEMPLATE
) -> str:
    """
    Generate a summary using Ollama's AsyncClient.
    
    Args:
        messages_text: The text of messages to summarize
        model: The model to use for summarization
        prompt_template: The prompt template to use for the summary
        
    Returns:
        The generated summary
    """
    try:
        # Format the prompt with the message text
        prompt = prompt_template.format(messages=messages_text)
        
        # Generate summary using AsyncClient
        logger.info(f"Generating summary using {model} model via Ollama AsyncClient")
        message = {'role': 'user', 'content': prompt}
        response = await AsyncClient().chat(model=model, messages=[message])
        
        ai_summary = response['message']['content']
        logger.info("AI summary generated successfully")
        return ai_summary
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return f"Error generating summary: {str(e)}"

async def analyze_messages(
    api_id: int, 
    api_hash: str, 
    session_string: str, 
    chat_id: Union[str, int], 
    target_users: Optional[List[str]] = None, 
    limit: int = 200, 
    summarize: bool = True,
    model: str = OLLAMA_MODEL
) -> Dict[str, Any]:
    """
    Fetch and analyze messages from a Telegram chat, with optional user filtering.
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API Hash
        session_string: StringSession for resuming an existing session
        chat_id: Chat ID to analyze
        target_users: List of usernames or user IDs to focus on
        limit: Maximum number of messages to fetch
        summarize: Whether to generate a summary using Ollama
        model: Ollama model to use for summarization
        
    Returns:
        Analysis results including conversation structure and summaries
    """
    # Ensure we have a session string - if not, create a new session
    if not session_string:
        logger.warning("No session string provided. A new session will be created.")
    
    # Use async context manager for the analyzer
    async with TelegramMessageAnalyzer(api_id, api_hash, session_string) as analyzer:
        # Fetch messages
        messages, chat_title = await analyzer.fetch_messages(chat_id, limit=limit)
        
        if not messages:
            return {
                "status": "error",
                "message": "No messages found in the specified chat"
            }
        
        # Process and filter messages
        filtered_messages, extended_messages = filter_and_extend_messages(messages, target_users)
        
        # Organize messages by participant
        participants = organize_by_participant(extended_messages)
        
        # Initialize summaries
        overall_summary = None
        participant_summaries = {}
        
        if summarize and extended_messages:
            # Generate summaries
            overall_summary, participant_summaries = await generate_summaries(
                extended_messages, 
                participants, 
                model
            )
        
        # Compile results
        results = {
            "status": "success",
            "chat_title": chat_title,
            "target_users": target_users,
            "message_count": {
                "total": len(messages),
                "filtered": len(filtered_messages),
                "with_context": len(extended_messages)
            },
            "date_range": get_date_range(filtered_messages),
            "text_summaries": {
                "overall_summary": overall_summary,
                "by_participant": participant_summaries
            }
        }
        
        return results

def filter_and_extend_messages(
    messages: List[Dict[str, Any]], 
    target_users: Optional[List[str]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter messages by target users and extend with context messages.
    
    Args:
        messages: List of all messages
        target_users: Optional list of target usernames or IDs
        
    Returns:
        Tuple of (filtered messages, extended messages with context)
    """
    if not target_users:
        return messages, messages
    
    # Convert usernames to lowercase for case-insensitive matching
    target_users_lower = [u.lower().strip('@') if isinstance(u, str) else str(u) for u in target_users]
    
    # Filter messages from target users
    filtered_messages = []
    for msg in messages:
        sender_name = msg.get("sender_name", "").lower().strip('@')
        sender_id = str(msg.get("sender_id", ""))
        
        if sender_name in target_users_lower or sender_id in target_users_lower:
            filtered_messages.append(msg)
    
    # Extend filtered_messages with context messages (replies to target users)
    # Create a set of message IDs that are referenced in replies
    context_message_ids = {
        msg.get("reply_to_msg_id") 
        for msg in filtered_messages 
        if msg.get("is_reply") and msg.get("reply_to_msg_id")
    }
    
    # Add context messages from the original messages list
    filtered_ids = {msg["id"] for msg in filtered_messages}
    context_messages = [
        msg for msg in messages 
        if msg["id"] in context_message_ids and msg["id"] not in filtered_ids
    ]
    
    extended_messages = filtered_messages + context_messages
    return filtered_messages, extended_messages

def organize_by_participant(messages: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Organize messages by participant.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Dictionary mapping participant names to their messages
    """
    participants = {}
    for msg in messages:
        sender_name = msg.get("sender_name", "Unknown")
        if sender_name not in participants:
            participants[sender_name] = []
        participants[sender_name].append(msg)
    return participants

def get_date_range(messages: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    """
    Get the date range of messages.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Dictionary with earliest and latest timestamps
    """
    if not messages:
        return {"earliest": None, "latest": None}
    
    # Messages are typically in reverse chronological order
    return {
        "earliest": messages[-1]["timestamp"] if messages else None,
        "latest": messages[0]["timestamp"] if messages else None
    }

async def generate_summaries(
    extended_messages: List[Dict[str, Any]],
    participants: Dict[str, List[Dict[str, Any]]],
    model: str
) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Generate overall and participant summaries.
    
    Args:
        extended_messages: List of all messages with context
        participants: Dictionary mapping participant names to their messages
        model: Ollama model to use for summarization
        
    Returns:
        Tuple of (overall summary, participant summaries dictionary)
    """
    # Format all messages for overall summary
    all_formatted_messages = []
    for msg in sorted(extended_messages, key=lambda m: m["datetime"]):
        # Format differently based on whether it's a forwarded message
        if msg.get("is_forwarded", False):
            forwarded_from = msg.get("forwarded_from", "Unknown Source")
            formatted_message = f"[{msg['timestamp']}] {msg['sender_name']} forwarded from {forwarded_from}: {msg['text']}"
        else:
            formatted_message = f"[{msg['timestamp']}] {msg['sender_name']}: {msg['text']}"
        all_formatted_messages.append(formatted_message)
    
    all_messages_text = "\n".join(all_formatted_messages)
    
    # Generate overall summary using the template from config
    logger.info("Generating overall summary of all messages")
    overall_summary = await generate_summary_with_ollama(
        all_messages_text, 
        model,
        OVERALL_PROMPT_TEMPLATE
    )
    
    # Process participant summaries in parallel
    participant_summaries = {}
    
    async def process_participant(participant, msgs):
        # Format messages for this participant
        participant_messages = []
        for msg in sorted(msgs, key=lambda m: m["datetime"]):
            # Format differently based on whether it's a forwarded message
            if msg.get("is_forwarded", False):
                forwarded_from = msg.get("forwarded_from", "Unknown Source")
                formatted_message = f"[{msg['timestamp']}] {participant} forwarded from {forwarded_from}: {msg['text']}"
            else:
                formatted_message = f"[{msg['timestamp']}] {participant}: {msg['text']}"
            participant_messages.append(formatted_message)
        
        participant_text = "\n".join(participant_messages)
        
        # Generate prompt for this participant using the template from config
        # We need to replace {participant} but keep {messages} for later formatting
        prompt = PARTICIPANT_PROMPT_TEMPLATE.replace("{participant}", participant)
        
        # Generate summary for this participant
        try:
            summary = await generate_summary_with_ollama(
                participant_text,
                model,
                prompt
            )
            return participant, summary
        except Exception as e:
            logger.error(f"Error generating summary for {participant}: {e}")
            return participant, f"Error generating summary: {str(e)}"
    
    # Create tasks for all participants
    participant_tasks = [
        process_participant(participant, msgs) 
        for participant, msgs in participants.items() 
    ]
    
    # Execute all participant summary tasks in parallel
    logger.info(f"Generating summaries for {len(participant_tasks)} participants in parallel")
    participant_results = await asyncio.gather(*participant_tasks)
    
    # Process results
    for participant, summary in participant_results:
        if summary:
            participant_summaries[participant] = summary
            
    return overall_summary, participant_summaries

async def main():
    """Parse command line arguments and run the analyzer."""
    parser = argparse.ArgumentParser(description='Analyze and summarize Telegram messages with conversation context')
    parser.add_argument('-c', '--chat-id', type=str, default=None,
                        help=f'Chat ID to analyze (default: {TELEGRAM_CHANNEL_ID})')
    parser.add_argument('-u', '--users', type=str, nargs='+',
                        help='Target users to focus on (usernames or IDs)')
    parser.add_argument('-n', '--num-messages', type=int, default=DEFAULT_MESSAGE_LIMIT,
                        help=f'Maximum number of messages to fetch (default: {DEFAULT_MESSAGE_LIMIT})')
    parser.add_argument('-o', '--output', type=str, default=None,
                        help='Output file for results (default: print to console)')
    parser.add_argument('-f', '--format', choices=['text', 'json', 'markdown'], default='text',
                        help='Output format (default: text)')
    parser.add_argument('--no-summary', action='store_true',
                        help='Skip AI summary generation')
    parser.add_argument('--model', type=str, default=OLLAMA_MODEL,
                        help=f'Ollama model to use (default: {OLLAMA_MODEL})')
    args = parser.parse_args()
    
    # Use the default channel ID from config if not specified in args
    chat_id = args.chat_id if args.chat_id is not None else TELEGRAM_CHANNEL_ID
    
    if chat_id is None:
        logger.error("No chat ID provided and no default found in config.")
        print("Error: No chat ID provided. Please specify a chat ID with -c/--chat-id or set TELEGRAM_CHANNEL_ID in your config.")
        sys.exit(1)
    
    try:
        results = await analyze_messages(
            TELEGRAM_API_ID, 
            TELEGRAM_API_HASH, 
            TELEGRAM_STRING_SESSION, 
            chat_id,
            args.users,
            args.num_messages,
            not args.no_summary,
            args.model
        )
        
        # Format and output results
        output_text = format_results(results, args.format)
        write_output(output_text, args.output)
        
    except Exception as e:
        logger.error(f"Error analyzing messages: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 