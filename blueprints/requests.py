# blueprints/requests.py
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import Request as ReqModel, Collection
from sqlalchemy.exc import IntegrityError

requests_bp = Blueprint('requests', __name__, url_prefix='/api')

@requests_bp.route('/collections/<int:collection_id>/requests', methods=['POST'])
@jwt_required()
def manage_requests(collection_id):
    # Ensure collection exists and belongs to user
    user_id = get_jwt_identity()
    collection = Collection.query.get_or_404(collection_id)
    # Optionally check ownership: via project owner
    if collection.project.owner_user != int(user_id):
        abort(403)

    if request.method == 'GET':
        reqs = ReqModel.query.filter_by(collection_id=collection_id).all()
        return jsonify([{
            'id': r.id,
            'name': r.name,
            'method': r.method,
            'path': r.path,
            'body_template': r.body_template,
            'tests': r.tests
        } for r in reqs])

    data = request.get_json() or {}
    name = data.get('name')
    method = data.get('method')
    path = data.get('path')
    body_template = data.get('body_template')
    tests = data.get('tests') or {}

    if not name or not method or not path:
        abort(400, description="'name', 'method', and 'path' are required")

    new_req = ReqModel(
        collection_id=collection_id,
        name=name,
        method=method,
        path=path,
        headers=data.get('headers', {}),
        query_params=data.get('query_params', {}),
        body_template=body_template,
        tests=tests
    )
    try:
        db.session.add(new_req)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, description="Database error adding request")

    return jsonify({'id': new_req.id}), 201

@requests_bp.route('/collections/<int:collection_id>/requests/<int:req_id>', methods=['GET','PUT','DELETE'])
@jwt_required()
def single_request(collection_id, req_id):
    user_id = get_jwt_identity()
    collection = Collection.query.get_or_404(collection_id)
    if collection.project.owner_user != int(user_id):
        abort(403)
    req = ReqModel.query.filter_by(id=req_id, collection_id=collection_id).first_or_404()

    if request.method == 'GET':
        return jsonify({
            'id': req.id,
            'name': req.name,
            'method': req.method,
            'path': req.path,
            'headers': req.headers,
            'query_params': req.query_params,
            'body_template': req.body_template,
            'tests': req.tests
        })

    if request.method == 'PUT':
        data = request.get_json() or {}
        req.name = data.get('name', req.name)
        req.method = data.get('method', req.method)
        req.path = data.get('path', req.path)
        req.headers = data.get('headers', req.headers)
        req.query_params = data.get('query_params', req.query_params)
        req.body_template = data.get('body_template', req.body_template)
        req.tests = data.get('tests', req.tests)
        db.session.commit()
        return jsonify({'message': 'Updated'}), 200

    if request.method == 'DELETE':
        db.session.delete(req)
        db.session.commit()
        return jsonify({'message': 'Deleted'}), 200