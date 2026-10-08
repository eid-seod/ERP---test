from flask import Blueprint, abort, flash, g, jsonify, redirect, render_template, request, session
from sqlalchemy import select, or_, func, text
from database import get_session
from models.user import User
from super_admin.models import PlatformSetting, utcnow
from super_admin.service import actor_in_transaction, audit, AdminError
from super_admin.views import protect_area, wants_json, paginated, paging, page_url, private_response
from .config import COMPANY_TYPES, COMPANY_TYPE_LABELS, LEGAL_FORM_LABELS
from .models import Company
from .storage import CompanyError, health_check, suspend_company, reactivate_company, _public_company

bp = Blueprint('company_admin', __name__, url_prefix='/super-admin')
bp.before_request(protect_area)
bp.after_request(private_response)


@bp.context_processor
def context():
    return {'csrf_token': session.get('csrf_token', ''), 'page_url': page_url, 'type_labels': COMPANY_TYPE_LABELS, 'legal_labels': LEGAL_FORM_LABELS}


@bp.errorhandler(CompanyError)
@bp.errorhandler(AdminError)
def failure(error):
    if wants_json(): return jsonify({'error': str(error)}), error.status
    return render_template('super_admin/error.html', message=str(error)), error.status


def metadata(row, owner):
    result = _public_company(row)
    result['owner'] = {'id': owner.id, 'name': owner.name, 'email': owner.email} if owner else None
    # Only this schema_meta health exception opens any company file.
    result['health'] = health_check(row)
    return result


@bp.get('/companies')
def companies():
    query = select(Company)
    search = request.args.get('q', '').strip()[:120]
    if search: query = query.where(Company.name.ilike('%' + search + '%'))
    company_type = request.args.get('type', '')
    if company_type:
        if company_type not in COMPANY_TYPES: raise AdminError('Invalid company type filter.')
        query = query.where(Company.company_type == company_type)
    status = request.args.get('status', '')
    if status:
        if status not in {'provisioning','active','failed','suspended'}: raise AdminError('Invalid company status filter.')
        query = query.where(Company.status == status)
    query = query.order_by(Company.created_at.desc(), Company.id.desc())
    with get_session() as db:
        items, pagination = paginated(db, query)
        rows = [metadata(row, db.get(User,row.owner_user_id)) for row in items]
    if wants_json(): return jsonify({'companies': rows, 'pagination': pagination})
    return render_template('super_admin/companies.html', companies=rows, pagination=pagination)


@bp.get('/companies/<int:company_id>')
def detail(company_id):
    with get_session() as db:
        company = db.get(Company, company_id)
        if not company: abort(404)
        result = metadata(company, db.get(User,company.owner_user_id))
    if wants_json(): return jsonify({'company': result})
    return render_template('super_admin/company_detail.html', company=result)


@bp.post('/companies/<int:company_id>/status')
def status(company_id):
    data = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    if not isinstance(data,dict) or data.get('action') not in ('suspend','reactivate'): raise AdminError('Choose suspend or reactivate.')
    service = suspend_company if data['action']=='suspend' else reactivate_company
    result = service(company_id,g.super_identity.id,expected_epoch=session.get('session_epoch',0),ip=request.remote_addr)
    if wants_json(): return jsonify({'company': result})
    flash('تم تحديث حالة الشركة وتسجيل التغيير.', 'success')
    return redirect('/super-admin/companies/' + str(company_id))


@bp.post('/company-limit')
def company_limit():
    data = request.get_json(silent=True) if request.is_json else request.form.to_dict()
    value = data.get('maximum') if isinstance(data,dict) else None
    if request.is_json and (not isinstance(value,int) or isinstance(value,bool)): raise AdminError('Choose a whole-number company limit (1–100).')
    try: maximum = int(value)
    except (TypeError, ValueError): raise AdminError('Choose a whole-number company limit (1–100).')
    if not 1<=maximum<=100: raise AdminError('Choose a whole-number company limit (1–100).')
    with get_session() as db:
        db.execute(text('BEGIN IMMEDIATE'))
        actor = actor_in_transaction(db,g.super_identity.id,session.get('session_epoch',0))
        setting = db.get(PlatformSetting,'max_companies_per_user')
        before = setting.integer_value if setting else 1
        if setting is None:
            setting = PlatformSetting(key='max_companies_per_user',value=False,integer_value=maximum);db.add(setting)
        else: setting.integer_value = maximum
        setting.updated_at = utcnow()
        audit(db,actor,'companies.limit_changed',before={'maximum':before},after={'maximum':maximum},ip=request.remote_addr)
        db.commit()
    if wants_json(): return jsonify({'max_companies_per_user':maximum})
    flash('تم تحديث حد الشركات.', 'success')
    return redirect('/super-admin/settings')
