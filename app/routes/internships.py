from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from datetime import datetime
from app.middleware import school_scoped, role_minimum
from app.models import db, Internship

internships_bp = Blueprint('internships', __name__, url_prefix='/internships')


@internships_bp.route('/', methods=['GET'])
@school_scoped
def index():
    """List all available internships, with optional search/filter."""
    query = Internship.query

    # Search by role or company name
    search = request.args.get('search', '')
    if search:
        query = query.filter(
            db.or_(
                Internship.company_name.ilike(f'%{search}%'),
                Internship.role.ilike(f'%{search}%')
            )
        )

    # Filter by location
    location = request.args.get('location', '')
    if location:
        query = query.filter(Internship.location.ilike(f'%{location}%'))

    # Filter by duration
    duration = request.args.get('duration', '')
    if duration:
        query = query.filter(Internship.duration.ilike(f'%{duration}%'))

    internships = query.order_by(Internship.created_at.desc()).all()
    return render_template('internships/index.html', internships=internships,
                           search=search, location=location, duration=duration)


@internships_bp.route('/api/<int:internship_id>', methods=['GET'])
@school_scoped
def get_internship(internship_id):
    """JSON detail endpoint for a single internship."""
    internship = Internship.query.get_or_404(internship_id)
    return jsonify({
        'id': internship.id,
        'company_name': internship.company_name,
        'role': internship.role,
        'location': internship.location,
        'duration': internship.duration,
        'stipend': internship.stipend,
        'application_deadline': internship.application_deadline.strftime('%Y-%m-%d') if internship.application_deadline else None,
        'description': internship.description,
        'required_skills': internship.required_skills,
        'application_link': internship.application_link,
    })


@internships_bp.route('/new', methods=['GET', 'POST'])
@school_scoped
@role_minimum('dean')
def create():
    """Admin/Dean: create a new internship listing."""
    if request.method == 'POST':
        internship = Internship(
            company_name=request.form.get('company_name', '').strip(),
            role=request.form.get('role', '').strip(),
            location=request.form.get('location', '').strip(),
            duration=request.form.get('duration', '').strip(),
            stipend=request.form.get('stipend', '').strip() or None,
            description=request.form.get('description', '').strip() or None,
            required_skills=request.form.get('required_skills', '').strip() or None,
            application_link=request.form.get('application_link', '').strip() or None,
        )

        deadline_str = request.form.get('application_deadline', '').strip()
        if deadline_str:
            try:
                internship.application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid deadline format. Use YYYY-MM-DD.', 'error')
                return render_template('internships/form.html', internship=None)

        if not internship.company_name or not internship.role or not internship.location or not internship.duration:
            flash('Company name, role, location, and duration are required.', 'error')
            return render_template('internships/form.html', internship=None)

        db.session.add(internship)
        db.session.commit()
        flash(f'Internship at {internship.company_name} posted successfully!', 'success')
        return redirect(url_for('internships.index'))

    return render_template('internships/form.html', internship=None)


@internships_bp.route('/<int:internship_id>/edit', methods=['GET', 'POST'])
@school_scoped
@role_minimum('dean')
def edit(internship_id):
    """Admin/Dean: edit an existing internship listing."""
    internship = Internship.query.get_or_404(internship_id)

    if request.method == 'POST':
        internship.company_name = request.form.get('company_name', '').strip()
        internship.role = request.form.get('role', '').strip()
        internship.location = request.form.get('location', '').strip()
        internship.duration = request.form.get('duration', '').strip()
        internship.stipend = request.form.get('stipend', '').strip() or None
        internship.description = request.form.get('description', '').strip() or None
        internship.required_skills = request.form.get('required_skills', '').strip() or None
        internship.application_link = request.form.get('application_link', '').strip() or None

        deadline_str = request.form.get('application_deadline', '').strip()
        if deadline_str:
            try:
                internship.application_deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid deadline format. Use YYYY-MM-DD.', 'error')
                return render_template('internships/form.html', internship=internship)
        else:
            internship.application_deadline = None

        db.session.commit()
        flash('Internship updated successfully!', 'success')
        return redirect(url_for('internships.index'))

    return render_template('internships/form.html', internship=internship)


@internships_bp.route('/<int:internship_id>/delete', methods=['POST'])
@school_scoped
@role_minimum('dean')
def delete(internship_id):
    """Admin/Dean: delete an internship listing."""
    internship = Internship.query.get_or_404(internship_id)
    db.session.delete(internship)
    db.session.commit()
    flash('Internship listing removed.', 'success')
    return redirect(url_for('internships.index'))
