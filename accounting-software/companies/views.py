import hmac
from flask import Blueprint, abort, g, jsonify, redirect, render_template, request, session
from sqlalchemy import select
from database import get_session
from super_admin.models import PlatformSetting
from .config import COMPANY_TYPE_LABELS, LEGAL_FORM_LABELS, CURRENCIES
from .chart_config import KIND_LABELS, PACK_LABELS
from .models import Company, CompanyMembership
from .storage import CompanyError, provision_company, company_workspace, read_company_chart, _public_company

bp = Blueprint('companies', __name__, url_prefix='/companies')


def wants_json():
    return request.is_json or request.accept_mimetypes.best == 'application/json'


@bp.before_request
def protect():
    user = g.get('super_identity')
    if not user:
        return redirect('/login')
    if user.role != 'user':
        from .storage import _record_denied
        if (request.view_args or {}).get('company_id'):
            _record_denied(user.id, request.view_args['company_id'], 'role_denied', request.remote_addr)
        abort(403)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        expected, supplied = session.get('csrf_token'), request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not isinstance(expected, str) or not expected or not isinstance(supplied, str) or not hmac.compare_digest(expected, supplied):
            abort(400, description='Invalid CSRF token.')


@bp.after_request
def private(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Robots-Tag'] = 'noindex, nofollow'
    return response


@bp.context_processor
def context():
    return {'csrf_token': session.get('csrf_token', ''), 'type_labels': COMPANY_TYPE_LABELS, 'legal_labels': LEGAL_FORM_LABELS, 'currencies': CURRENCIES}


@bp.errorhandler(CompanyError)
def failure(error):
    if wants_json():
        return jsonify({'error': str(error), 'code': error.code}), error.status
    return render_template('companies/error.html', message=str(error)), error.status


def listing():
    with get_session() as db:
        query = select(Company).join(CompanyMembership, Company.id == CompanyMembership.company_id).where(CompanyMembership.user_id == g.super_identity.id, CompanyMembership.role == 'owner', CompanyMembership.status == 'active').order_by(Company.created_at.desc())
        rows = [_public_company(row) for row in db.scalars(query)]
        setting = db.get(PlatformSetting, 'max_companies_per_user')
        maximum = setting.integer_value if setting else None
        if not isinstance(maximum, int) or isinstance(maximum, bool) or not 1 <= maximum <= 100:
            raise CompanyError('Company limit configuration requires administrator review.', 503, 'invalid_company_limit')
    return rows, maximum


@bp.get('')
@bp.get('/')
def index():
    rows, maximum = listing()
    if wants_json(): return jsonify({'companies': rows, 'maximum': maximum})
    return render_template('companies/index.html', companies=rows, maximum=maximum, can_create=len(rows) < maximum)


@bp.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'GET':
        rows, maximum = listing()
        if len(rows) >= maximum: return redirect('/companies')
        return render_template('companies/new.html', values={})
    data = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    if not isinstance(data, dict): raise CompanyError('Enter valid company details.', 400, 'invalid_data')
    if not request.is_json:
        try: data['fiscal_year_start_month'] = int(data.get('fiscal_year_start_month', ''))
        except ValueError: raise CompanyError('Fiscal year start month must be between 1 and 12.', 400, 'invalid_fiscal_month')
    try:
        result = provision_company(g.super_identity.id, data, expected_epoch=session.get('session_epoch', 0), ip=request.remote_addr)
    except CompanyError as error:
        if wants_json(): raise
        safe_values = {key: value for key, value in data.items() if key in {'name','company_type','legal_form','base_currency','fiscal_year_start_month','tax_id'} and isinstance(value, (str, int))}
        return render_template('companies/new.html', values=safe_values, error=str(error)), error.status
    if wants_json(): return jsonify({'company': result}), 201
    return redirect('/companies/' + str(result['id']))


@bp.get('/<int:company_id>')
def workspace(company_id):
    result = company_workspace(company_id, g.super_identity.id, expected_epoch=session.get('session_epoch', 0), ip=request.remote_addr)
    result['status'] = 'active'
    if wants_json(): return jsonify({'company': result})
    chart = read_company_chart(company_id, g.super_identity.id, expected_epoch=session.get('session_epoch', 0), ip=request.remote_addr)
    return render_template('companies/workspace.html', company=result, accounts=chart, pack_labels=PACK_LABELS, kind_labels=KIND_LABELS)


@bp.get('/<int:company_id>/chart-of-accounts')
def chart_of_accounts(company_id):
    accounts = read_company_chart(company_id, g.super_identity.id, expected_epoch=session.get('session_epoch', 0), ip=request.remote_addr)
    return jsonify({'accounts': accounts})
