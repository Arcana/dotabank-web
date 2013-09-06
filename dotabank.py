from app import app, admin, db

from views import UserAdmin, ReplayAdmin, ReplayRatingAdmin

admin.add_view(UserAdmin(db.session))
admin.add_view(ReplayAdmin(db.session))
admin.add_view(ReplayRatingAdmin(db.session))
if __name__ == '__main__':
    app.run()
