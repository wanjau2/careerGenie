"""Career Genie Backend API - Main Application."""
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Import configuration
from config.settings import get_config
from config.database import init_database, db_manager

# Import routes
from routes.auth import auth_bp
from routes.users import users_bp
from routes.jobs import jobs_bp
from routes.files import files_bp
from routes.onboarding import onboarding_bp
from routes.resume import resume_bp
from routes.courses import courses_bp
from routes.training import training_bp
from routes.oauth import oauth_bp
from routes.subscription import subscription_bp
from routes.ads import ads_bp

# Import utilities
from utils.helpers import format_error_response


def create_app(config_name=None):
    """
    Create and configure Flask application.

    Args:
        config_name: Configuration name (development, production, testing)

    Returns:
        Flask app instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    config_class = get_config()
    app.config.from_object(config_class)

    # Setup logging
    setup_logging(app)

    # Initialize extensions
    setup_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Initialize database
    with app.app_context():
        try:
            init_database()
            app.logger.info("Database initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize database: {e}")

    # Add health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        try:
            # Check database connection
            from config.database import get_database
            db = get_database()
            db.command('ping')

            return jsonify({
                'status': 'healthy',
                'service': 'career-genie-api',
                'database': 'connected',
                'version': '1.0.0'
            }), 200

        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'service': 'career-genie-api',
                'database': 'disconnected',
                'error': str(e)
            }), 503

    @app.route('/')
    def index():
        """API root endpoint."""
        return jsonify({
            'message': 'Career Genie API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'oauth': '/api/oauth',
                'users': '/api/user',
                'jobs': '/api/jobs',
                'files': '/api/files',
                'onboarding': '/api/onboarding',
                'courses': '/api/courses',
                'training': '/api/training',
                'health': '/health',
                'docs': '/api/docs'
            }
        }), 200

    @app.route('/oauth/callback')
    def oauth_callback():
        """OAuth callback endpoint for browser redirects from LinkedIn."""
        from flask import request, render_template_string, redirect

        # Check for errors
        error = request.args.get('error')
        error_description = request.args.get('error_description')

        if error:
            # Show error page for all platforms
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth Error - Career Genie</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                    .error { background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 5px; }
                    .error h2 { color: #c33; margin-top: 0; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>OAuth Authentication Failed</h2>
                    <p><strong>Error:</strong> {{ error }}</p>
                    <p><strong>Description:</strong> {{ error_description }}</p>
                    <p>Please close this window and try again.</p>
                </div>
            </body>
            </html>
            """, error=error, error_description=error_description), 400

        # Get authorization code
        code = request.args.get('code')
        state = request.args.get('state')

        if not code:
            # Show error page for all platforms
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OAuth Error - Career Genie</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                    .error { background: #fee; border: 1px solid #fcc; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="error">
                    <h2>OAuth Error</h2>
                    <p>No authorization code received.</p>
                    <p>Please close this window and try again.</p>
                </div>
            </body>
            </html>
            """), 400

        # Display postMessage page for all platforms (web and mobile)
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OAuth Success - Career Genie</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    text-align: center;
                }
                .success {
                    background: #efe;
                    border: 1px solid #cfc;
                    padding: 30px;
                    border-radius: 10px;
                }
                .success h2 {
                    color: #0077B5;
                    margin-top: 0;
                }
                .close-btn {
                    background: #0077B5;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 20px;
                }
                .close-btn:hover {
                    background: #005582;
                }
            </style>
            <script>
                // For web apps, try to send message to opener window
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'LINKEDIN_OAUTH_SUCCESS',
                        code: '{{ code }}',
                        state: '{{ state }}'
                    }, '*');

                    // Auto-close after a short delay
                    setTimeout(function() {
                        window.close();
                    }, 2000);
                }

                function closeWindow() {
                    window.close();
                }
            </script>
        </head>
        <body>
            <div class="success">
                <h2>✓ LinkedIn Authentication Successful!</h2>
                <p>You have successfully authenticated with LinkedIn.</p>
                <p style="color: #666; font-size: 14px;">
                    This window will close automatically in 2 seconds, or you can close it manually.
                </p>
                <button class="close-btn" onclick="closeWindow()">Close Window</button>
            </div>
        </body>
        </html>
        """, code=code, state=state), 200

    @app.route('/api/docs')
    def api_docs():
        """API documentation endpoint."""
        return jsonify({
            'message': 'Career Genie API Documentation',
            'version': '1.0.0',
            'authentication': {
                'POST /api/auth/register': 'Register new user',
                'POST /api/auth/login': 'Login user',
                'POST /api/auth/refresh': 'Refresh access token',
                'GET /api/auth/me': 'Get current user profile',
                'POST /api/auth/logout': 'Logout user'
            },
            'oauth': {
                'GET /api/oauth/linkedin/url': 'Get LinkedIn OAuth authorization URL',
                'POST /api/oauth/linkedin/callback': 'Handle LinkedIn OAuth callback',
                'GET /api/oauth/google/url': 'Get Google OAuth authorization URL (not implemented)',
                'POST /api/oauth/google/callback': 'Handle Google OAuth callback (not implemented)'
            },
            'users': {
                'GET /api/user/profile': 'Get user profile',
                'PUT /api/user/profile': 'Update user profile',
                'PUT /api/user/preferences': 'Update job preferences',
                'GET /api/user/subscription/status': 'Get subscription status',
                'POST /api/user/subscription/upgrade': 'Upgrade subscription',
                'DELETE /api/user/account': 'Deactivate account'
            },
            'jobs': {
                'GET /api/jobs': 'Get recommended jobs',
                'GET /api/jobs/<id>': 'Get job details',
                'POST /api/jobs/<id>/swipe': 'Swipe on job',
                'GET /api/jobs/liked': 'Get liked jobs',
                'GET /api/jobs/history': 'Get swipe history',
                'POST /api/jobs/<id>/apply': 'Apply to job',
                'GET /api/jobs/applications': 'Get applications',
                'GET /api/jobs/search': 'Search jobs'
            },
            'files': {
                'POST /api/files/upload-avatar': 'Upload profile picture',
                'POST /api/files/upload-resume': 'Upload resume',
                'POST /api/files/upload-document': 'Upload document',
                'DELETE /api/files/delete': 'Delete file'
            },
            'onboarding': {
                'POST /api/onboarding/start': 'Start onboarding process',
                'POST /api/onboarding/step/<step>': 'Complete onboarding step',
                'POST /api/onboarding/complete': 'Complete onboarding',
                'GET /api/onboarding/status': 'Get onboarding status',
                'POST /api/onboarding/parse-resume': 'Parse resume with AI',
                'POST /api/onboarding/skills/recommend': 'Get diverse skill recommendations',
                'GET /api/onboarding/skills/search': 'Search skills across all industries',
                'GET /api/onboarding/skills/industries': 'Get all supported industries',
                'GET /api/onboarding/skills/categories/<industry>': 'Get skill categories by industry',
                'POST /api/onboarding/linkedin/merge': 'Merge LinkedIn data'
            },
            'courses': {
                'GET /api/courses': 'Get courses with filters',
                'GET /api/courses/search': 'Search courses',
                'GET /api/courses/recommended': 'Get AI-recommended courses',
                'GET /api/courses/<id>': 'Get course details',
                'GET /api/courses/categories': 'Get course categories',
                'GET /api/courses/providers': 'Get course providers',
                'GET /api/courses/featured': 'Get featured courses',
                'GET /api/courses/skill-gaps': 'Get skill gap analysis',
                'GET /api/courses/enrollments': 'Get user enrollments',
                'POST /api/courses/enrollments': 'Enroll in course'
            },
            'training': {
                'POST /api/training/upload': 'Upload training corpus (resumes)',
                'GET /api/training/corpora': 'Get all training corpora',
                'GET /api/training/corpora/<id>': 'Get corpus details',
                'DELETE /api/training/corpora/<id>': 'Delete training corpus',
                'POST /api/training/jobs/start': 'Start model training job',
                'GET /api/training/jobs/<id>': 'Get training job status',
                'GET /api/training/analytics': 'Get training analytics',
                'GET /api/training/search': 'Search training resumes',
                'GET /api/training/patterns': 'Get extracted patterns',
                'POST /api/training/validate': 'Validate resume quality',
                'POST /api/training/auto-train': 'Trigger automatic training'
            }
        }), 200

    return app


