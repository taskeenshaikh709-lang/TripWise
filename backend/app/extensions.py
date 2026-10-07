# Shared Flask extensions will be initialized here
# as we add database and authentication modules.
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()