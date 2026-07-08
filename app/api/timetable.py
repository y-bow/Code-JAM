from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from ..models import User, TimetableEntry
from ..services import get_assigned_courses
from .schemas import TimetableEntrySchema

blp = Blueprint('timetable_api', __name__, url_prefix='/api/v1/timetable', description='Timetable operations')


@blp.route('/me')
class TimetableMe(MethodView):
    @blp.response(200, TimetableEntrySchema(many=True))
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        if user.role in ('student', 'class_rep'):
            profile = user.student_profile
            if not profile:
                return []
            section_id = profile.section_id
        elif user.role == 'dean':
            section_ids = [s.id for s in user.school.sections] if user.school else []
            entries = TimetableEntry.query.filter(
                TimetableEntry.section_id.in_(section_ids)
            ).order_by(TimetableEntry.day, TimetableEntry.start_time).all()
            return [e.to_dict() for e in entries]
        elif user.role in ('professor', 'assistant_professor'):
            courses = get_assigned_courses(user)
            course_ids = [c.id for c in courses]
            entries = TimetableEntry.query.filter(
                TimetableEntry.course_id.in_(course_ids)
            ).order_by(TimetableEntry.day, TimetableEntry.start_time).all()
            return [e.to_dict() for e in entries]
        else:
            return []

        entries = TimetableEntry.query.filter_by(
            section_id=section_id
        ).order_by(TimetableEntry.day, TimetableEntry.start_time).all()

        return [e.to_dict() for e in entries]
