from flask import Blueprint, request, jsonify, abort
from db import db
from models import MockRule, Project

# CRUD for MockRules nested under Projects
mockrules_bp = Blueprint(
    'mockrules', __name__,
    url_prefix='/api/projects/<int:project_id>/mockrules'
)

@mockrules_bp.route('/', methods=['GET'])

def list_mockrules(project_id):
    # Ensure project exists
    Project.query.get_or_404(project_id)
    rules = MockRule.query.filter_by(project_id=project_id).all()
    return jsonify([
        {
            'id':      r.id,
            'name':    r.name,
            'match':   r.match_criteria,
            'response':r.response_template,
            'delay_ms':r.delay_ms,
            'created_at': r.created_at.isoformat(),
            'updated_at': r.updated_at.isoformat()
        } for r in rules
    ]), 200

@mockrules_bp.route('/<int:rule_id>', methods=['GET'])

def get_mockrule(project_id, rule_id):
    r = MockRule.query.filter_by(project_id=project_id, id=rule_id).first_or_404()
    return jsonify({
        'id':      r.id,
        'name':    r.name,
        'match':   r.match_criteria,
        'response':r.response_template,
        'delay_ms':r.delay_ms,
        'created_at': r.created_at.isoformat(),
        'updated_at': r.updated_at.isoformat()
    }), 200

@mockrules_bp.route('/', methods=['POST'])

def create_mockrule(project_id):
    # Ensure project exists
    Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    # Validate required fields
    name = data.get('name')
    match = data.get('match_criteria')
    response = data.get('response_template')
    if not name or not match or not response:
        abort(400, description="'name', 'match_criteria', and 'response_template' are required fields.")
    delay = data.get('delay_ms')
    rule = MockRule(
        project_id=project_id,
        name=name,
        match_criteria=match,
        response_template=response,
        delay_ms=delay
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify({'id': rule.id}), 201

@mockrules_bp.route('/<int:rule_id>', methods=['PUT'])

def update_mockrule(project_id, rule_id):
    r = MockRule.query.filter_by(project_id=project_id, id=rule_id).first_or_404()
    data = request.get_json() or {}
    r.name = data.get('name', r.name)
    r.match_criteria = data.get('match_criteria', r.match_criteria)
    r.response_template = data.get('response_template', r.response_template)
    r.delay_ms = data.get('delay_ms', r.delay_ms)
    db.session.commit()
    return jsonify({'message': 'MockRule updated'}), 200

@mockrules_bp.route('/<int:rule_id>', methods=['DELETE'])

def delete_mockrule(project_id, rule_id):
    r = MockRule.query.filter_by(project_id=project_id, id=rule_id).first_or_404()
    db.session.delete(r)
    db.session.commit()
    return jsonify({'message': 'MockRule deleted'}), 200
