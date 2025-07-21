import json
import logging
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from db import db
from models import Project, MockRule

logger = logging.getLogger(__name__)
mockrules_bp = Blueprint('mockrules', __name__, template_folder='templates')

def parse_json_field(field_name, default="{}"):
    """
    Pull a value from request.form[field_name], defaulting to '{}' if blank,
    then json.loads() it. On error, flash a message and abort(400).
    """
    raw = (request.form.get(field_name) or "").strip()
    if not raw:
        raw = default
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        flash(f"Invalid JSON in '{field_name}': {e}", 'error')
        abort(400)

@mockrules_bp.route(
    '/projects/<int:project_id>/mockrules',
    methods=['GET', 'POST']
)
@mockrules_bp.route(
    '/projects/<int:project_id>/mockrules/<int:rule_id>',
    methods=['GET', 'POST']
)
@jwt_required()
def manage_mockrules(project_id, rule_id=None):
    user_id = get_jwt_identity()
    project = Project.query.filter_by(id=project_id, owner_user=user_id).first_or_404()

    rule = None
    if rule_id:
        rule = MockRule.query.filter_by(id=rule_id, project_id=project_id).first_or_404()

    if request.method == 'POST':
        # 1) Required scalar fields
        method   = (request.form.get('method') or "").upper()
        endpoint = (request.form.get('endpoint') or "").strip()
        if not method or not endpoint:
            flash('Method and Endpoint are required.', 'error')
            return render_template(
                'mockrules.html',
                project=project,
                rule=rule,
                mock_rules=project.mock_rules
            )

        # 2) Parse JSON inputs
        match_body   = parse_json_field('match_body')
        resp_headers = parse_json_field('resp_headers', default="{}")
        resp_body    = parse_json_field('resp_body',    default="{}")

        # 3) Parse numeric inputs
        try:
            status = int(request.form.get('resp_status', 200))
        except ValueError:
            flash('Status must be a number.', 'error')
            abort(400)
        try:
            delay = int(request.form.get('resp_delay', 0))
        except ValueError:
            flash('Delay must be a number.', 'error')
            abort(400)

        # 4) Build JSON column payloads
        match_crit = {
            'method':    method,
            'pathRegex': endpoint,
            'body':      match_body
        }
        response_step = {
            'response_template': {
                'status':  status,
                'headers': resp_headers,
                'body':    resp_body
            },
            'delay_ms': delay
        }
        sequence = [response_step]

        # 5) Name the rule
        name = (request.form.get('name') or '').strip()
        if not name:
            flash('Rule Name is required.', 'error')
            abort(400)

        if rule:
            # update existing
            rule.name               = name
            rule.match_criteria     = match_crit
            rule.response_sequence  = sequence
            rule.updated_at         = datetime.utcnow()
            flash('MockRule updated.', 'success')
        else:
            # create new
            rule = MockRule(
                project_id=project_id,
                name=name,
                match_criteria=match_crit,
                response_sequence=sequence
            )
            db.session.add(rule)
            flash('MockRule created.', 'success')

        db.session.commit()
        return redirect(url_for('ui.project_detail', project_id=project_id))

    # GET → render UI
    return render_template(
        'mockrules.html',
        project=project,
        rule=rule,
        mock_rules=project.mock_rules
    )

@mockrules_bp.route(
    '/projects/<int:project_id>/mockrules/<int:rule_id>/delete',
    methods=['POST']
)
@jwt_required()
def delete_mockrule(project_id, rule_id):
    rule = MockRule.query.filter_by(id=rule_id, project_id=project_id).first_or_404()
    db.session.delete(rule)
    db.session.commit()
    flash('MockRule deleted.', 'success')
    return redirect(url_for('ui.project_detail', project_id=project_id))
