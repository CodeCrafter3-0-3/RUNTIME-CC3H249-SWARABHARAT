"""Vercel serverless handler for SwaraBharat Flask app."""

import sys
import os

# Add BACKEND to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'BACKEND'))

from app import app

# Export for Vercel
app = app
