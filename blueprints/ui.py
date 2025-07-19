from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from db import db
from models import Project, Collection, Request as ReqModel

ui_bp = Blueprint('ui', __name__, template_folder='templates')

def jwt_ui_required(fn):
    """Decorator to ensure valid JWT exists, else redirect to login."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
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
    """Show a project, handle adding collections"""
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'new_collection':
            name = request.form.get('collection_name')
            desc = request.form.get('collection_description')
            if not name:
                flash('Collection name is required.', 'error')
            else:
                col = Collection(
                    project_id=project_id,
                    name=name,
                    description=desc or ''
                )
                db.session.add(col)
                db.session.commit()
                return redirect(url_for('ui.project_detail', project_id=project_id))

    collections = project.collections
    return render_template(
        'project_detail.html',
        project=project,
        collections=collections
    )

@ui_bp.route('/collections/<int:collection_id>', methods=['GET', 'POST'])
@jwt_ui_required
def collection_detail(collection_id):
    # 1) Load the collection and ensure it exists
    col = Collection.query.get_or_404(collection_id)

    # 2) On POST, create a new Request
    if request.method == 'POST' and request.form.get('action') == 'new_request':
        name      = request.form.get('req_name')
        method    = request.form.get('req_method')
        path      = request.form.get('req_path')
        fmt       = request.form.get('response_format', 'json')
        body_text = request.form.get('body_template', '').strip()


        # Basic validation
        if not name or not method or not path:
            flash('Name, Method, and Path are required.', 'error')
        else:
            # Parse JSON if needed
            body_obj = None
            if fmt == 'json' and body_text:
                try:
                    body_obj = __import__('json').loads(body_text)
                except ValueError:
                    flash('Invalid JSON in template.', 'error')
                    # reload reqs below
                    reqs = col.requests
                    return render_template('collection_detail.html', collection=col, reqs=reqs)

            # Create and commit
            new_req = ReqModel(
                collection_id=collection_id,
                name=name,
                method=method,
                path=path,
                headers={},
                query_params={},
                body_template=body_obj,
                tests={'responseType': fmt.upper(), 'status': 200, 'delay_ms': 0}
            )
            db.session.add(new_req)
            db.session.commit()
            # redirect to clear the form and reload the GET
            return redirect(url_for('ui.collection_detail', collection_id=collection_id))


    # 3) Always fetch the up-to-date list of requests
    reqs = col.requests

    # 4) Render the template with that list
    return render_template('collection_detail.html', collection=col, reqs=reqs)

@ui_bp.route('/collections/<int:collection_id>/requests/<int:req_id>/test', methods=['GET'])
@jwt_ui_required
def test_request(collection_id, req_id):
    req = ReqModel.query.filter_by(id=req_id, collection_id=collection_id).first_or_404()
    return render_template('request_test.html', req=req)

@ui_bp.route('/collections/<int:collection_id>/requests/<int:req_id>/delete', methods=['POST'])
@jwt_ui_required
def delete_request(collection_id, req_id):
    req = ReqModel.query.filter_by(collection_id=collection_id, id=req_id).first_or_404()
    db.session.delete(req)
    db.session.commit()
    flash('Request deleted.', 'success')
    return redirect(url_for('ui.collection_detail', collection_id=collection_id))

@ui_bp.route('/logout', methods=['GET'])
def logout_page():
    """Page to redirect to login; front-end should clear token."""
    return redirect(url_for('auth.login'))
