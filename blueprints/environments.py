from flask import Blueprint, request, jsonify, abort
from db import db
from models import Environment, Project

# Nested under projects: /api/projects/<project_id>/environments
env_bp = Blueprint(
    'environments', __name__,
    url_prefix='/api/projects/<int:project_id>/environments'
)

@env_bp.route('/', methods=['GET'])
def list_environments(project_id):
    # Ensure project exists
    Project.query.get_or_404(project_id)
    envs = Environment.query.filter_by(project_id=project_id).all()
    return jsonify([
        {
            'id': e.id,
            'project_id': e.project_id,
            'name': e.name,
            'variables': e.variables,
            'created_at': e.created_at.isoformat(),
            'updated_at': e.updated_at.isoformat()
        } for e in envs
    ]), 200

@env_bp.route('/<int:env_id>', methods=['GET'])
def get_environment(project_id, env_id):
    e = Environment.query.filter_by(project_id=project_id, id=env_id).first_or_404()
    return jsonify({
        'id': e.id,
        'project_id': e.project_id,
        'name': e.name,
        'variables': e.variables,
        'created_at': e.created_at.isoformat(),
        'updated_at': e.updated_at.isoformat()
    }), 200

@env_bp.route('/', methods=['POST'])

def create_environment(project_id):
    # Ensure parent project exists
    Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    if not data.get('name') or not data.get('variables'):
        abort(400, description="Missing 'name' or 'variables'.")
    e = Environment(
        project_id=project_id,
        name=data['name'],
        variables=data['variables']
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({'id': e.id}), 201

@env_bp.route('/<int:env_id>', methods=['PUT'])
def update_environment(project_id, env_id):
    e = Environment.query.filter_by(project_id=project_id, id=env_id).first_or_404()
    data = request.get_json() or {}
    e.name = data.get('name', e.name)
    e.variables = data.get('variables', e.variables)
    db.session.commit()
    return jsonify({'message': 'Environment updated'}), 200

@env_bp.route('/<int:env_id>', methods=['DELETE'])
def delete_environment(project_id, env_id):
    e = Environment.query.filter_by(project_id=project_id, id=env_id).first_or_404()
    db.session.delete(e)
    db.session.commit()
    return jsonify({'message': 'Environment deleted'}), 200