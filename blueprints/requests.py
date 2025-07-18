# blueprints/requests.py
from flask import Blueprint, request, jsonify, abort
#from flask_jwt_extended import jwt_required
from db import db
from models import Request as ReqModel, Collection

# Nested under collections: /api/collections/<collection_id>/requests
requests_bp = Blueprint(
    'requests', __name__,
    url_prefix='/api/collections/<int:collection_id>/requests'
)

@requests_bp.route('/', methods=['GET'])

def list_requests(collection_id):
    # Ensure collection exists
    Collection.query.get_or_404(collection_id)
    reqs = ReqModel.query.filter_by(collection_id=collection_id).all()
    return jsonify([
        {
            'id': r.id,
            'collection_id': r.collection_id,
            'name': r.name,
            'method': r.method,
            'path': r.path,
            'headers': r.headers,
            'query_params': r.query_params,
            'body_template': r.body_template,
            'tests': r.tests,
            'created_at': r.created_at.isoformat(),
            'updated_at': r.updated_at.isoformat()
        } for r in reqs
    ]), 200

@requests_bp.route('/<int:req_id>', methods=['GET'])

def get_request(collection_id, req_id):
    # Ensure request exists within the given collection
    r = ReqModel.query.filter_by(collection_id=collection_id, id=req_id).first_or_404()
    return jsonify({
        'id': r.id,
        'collection_id': r.collection_id,
        'name': r.name,
        'method': r.method,
        'path': r.path,
        'headers': r.headers,
        'query_params': r.query_params,
        'body_template': r.body_template,
        'tests': r.tests,
        'created_at': r.created_at.isoformat(),
        'updated_at': r.updated_at.isoformat()
    }), 200

@requests_bp.route('/', methods=['POST'])

def create_request(collection_id):
    # Ensure parent collection exists
    Collection.query.get_or_404(collection_id)
    data = request.get_json() or {}
    # Validate required fields
    if not data.get('name') or not data.get('method') or not data.get('path'):
        abort(400, description="Missing 'name', 'method', or 'path'.")
    r = ReqModel(
        collection_id=collection_id,
        name=data['name'],
        method=data['method'],
        path=data['path'],
        headers=data.get('headers'),
        query_params=data.get('query_params'),
        body_template=data.get('body_template'),
        tests=data.get('tests')
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({'id': r.id}), 201

@requests_bp.route('/<int:req_id>', methods=['PUT'])

def update_request(collection_id, req_id):
    # Ensure the request exists within the collection
    r = ReqModel.query.filter_by(collection_id=collection_id, id=req_id).first_or_404()
    data = request.get_json() or {}
    # Allow updates only within the same collection
    r.name = data.get('name', r.name)
    r.method = data.get('method', r.method)
    r.path = data.get('path', r.path)
    r.headers = data.get('headers', r.headers)
    r.query_params = data.get('query_params', r.query_params)
    r.body_template = data.get('body_template', r.body_template)
    r.tests = data.get('tests', r.tests)
    db.session.commit()
    return jsonify({'message': 'Request updated'}), 200

@requests_bp.route('/<int:req_id>', methods=['DELETE'])

def delete_request(collection_id, req_id):
    r = ReqModel.query.filter_by(collection_id=collection_id, id=req_id).first_or_404()
    db.session.delete(r)
    db.session.commit()
    return jsonify({'message': 'Request deleted'}), 200