def setup_logging(app):
    """Setup application logging."""
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # File handler for general logs
        file_handler = RotatingFileHandler(
            'logs/career_genie.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Career Genie API startup')


def setup_extensions(app):
    """Initialize Flask extensions."""
    # JWT
    jwt = JWTManager(app)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        response, status_code = format_error_response("Token has expired", 401)
        return jsonify(response), status_code

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        response, status_code = format_error_response("Invalid token", 401)
        return jsonify(response), status_code

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        response, status_code = format_error_response("Authorization token required", 401)
        return jsonify(response), status_code

    # CORS - Allow all localhost origins in development for Flutter web
    cors_config = {
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }

    # In development, allow all origins for testing (Flutter web uses dynamic ports)
    if app.config['DEBUG']:
        cors_config["origins"] = "*"
    else:
        cors_config["origins"] = app.config['CORS_ORIGINS']

    CORS(app, resources={r"/api/*": cors_config})

    # Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config['RATELIMIT_STORAGE_URL'],
        default_limits=[app.config['RATELIMIT_DEFAULT']]
    )

    app.logger.info("Extensions initialized")


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(training_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(ads_bp)

    app.logger.info("Blueprints registered")


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(format_error_response("Bad request", 400)), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify(format_error_response("Unauthorized", 401)), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify(format_error_response("Forbidden", 403)), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(format_error_response("Resource not found", 404)), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify(format_error_response("Method not allowed", 405)), 405

    @app.errorhandler(409)
    def conflict(error):
        return jsonify(format_error_response("Conflict", 409)), 409

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify(format_error_response("File too large", 413)), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify(format_error_response("Rate limit exceeded. Please try again later.", 429)), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify(format_error_response("Internal server error", 500)), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        return jsonify(format_error_response("Service temporarily unavailable", 503)), 503


# Create application instance
app = create_app()


# Cleanup on shutdown
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close database connection on shutdown."""
    if exception:
        app.logger.error(f"Application error: {exception}")


if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'

    print(f"""
╔═══════════════════════════════════════════════╗
║     Career Genie API Server Starting...      ║
╚═══════════════════════════════════════════════╝

🚀 Server running on: http://localhost:{port}
📚 API Documentation: http://localhost:{port}/api/docs
💚 Health Check: http://localhost:{port}/health

Press CTRL+C to quit
    """)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
