# blueprints/mockserve.py

import re
import json
import time
from flask import Blueprint, request, jsonify, abort, current_app
from sqlalchemy.inspection import inspect

from models import Request as ReqModel, MockRule, User, Collection  # import your models

# Map field names to model classes
DYNAMIC_MODELS = {
    'username': User,
    'collection_name': Collection,
    # add more: 'email': User, 'project_id': Project, etc.
}

mock_bp = Blueprint('mock', __name__)

def model_to_dict(obj):
    """Turn a SQLAlchemy object into a plain dict."""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

@mock_bp.route('/<path:full_path>', methods=['GET','POST','PUT','DELETE','PATCH'])
def serve_mock(full_path):
    current_app.logger.info(f"[MOCK] Incoming {request.method} /{full_path}")

    # 1) Static assets
    if full_path.startswith('static/'):
        return current_app.send_static_file(full_path)

    # 2) Dynamic MockRules (explicit JSON templates or DB rules)
    for rule in MockRule.query.all():
        crit = rule.match_criteria or {}
        if crit.get('method', '').upper() != request.method:
            continue

        # Build the regex for pathRegex with :param → named groups
        raw = crit.get('pathRegex', '').lstrip('/')
        pattern = '^' + re.sub(r':(\w+)',
                               lambda m: f"(?P<{m.group(1)}>[^/]+)",
                               raw) + '$'
        m = re.fullmatch(pattern, full_path)
        current_app.logger.info(f"[MOCK] Trying rule #{rule.id} pattern /{pattern} → {bool(m)}")
        if not m:
            continue

        # 2a) If rule says to use DB lookup automatically
        # We detect any DYNAMIC_MODELS keys in JSON body:
        data = request.get_json(silent=True) or {}
        model_class = None
        for field in DYNAMIC_MODELS:
            if field in data:
                model_class = DYNAMIC_MODELS[field]
                break

        if model_class:
            # Build filter kwargs from intersection of model's columns & data
            mapper = inspect(model_class)
            cols = {col.key for col in mapper.mapper.column_attrs}
            filters = {k: data[k] for k in data if k in cols}

            # Query
            obj = model_class.query.filter_by(**filters).first()
            if not obj:
                return jsonify({"error": f"{model_class.__name__} not found", **{k: None for k in filters}}), 404

            # Optionally simulate delay
            delay = rule.response_sequence[0].get('delay_ms', 0) or 0
            if delay:
                time.sleep(delay / 1000.0)

            return jsonify(model_to_dict(obj)), 200, {"Content-Type":"application/json"}

        # 2b) Otherwise fall back to your existing JSON‐template logic
        step    = rule.response_sequence[0]
        delay   = step.get('delay_ms', 0) or 0
        if delay:
            time.sleep(delay/1000.0)

        tpl     = step['response_template']
        body_obj= tpl.get('body', {})

        # Perform simple :param replacements from URL captures
        params  = m.groupdict()
        body_str = json.dumps(body_obj)
        for k, v in params.items():
            body_str = body_str.replace(f":{k}", str(v))

        try:
            body = json.loads(body_str)
            return jsonify(body), tpl.get('status',200), tpl.get('headers',{})
        except json.JSONDecodeError:
            return body_str, tpl.get('status',200), tpl.get('headers',{})

    # 3) Static Request fallback (unchanged)
    for r in ReqModel.query.filter_by(method=request.method).all():
        raw = r.path.lstrip('/')
        pat = '^' + re.sub(r':(\w+)',
                           lambda m: f"(?P<{m.group(1)}>[^/]+)",
                           raw) + '$'
        mm = re.fullmatch(pat, full_path)
        if not mm:
            continue

        params   = mm.groupdict()
        body_tpl = r.body_template or {}
        body_str = json.dumps(body_tpl)
        for k, v in params.items():
            body_str = body_str.replace(f":{k}", str(v))
        try:
            body = json.loads(body_str)
            return jsonify(body), 200, (r.headers or {})
        except json.JSONDecodeError:
            return body_str, 200, (r.headers or {})

    # 4) No match → 404
    abort(404, description=f"No mock for {request.method} /{full_path}")