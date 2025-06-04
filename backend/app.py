"""
Main Flask application for the Voice Agent backend.
"""

from flask import Flask
from flask_socketio import SocketIO
import os
from config.settings import get_config
from websocket.conversation_events import register_conversation_events
from websocket.voice_events import register_voice_events
from websocket.tts_events import register_tts_events


def create_app(config_name=None):
    """Create and configure the Flask application."""

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Validate configuration
    config_errors = config_class.validate_config()
    if config_errors:
        for error in config_errors:
            app.logger.warning(f"CONFIG WARNING: {error}")

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Audio buffer storage for voice conversations
    # In production, use Redis or proper session storage
    voice_sessions = {}

    # Register WebSocket event handlers
    register_conversation_events(socketio, app)
    register_voice_events(socketio, app, voice_sessions)
    register_tts_events(socketio, app)

    # Add cleanup for voice sessions on disconnect
    @socketio.on("disconnect")
    def handle_disconnect():
        from flask import request

        session_id = request.sid
        if session_id in voice_sessions:
            del voice_sessions[session_id]
            app.logger.info(f"Cleaned up voice session for {session_id}")

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Simple health check endpoint."""
        return {"status": "healthy", "service": "voice-agent-backend"}

    # Root endpoint for Flutter connection testing
    @app.route("/")
    def root():
        """Root endpoint to verify backend is running."""
        return {
            "service": "Voice Agent Backend",
            "status": "running",
            "version": "1.0.0",
            "endpoints": {
                "websocket": "Connect to SocketIO for real-time communication",
                "health": "/health for health checks",
                "test": "/test for TTS streaming test page",
            },
        }

    # Test page for TTS streaming
    @app.route("/test")
    def test_page():
        """Serve the TTS streaming test page."""
        from flask import send_file
        import os

        test_file = os.path.join(
            os.path.dirname(__file__), "tests", "static", "test_tts.html"
        )
        return send_file(test_file)

    return app, socketio


def main():
    """Main entry point for running the application."""

    # Create app and socketio
    app, socketio = create_app()

    # Get configuration
    config = get_config()

    # Ensure temp audio directory exists
    os.makedirs(config.TEMP_AUDIO_DIR, exist_ok=True)

    # Log startup information
    app.logger.info("=" * 50)
    app.logger.info("Voice Agent Backend Starting")
    app.logger.info("=" * 50)
    app.logger.info(f"Host: {config.HOST}")
    app.logger.info(f"Port: {config.PORT}")
    app.logger.info(f"Debug: {config.DEBUG}")
    app.logger.info(f"Temp Audio Dir: {config.TEMP_AUDIO_DIR}")

    if config.CARTESIA_API_KEY:
        app.logger.info("✓ Cartesia API Key configured")
    else:
        app.logger.warning("✗ Cartesia API Key missing")

    if config.OPENAI_API_KEY:
        app.logger.info("✓ OpenAI API Key configured")
    else:
        app.logger.warning("✗ OpenAI API Key missing")

    app.logger.info("=" * 50)

    # Run the application
    try:
        socketio.run(
            app,
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            allow_unsafe_werkzeug=True,  # For development only
        )
    except KeyboardInterrupt:
        app.logger.info("Shutting down Voice Agent Backend...")
    except Exception as e:
        app.logger.error(f"Failed to start server: {e}")
        raise


if __name__ == "__main__":
    main()
