from flask.views import MethodView
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from ..models import User, db, bcrypt
from .schemas import LoginSchema, TokenSchema, UserSchema

blp = Blueprint('auth_api', __name__, url_prefix='/api/v1/auth', description='Authentication')


@blp.route('/login')
class Login(MethodView):
    @blp.arguments(LoginSchema)
    @blp.response(200, TokenSchema)
    def post(self, args):
        user = User.query.filter_by(email=args['email']).first()

        if not user or not bcrypt.check_password_hash(user.password_hash, args['password']):
            return {'code': 401, 'message': 'Invalid email or password'}, 401

        if not user.is_active:
            return {'code': 403, 'message': 'Account is deactivated'}, 403

        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'role': user.role,
                'school_id': user.school_id,
            }
        )

        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
            }
        }


@blp.route('/me')
class UserInfo(MethodView):
    @blp.response(200, UserSchema)
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        return {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
        }
