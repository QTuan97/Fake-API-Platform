from flask import Blueprint, request, jsonify, abort
from db import db
from models import Collection, Project

collections_bp = Blueprint('collections', __name__, url_prefix='/api/collections')

@collections_bp.route('/', methods=['GET'])
def list_collections():
    collections = Collection.query.all()
    return jsonify([{
        'id': c.id,
        'project_id': c.project_id,
        'name': c.name,
        'description': c.description,
        'created_at': c.created_at.isoformat(),
        'updated_at': c.updated_at.isoformat()
    } for c in collections]), 200

@collections_bp.route('/<int:collection_id>', methods=['GET'])
def get_collection(collection_id):
    c = Collection.query.get_or_404(collection_id)
    return jsonify({
        'id': c.id,
        'project_id': c.project_id,
        'name': c.name,
        'description': c.description,
        'created_at': c.created_at.isoformat(),
        'updated_at': c.updated_at.isoformat()
    }), 200

@collections_bp.route('/', methods=['POST'])
def create_collection():
    data = request.get_json() or {}
    if not data.get('project_id') or not data.get('name'):
        abort(400, description="Missing 'project_id' or 'name' field.")
    # ensure project exists
    if not Project.query.get(data['project_id']):
        abort(404, description="Project not found.")
    c = Collection(
        project_id=data['project_id'],
        name=data['name'],
        description=data.get('description')
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'id': c.id}), 201

@collections_bp.route('/<int:collection_id>', methods=['PUT'])
def update_collection(collection_id):
    c = Collection.query.get_or_404(collection_id)
    data = request.get_json() or {}
    c.name = data.get('name', c.name)
    c.description = data.get('description', c.description)
    c.project_id = data.get('project_id', c.project_id)
    db.session.commit()
    return jsonify({'message': 'Collection updated'}), 200

@collections_bp.route('/<int:collection_id>', methods=['DELETE'])
def delete_collection(collection_id):
    c = Collection.query.get_or_404(collection_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Collection deleted'}), 200