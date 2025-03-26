#!/usr/bin/env python3
"""
Telegram Message Analyzer

This module provides functionality to fetch and analyze Telegram messages.
"""

import logging
import atexit
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta, timezone
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import User, Channel, PeerChannel, PeerUser, PeerChat

class TelegramMessageAnalyzer:
    """
    Telegram message analyzer that fetches and processes messages.
    """
    
    def __init__(self, api_id: int, api_hash: str, session_string: Optional[str] = None, session_name: str = "TelegramAnalyzer"):
        """
        Initialize the Telegram Message Analyzer.
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_string: StringSession for resuming an existing session
            session_name: Name for the session file if not using StringSession
        """
        self.logger = logging.getLogger("TelegramMessageAnalyzer")
        
        # Initialize Telegram client with session string if provided
        if session_string:
            self.client = TelegramClient(StringSession(session_string), api_id, api_hash)
            self.logger.info("Using provided session string")
        else:
            self.client = TelegramClient(session_name, api_id, api_hash)
            self.logger.warning("No session string provided. Using local session file.")
            
        # Register disconnect on program exit to avoid breaking the session
        atexit.register(self._disconnect)
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def start(self):
        """Start the Telegram client session"""
        await self.client.start()
        self.logger.info("Telegram client started")
    
    def _disconnect(self):
        """Disconnect the client if it's still connected (called on exit)"""
        try:
            if self.client and self.client.is_connected():
                self.client.disconnect()
                self.logger.info("Telegram client disconnected on exit")
        except Exception as e:
            self.logger.error(f"Error disconnecting client on exit: {e}")
    
    async def disconnect(self):
        """Disconnect the client manually"""
        if self.client:
            await self.client.disconnect()
            self.logger.info("Telegram client disconnected")
    
    @staticmethod
    def get_user_display_name(sender: Optional[Union[User, Channel]]) -> str:
        """
        Get a user's display name from a sender object.
        
        Args:
            sender: A Telegram User or Channel object
            
        Returns:
            The user's display name (first_name + last_name or username)
        """
        if not sender:
            return "Unknown"
        
        if isinstance(sender, User):
            if sender.username:
                return f"@{sender.username}"
            else:
                full_name = []
                if hasattr(sender, 'first_name') and sender.first_name:
                    full_name.append(sender.first_name)
                if hasattr(sender, 'last_name') and sender.last_name:
                    full_name.append(sender.last_name)
                return " ".join(full_name) if full_name else "Unknown User"
        elif isinstance(sender, Channel):
            return sender.title if sender.title else "Unknown Channel"
        else:
            return str(sender)
    
    @staticmethod
    def get_datetime_from(lookback_period: int) -> datetime:
        """
        Calculate the datetime from which to fetch messages.
        
        Args:
            lookback_period: Time period in seconds to look back
            
        Returns:
            UTC datetime object representing the lookback point
        """
        return (datetime.utcnow() - timedelta(seconds=lookback_period)).replace(tzinfo=timezone.utc)
    
    def get_peer_from_id(self, chat_id: Union[str, int]) -> Any:
        """
        Convert chat_id string to appropriate Peer object.
        
        Args:
            chat_id: Chat ID to convert
            
        Returns:
            Peer object or original chat_id
        """
        try:
            # Try to convert to integer
            chat_id_int = int(chat_id)
            
            # Handling different types of IDs
            if chat_id_int < 0:
                # For supergroups and channels
                if str(chat_id_int).startswith('-100'):
                    # Strip the -100 prefix to get the actual channel ID
                    channel_id = int(str(abs(chat_id_int))[2:])
                    return PeerChannel(channel_id)
                else:
                    # For older groups
                    return PeerChat(abs(chat_id_int))
            else:
                # For users
                return PeerUser(chat_id_int)
        except ValueError:
            # If it's not an integer, return the string as is
            return chat_id
    
    async def fetch_messages(self, chat_id: Union[str, int, Any], limit: Optional[int] = None, 
                             lookback_period: Optional[int] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Fetch messages from the specified chat.
        
        Args:
            chat_id: Chat ID to fetch messages from
            limit: Maximum number of messages to fetch
            lookback_period: Time period in seconds to look back
            
        Returns:
            Tuple of (list of message dictionaries, chat title)
        """
        self.logger.info(f"Fetching messages from chat")
        
        # Convert chat_id to appropriate peer
        peer = self.get_peer_from_id(chat_id) if isinstance(chat_id, (str, int)) else chat_id
        
        # Get chat entity and title
        try:
            chat_entity = await self.client.get_entity(peer)
            chat_title = getattr(chat_entity, 'title', str(chat_id))
        except Exception as e:
            self.logger.error(f"Error getting chat entity: {e}")
            chat_title = str(chat_id)
        
        # Determine fetch criteria (limit or time-based)
        messages = []
        datetime_from = None
        if lookback_period:
            datetime_from = self.get_datetime_from(lookback_period)
            self.logger.info(f"Fetching messages since {datetime_from}")
        
        try:
            async for message in self.client.iter_messages(peer, limit=limit):
                # Skip if before lookback period
                if datetime_from and message.date < datetime_from:
                    break
                
                if not message.text:
                    self.logger.debug("Skipping non-text message")
                    continue
                
                # Get message sender
                try:
                    sender = await message.get_sender()
                    sender_name = self.get_user_display_name(sender)
                    sender_id = sender.id
                except Exception as e:
                    self.logger.warning(f"Error getting sender: {e}")
                    sender_name = "Unknown"
                    sender_id = None
                
                # Check if message is forwarded
                is_forwarded = False
                fwd_from_name = None
                if hasattr(message, 'fwd_from') and message.fwd_from:
                    is_forwarded = True
                    # Try to get the original sender name
                    if hasattr(message.fwd_from, 'from_name') and message.fwd_from.from_name:
                        fwd_from_name = message.fwd_from.from_name
                    elif hasattr(message.fwd_from, 'from_id'):
                        try:
                            fwd_from_entity = await self.client.get_entity(message.fwd_from.from_id)
                            fwd_from_name = self.get_user_display_name(fwd_from_entity)
                        except:
                            fwd_from_name = "Unknown Source"
                    else:
                        fwd_from_name = "Unknown Source"
                
                # Create message dictionary
                msg_dict = {
                    "id": message.id,
                    "datetime": message.date.isoformat(),
                    "timestamp": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "text": message.text,
                    "sender_name": sender_name,
                    "sender_id": sender_id,
                    "is_reply": message.is_reply,
                    "is_forwarded": is_forwarded,
                    "forwarded_from": fwd_from_name if is_forwarded else None
                }
                
                # Add reply information if applicable
                if message.is_reply:
                    msg_dict["reply_to_msg_id"] = message.reply_to.reply_to_msg_id
                
                messages.append(msg_dict)
            
            self.logger.info(f"Successfully fetched {len(messages)} messages")
            return messages, chat_title
            
        except Exception as e:
            self.logger.error(f"Error fetching messages: {e}")
            return [], chat_title 