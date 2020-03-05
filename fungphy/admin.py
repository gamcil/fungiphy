from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView

from database import app, Organism, Marker, Section, Genus, Subgenus, ExType, db


class MyView(BaseView):
    @expose("/")
    def index(self):
        return self.render("index.html")


admin = Admin(app)


class OrganismView(ModelView):
    column_list = (
        "section.subgenus.genus",
        "species",
        "mycobank",
        "reference",
        "type_strain",
        "extypes",
        "markers",
    )
    column_sortable_list = (
        ("section.subgenus.genus", "section.subgenus.genus.name"),
        "species",
        "mycobank",
        "reference",
        "type_strain",
    )
    column_searchable_list = (
        "section.subgenus.genus.name",
        "species",
        "mycobank",
        "reference",
        "type_strain",
    )
    column_labels = {"section.subgenus.genus": "Genus"}
    inline_models = (Marker, ExType)


class GenusView(ModelView):
    inline_models = (Subgenus,)


# Organism editor
admin.add_view(OrganismView(Organism, db.session))

# Taxonomy
# This should facilitate
admin.add_view(GenusView(Genus, db.session))
admin.add_view(ModelView(Subgenus, db.session))
admin.add_view(ModelView(Section, db.session))

app.run()
