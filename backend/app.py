from flask import Flask, jsonify
from flask_cors import CORS

import config
import db
from routes.attacks import bp as attacks_bp
from routes.checkins import bp as checkins_bp
from routes.patterns import bp as patterns_bp
from routes.report import bp as report_bp
from routes.profile import bp as profile_bp


def create_app():
    app = Flask(__name__)
    CORS(app, origins=config.CORS_ORIGINS)
    app.teardown_appcontext(db.close_db)

    for blueprint in (attacks_bp, checkins_bp, patterns_bp, report_bp, profile_bp):
        app.register_blueprint(blueprint, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok")

    db.init_db()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=config.PORT, debug=True)
