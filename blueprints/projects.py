
from flask import Blueprint, request, jsonify, abort
from db import db
from models import Project

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


@projects_bp.route('/', methods=['GET'])
def list_projects():
    projects = Project.query.all()
    return jsonify([{
        'id': p.id,
        'owner_user': p.owner_user,
        'name': p.name,
        'description': p.description,
        'created_at': p.created_at.isoformat(),
        'updated_at': p.updated_at.isoformat()
    } for p in projects]), 200

@projects_bp.route('/<int:project_id>', methods=['GET'])
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify({
        'id': project.id,
        'owner_user': project.owner_user,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at.isoformat(),
        'updated_at': project.updated_at.isoformat()
    }), 200

@projects_bp.route('/', methods=['POST'])
def create_project():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('owner_user'):
        abort(400, description="Missing 'name' or 'owner_user' field.")
    project = Project(
        owner_user=data['owner_user'],
        name=data['name'],
        description=data.get('description')
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({'id': project.id}), 201

@projects_bp.route('/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    project.name = data.get('name', project.name)
    project.description = data.get('description', project.description)
    project.owner_user = data.get('owner_user', project.owner_user)
    db.session.commit()
    return jsonify({'message': 'Project updated'}), 200

@projects_bp.route('/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': 'Project deleted'}), 200