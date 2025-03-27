"""
Model package for Telegram Message Analyzer.
Contains the TelegramMessageAnalyzer class for message analysis.
"""

from model.message_analyzer import TelegramMessageAnalyzer

__all__ = ['TelegramMessageAnalyzer'] 

from model.ai_models import (
    generate_summary_with_ai
)