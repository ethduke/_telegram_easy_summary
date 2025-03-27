import logging
from ollama import AsyncClient
from anthropic import AsyncAnthropic
from utils.config import (
    OLLAMA_MODEL,
    SUMMARY_PROMPT_TEMPLATE,
    ANTHROPIC_API_KEY,
    CLAUDE_OUTPUT_TOKENS,
    CLAUDE_MODEL
)

logger = logging.getLogger("TelegramMessageAnalyzer")


async def generate_summary_with_ai(
    messages_text: str,
    model: str = OLLAMA_MODEL,
    prompt_template: str = SUMMARY_PROMPT_TEMPLATE
) -> str:
    """
    Generate a summary using the appropriate AI provider based on the model name.
    
    Args:
        messages_text: The text of messages to summarize
        model: The model to use for summarization (determines which provider to use)
        prompt_template: The prompt template to use for the summary
        
    Returns:
        The generated summary
    """
    try:
        # Format the prompt with the message text
        prompt = prompt_template.format(messages=messages_text)
        
        # Determine which provider to use based on the model name
        if model.startswith("claude"):
            # Use Anthropic API for Claude models
            logger.info(f"Generating summary using {model} model via Anthropic API")
            client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            response = await client.messages.create(
                max_tokens=CLAUDE_OUTPUT_TOKENS,
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            ai_summary = response.content[0].text
        else:
            # Default to Ollama for other models
            logger.info(f"Generating summary using {model} model via Ollama AsyncClient")
            message = {'role': 'user', 'content': prompt}
            response = await AsyncClient().chat(model=model, messages=[message])
            ai_summary = response['message']['content']
        
        logger.info("AI summary generated successfully")
        return ai_summary
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return f"Error generating summary: {str(e)}"

    


    

