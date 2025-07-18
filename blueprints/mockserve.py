# blueprints/mockserve.py

import re
import json
import time
from flask import Blueprint, request, jsonify, abort, current_app
from jinja2 import Template

from models import Request as ReqModel, MockRule

mock_bp = Blueprint('mock', __name__)

@mock_bp.route('/<path:full_path>', methods=['GET','POST','PUT','DELETE','PATCH'])
def serve_mock(full_path):
    # Serve static assets
    if full_path.startswith('static/'):
        return current_app.send_static_file(full_path)

    # 1) Dynamic MockRules
    for rule in MockRule.query.all():
        crit = rule.match_criteria or {}
        if crit.get('method') and crit['method'] != request.method:
            continue
        regex = crit.get('pathRegex')
        if not regex:
            continue
        m = re.fullmatch(regex.lstrip('/'), full_path)
        if not m:
            continue
        if rule.delay_ms:
            time.sleep(rule.delay_ms / 1000)
        params = m.groupdict()
        body = json.loads(
            Template(json.dumps(rule.response_template.get('body', {}))).render(**params)
        )
        status  = rule.response_template.get('status', 200)
        headers = rule.response_template.get('headers', {}) or {}
        return jsonify(body), status, headers

    # 2) Static Request definitions
    for r in ReqModel.query.filter_by(method=request.method).all():
        pattern = '^' + re.sub(r':(\w+)', r'(?P<\1>[^/]+)', r.path.lstrip('/')) + '$'
        m = re.fullmatch(pattern, full_path)
        if not m:
            continue
        body = json.loads(
            Template(json.dumps(r.body_template or {})).render(**m.groupdict())
        )
        return jsonify(body), 200, (r.headers or {})

    # 3) No match → real 404
    abort(404, description=f"No mock for {request.method} /{full_path}")
