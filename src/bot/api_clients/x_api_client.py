# Compatibility wrapper for tests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.bot.api.x_client import XAPIClient

__all__ = ['XAPIClient']