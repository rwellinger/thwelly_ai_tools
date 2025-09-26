"""
MUREKA API Clients

Modular client architecture for MUREKA API integration.
Provides backward compatibility with existing imports.
"""

# Import all public functions for backward compatibility
from .generation_client import (
    start_mureka_generation,
    check_mureka_status,
    wait_for_mureka_completion,
    MurekaGenerationClient
)

from .instrumental_client import (
    start_mureka_instrumental_generation,
    check_mureka_instrumental_status,
    wait_for_mureka_instrumental_completion,
    MurekaInstrumentalClient
)

from .base_client import MurekaBaseClient

# Preserve the original function imports from client.py
__all__ = [
    # Original client.py functions (backward compatibility)
    'start_mureka_generation',
    'check_mureka_status',
    'wait_for_mureka_completion',
    'start_mureka_instrumental_generation',
    'check_mureka_instrumental_status',
    'wait_for_mureka_instrumental_completion',
    # New client classes
    'MurekaBaseClient',
    'MurekaGenerationClient',
    'MurekaInstrumentalClient'
]