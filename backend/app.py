"""Flask application entry point."""
import os
from app import create_app

env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', '').lower() in ('true', '1', 'yes') or env == 'development'
    app.run(debug=debug, host='127.0.0.1', port=5000)
