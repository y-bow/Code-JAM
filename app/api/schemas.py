from marshmallow import Schema, fields


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class TokenSchema(Schema):
    access_token = fields.String()
    token_type = fields.String()
    user = fields.Nested(lambda: UserSchema(only=('id', 'name', 'email', 'role')))


class UserSchema(Schema):
    id = fields.String()
    name = fields.String()
    email = fields.Email()
    role = fields.String()
    is_active = fields.Boolean()


class TimetableEntrySchema(Schema):
    id = fields.String()
    day = fields.Integer()
    start_time = fields.String(attribute='start_time')
    end_time = fields.String(attribute='end_time')
    title = fields.String()
    teacher = fields.String()
    period = fields.String()
    room = fields.String()
    color = fields.String()
    status = fields.String()
    course_id = fields.String()


class ErrorSchema(Schema):
    code = fields.Integer()
    message = fields.String()
    errors = fields.Dict(fields.List(fields.String()), required=False)
