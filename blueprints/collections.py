from flask import Blueprint, request, jsonify, abort
from db import db
from models import Collection, Project
from models import Request as ReqModel
from flask_jwt_extended import jwt_required
import json

collections_bp = Blueprint('collections', __name__, url_prefix='/api/collections')

@collections_bp.route('/', methods=['GET'])
@jwt_required()
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
@jwt_required()
def collection_detail(collection_id):
    col = Collection.query.get_or_404(collection_id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'new_request':
            name    = request.form.get('req_name')
            method  = request.form.get('req_method')
            path    = request.form.get('req_path')
            fmt     = request.form.get('response_format', 'json')
            status  = int(request.form.get('status_code', 200))
            delay   = int(request.form.get('delay_ms', 0))
            body    = request.form.get('body_template', '').strip()

            if not name or not method or not path:
                flash('Name, Method, and Path are required.', 'error')
            else:
                # parse template into JSON or leave raw for XML
                if fmt == 'json':
                    try:
                        body_obj = json.loads(body) if body else {}
                    except json.JSONDecodeError:
                        flash('Invalid JSON in body template.', 'error')
                        return render_template('requests.html', collection=col, reqs=col.requests)
                else:
                    # for XML store raw string
                    body_obj = body

                new_req = ReqModel(
                    collection_id=collection_id,
                    name=name,
                    method=method,
                    path=path,
                    headers={},
                    query_params={},
                    body_template=body_obj if fmt=='json' else None,
                    tests={
                      'responseType': fmt.upper(),
                      'status': status,
                      'delay_ms': delay
                    }
                )
                db.session.add(new_req)
                db.session.commit()
                return redirect(url_for('ui.collection_detail', collection_id=collection_id))

    # existing GET logic
    reqs = col.requests
    return render_template('requests.html', collection=col, reqs=reqs)

@collections_bp.route('/', methods=['GET'])
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
@jwt_required()
def update_collection(collection_id):
    c = Collection.query.get_or_404(collection_id)
    data = request.get_json() or {}
    c.name = data.get('name', c.name)
    c.description = data.get('description', c.description)
    c.project_id = data.get('project_id', c.project_id)
    db.session.commit()
    return jsonify({'message': 'Collection updated'}), 200

@collections_bp.route('/<int:collection_id>', methods=['DELETE'])
@jwt_required()
def delete_collection(collection_id):
    c = Collection.query.get_or_404(collection_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Collection deleted'}), 200