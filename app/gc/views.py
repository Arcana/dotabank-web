from app import app, mem_cache
from app.admin.views import AdminModelView
from wtforms import PasswordField
from models import GCWorker
from helpers import AESCipher


@app.context_processor
@mem_cache.cached(timeout=60*60, key_prefix="gc_load")
def inject_gc_load():
    gc_workers = GCWorker.query.all()
    max_capacity = app.config['GC_MATCH_REQUSTS_RATE_LIMIT'] * len(gc_workers)
    jobs_processed = sum(w.job_count() for w in gc_workers)

    return dict(
        gc_jobs_processed=jobs_processed,
        gc_max_capacity=max_capacity,
        gc_load=(float(jobs_processed)/float(max_capacity))*100.0
    )


class GCWorkerAdmin(AdminModelView):
    form_excluded_columns = ('password', 'sentry')
    column_exclude_list = ('password', 'sentry')

    def __init__(self, session, **kwargs):
        # Just call parent class with predefined model.
        super(GCWorkerAdmin, self).__init__(GCWorker, session, **kwargs)

    def scaffold_form(self):
        form_class = super(GCWorkerAdmin, self).scaffold_form()
        form_class.new_password = PasswordField('New Password')

        return form_class

    def on_model_change(self, form, model):
        if len(model.new_password):
            model.password = AESCipher(app.config["ENCRYPTION_KEY"]).encrypt(model.new_password)
