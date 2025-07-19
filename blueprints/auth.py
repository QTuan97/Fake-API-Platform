import logging
from flask import Blueprint, request, jsonify, make_response, render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token, unset_jwt_cookies, set_access_cookies, jwt_required
from db import db
from models import User

# configure logger for this module
gen_logger = logging.getLogger('auth')
auth_bp = Blueprint('auth', __name__)

def serve_mock(full_path):
    # 1) static files
    if full_path.startswith('static/'):
        return current_app.send_static_file(full_path)

    # 2) MockRules (dynamic)
    for rule in MockRule.query.all():
        crit = rule.match_criteria or {}
        if crit.get('method') != request.method:
            continue
        regex = crit.get('pathRegex')
        if not regex:
            continue
        if not re.fullmatch(regex.lstrip('/'), full_path):
            continue
        if rule.delay_ms:
            time.sleep(rule.delay_ms/1000)
        params = re.fullmatch(regex.lstrip('/'), full_path).groupdict()
        body = json.loads(Template(
            json.dumps(rule.response_template.get('body', {}))
        ).render(**params))
        return (jsonify(body),
                rule.response_template.get('status', 200),
                rule.response_template.get('headers', {}))

    # 3) Static Request definitions
    for r in ReqModel.query.filter_by(method=request.method).all():
        pattern = '^' + re.sub(
            r':(\w+)', r'(?P<\1>[^/]+)',
            r.path.lstrip('/')
        ) + '$'
        m = re.fullmatch(pattern, full_path)
        if m:
            params = m.groupdict()
            body = json.loads(Template(
                json.dumps(r.body_template or {})
            ).render(**params))
            return jsonify(body), 200, (r.headers or {})

    # 4) No match → genuine 404
    abort(404, description=f"No mock for {request.method} /{full_path}")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET: render login form
    POST: authenticate credentials from form or JSON, set JWT cookie, redirect to projects page
    """
    # 1) Render form on GET
    if request.method == 'GET':
        return render_template('login.html')

    # 2) Extract credentials
    if request.is_json:
        data = request.get_json() or {}
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    gen_logger.info(f"[AUTH] POST /auth/login username={username!r}")

    # 3) Validate
    user = User.query.filter_by(username=username).first()
    if not user:
        gen_logger.info("[AUTH] Invalid login: user not found")
        flash('Invalid credentials.', 'error')
        return render_template('login.html')

    if not user.check_password(password):
        gen_logger.info("[AUTH] Invalid login: incorrect password")
        flash('Invalid credentials.', 'error')
        return render_template('login.html')

    # 4) Issue token
    access_token = create_access_token(identity=str(user.id))
    resp = make_response(redirect(url_for('ui.index')))
    set_access_cookies(resp, access_token)
    gen_logger.info("[AUTH] Successful login; redirecting to projects page")
    return resp

@auth_bp.route('/logout')
@jwt_required()
def logout():
    resp = make_response(redirect(url_for('auth.login')))
    unset_jwt_cookies(resp)
    flash('Logged out.', 'info')
    return resp
