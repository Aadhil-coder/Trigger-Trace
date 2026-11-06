from flask import Flask, jsonify
from flask_cors import CORS

import config
import db
from routes.attacks import bp as attacks_bp


def create_app():
    app = Flask(__name__)
    CORS(app, origins=config.CORS_ORIGINS)
    app.teardown_appcontext(db.close_db)
    app.register_blueprint(attacks_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    db.init_db()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=config.PORT, debug=True)
