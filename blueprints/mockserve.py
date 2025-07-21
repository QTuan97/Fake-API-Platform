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
        if crit.get('method') and crit['method'] != request.method:
            continue
        regex = crit.get('pathRegex')
        if not regex:
            continue
        m = re.fullmatch(regex.lstrip('/'), full_path)
        if not m:
            continue

        # We have a matching rule
        steps = rule.response_sequence or []
        if not steps:
            abort(500, "No response_sequence defined on rule")

        # 1) Check for conditional override steps first
        for step in steps:
            cond = step.get('condition')
            if cond:
                if _matches_condition(cond, request):   # implement this helper
                    chosen = step
                    break
        else:
            # 2) Otherwise cycle through steps by invocation count
            key = f"mockrule:{rule.id}:idx"
            idx = session.get(key, 0)
            chosen = steps[idx % len(steps)]
            session[key] = idx + 1

        # 3) Render the body_template with Jinja
        params = m.groupdict()
        # Also inject current_user if you like:
        user = None
        try:
            verify_jwt_in_request(optional=True)
            uid = get_jwt_identity()
            user = User.query.get(uid) if uid else None
        except:
            pass

        template_str = json.dumps(chosen['response_template'].get('body', {}))
        rendered = Template(template_str).render(**params, user=user)
        body = json.loads(rendered)

        # 4) Delay, status, headers
        if chosen.get('delay_ms'):
            time.sleep(chosen['delay_ms']/1000)
        status  = chosen['response_template'].get('status', 200)
        headers = chosen['response_template'].get('headers', {})

        return jsonify(body), status, headers

    # 5) No match → return 404
    abort(404, description=f"No mock for {request.method} /{full_path}")

def _matches_condition(cond, req):
    qs = req.args or {}
    for where, checks in cond.items():
        if where == 'query':
            for k,v in checks.items():
                if qs.get(k) == v:
                    return True
    return False