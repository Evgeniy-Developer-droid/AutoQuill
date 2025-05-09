from app.ai.models import AIConfig


async def add_ai_config_prompt(prompt: str, config: AIConfig) -> str:
    """
    Add AI config prompt to the given prompt.
    """
    prompt += f"""Use the following AI config for the generation:
    \nTemperature: {config.temperature}
    \nMax tokens: {config.max_tokens}
    \nLanguage: {config.language}
    \nTone: {config.tone}
    \nWriting style: {config.writing_style}
    \nEmojis: {config.emojis}"""
    if config.custom_instructions:
        prompt += f"\nCustom instructions: {config.custom_instructions}"
    return prompt

