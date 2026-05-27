from .youtube import YouTubeScraper
from .openai_scraper import OpenAIScraper
from .anthropic import AnthropicScraper
from .huggingface import HuggingFaceScraper

SCRAPER_REGISTRY = [
    YouTubeScraper(),
    OpenAIScraper(),
    AnthropicScraper(),
    HuggingFaceScraper(),
]
