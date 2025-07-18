# blueprints/ui.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from db import db
from models import Project, Collection, Request as ReqModel, Environment

ui_bp = Blueprint('ui', __name__, template_folder='templates')

def jwt_ui_required(fn):
    """Decorator to ensure valid JWT exists, else redirect to login."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            if not get_jwt_identity():
                raise Exception()
        except:
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)
    return wrapper

@ui_bp.route('/', methods=['GET', 'POST'])
@jwt_ui_required
def index():
    """Show projects list and handle creation."""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        user_id = int(get_jwt_identity())
        if not name:
            flash('Project name is required.', 'error')
        else:
            project = Project(owner_user=user_id, name=name, description=description or '')
            db.session.add(project)
            db.session.commit()
            return redirect(url_for('ui.index'))
    projects = Project.query.filter_by(owner_user=int(get_jwt_identity())).all()
    return render_template('projects.html', projects=projects)

@ui_bp.route('/projects/<int:project_id>', methods=['GET', 'POST'])
@jwt_ui_required
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        # handle nested forms if needed
        pass
    collections = project.collections
    environments = project.environments
    return render_template('project_detail.html', project=project, collections=collections, envs=environments)

@ui_bp.route('/collections/<int:collection_id>', methods=['GET', 'POST'])
@jwt_ui_required
def collection_detail(collection_id):
    col = Collection.query.get_or_404(collection_id)
    if request.method == 'POST':
        # handle form if needed
        pass
    reqs = col.requests
    return render_template('collection_detail.html', collection=col, reqs=reqs)

@ui_bp.route('/logout', methods=['GET'])
def logout_page():
    """Page to redirect to login; front-end should clear token."""
    return redirect(url_for('auth.login'))
