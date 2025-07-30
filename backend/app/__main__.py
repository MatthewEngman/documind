#!/usr/bin/env python3
"""
Main entry point for the DocuMind application
This ensures proper configuration loading and startup
"""

import os
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application"""
    # Import settings after logging is configured
    from app.config import settings
    
    logger.info("🚀 Starting DocuMind API server...")
    logger.info(f"🔧 Host: {settings.api_host}")
    logger.info(f"🔧 Port: {settings.api_port}")
    logger.info(f"🔧 Debug: {settings.debug}")
    logger.info(f"🌍 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"🌍 PORT env var: {os.getenv('PORT', 'not set')}")
    
    # Start the uvicorn server
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )

if __name__ == "__main__":
    main()
