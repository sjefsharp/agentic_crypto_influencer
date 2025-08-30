"""
tools package initialization.
Includes utility modules for API integration and callbacks.
"""

# Import tools that don't have external dependencies
from .bitvavo_handler import BitvavoHandler
from .post_handler import PostHandler
from .trends_handler import TrendsHandler
from .validator import Validator
from .x import X

# Import tools with external dependencies conditionally
try:
    from .google_grounding_tool import GoogleGroundingTool
except ImportError:
    GoogleGroundingTool = None  # type: ignore

try:
    from .oauth_handler import OAuthHandler
except ImportError:
    OAuthHandler = None  # type: ignore

try:
    from .redis_handler import RedisHandler
except ImportError:
    RedisHandler = None  # type: ignore

try:
    from .callback_server import *  # noqa: F403
except ImportError:
    pass

__all__ = [
    "BitvavoHandler",
    "PostHandler",
    "TrendsHandler",
    "Validator",
    "X",
]

# Add optional tools to __all__ only if import succeeded
if GoogleGroundingTool is not None:
    __all__.append("GoogleGroundingTool")

if OAuthHandler is not None:
    __all__.append("OAuthHandler")

if RedisHandler is not None:
    __all__.append("RedisHandler")
