"""Register Step 2 on the existing app; no existing schema is upgraded here."""
from sqlalchemy import select
from database import get_session
from super_admin.models import PlatformSetting
from super_admin.service import registration_enabled
from . import models


def init_companies(app, fresh=False):
    from .views import bp
    from .admin_views import bp as admin_bp
    if fresh:
        with get_session() as db:
            if db.get(PlatformSetting, 'max_companies_per_user') is None:
                db.add(PlatformSetting(key='max_companies_per_user', value=False, integer_value=1))
                db.commit()
    app.register_blueprint(bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def registration_context():
        return {'public_registration_enabled': registration_enabled()}
