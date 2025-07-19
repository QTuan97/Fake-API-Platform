import re
import json
import time
from flask import Blueprint, request, jsonify, abort, current_app
from jinja2 import Template

from models import Request as ReqModel, MockRule

mock_bp = Blueprint('mock', __name__)

@mock_bp.route('/<path:full_path>', methods=['GET','POST','PUT','DELETE','PATCH'])
def serve_mock(full_path):
    """
    Catch-all mock server:
    1. Skip real routes (login, auth, API endpoints)
    2. Serve static assets
    3. Apply MockRule definitions
    4. Fallback to stored Request models
    5. Return 404 if no match
    """
    # 1) Skip real application routes
    if full_path in ('login', 'logout') or full_path.startswith('auth/') or full_path.startswith('api/'):
        abort(404)

    # 2) Serve static assets
    if full_path.startswith('static/'):
        return current_app.send_static_file(full_path)

    # 3) Dynamic MockRules
    for rule in MockRule.query.all():
        crit = rule.match_criteria or {}
        # match HTTP method if specified
        if crit.get('method') and crit['method'] != request.method:
            continue
        # match path regex
        regex = crit.get('pathRegex')
        if not regex:
            continue
        m = re.fullmatch(regex.lstrip('/'), full_path)
        if not m:
            continue
        # optional artificial delay
        if rule.delay_ms:
            time.sleep(rule.delay_ms / 1000)
        params = m.groupdict()
        body = json.loads(
            Template(json.dumps(rule.response_template.get('body', {}))).render(**params)
        )
        status  = rule.response_template.get('status', 200)
        headers = rule.response_template.get('headers', {}) or {}
        return jsonify(body), status, headers

    # 4) Stored Request definitions
    for r in ReqModel.query.filter_by(method=request.method).all():
        pattern = '^' + re.sub(r':(\w+)', r'(?P<\1>[^/]+)', r.path.lstrip('/')) + '$'
        m = re.fullmatch(pattern, full_path)
        if not m:
            continue
        params = m.groupdict()
        body = json.loads(
            Template(json.dumps(r.body_template or {})).render(**params)
        )
        headers = r.headers or {}
        return jsonify(body), 200, headers

    # 5) No match → return 404
    abort(404, description=f"No mock for {request.method} /{full_path}")
