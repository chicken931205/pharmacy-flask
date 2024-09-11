from flasgger import Swagger
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

from blueprint.app_api import api
from blueprint.routes import routes_bp
from config import Config
from models import db, User

login_manager = LoginManager()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'routes.login'
mail = Mail()
app.register_blueprint(routes_bp)
app.register_blueprint(api)
swagger = Swagger(app)
mail.init_app(app)
migrate = Migrate(app, db)


@app.before_request
def create_tables():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
