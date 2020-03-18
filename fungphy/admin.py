from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin

from fungphy.database import (
    Genus,
    Marker,
    Section,
    Species,
    Strain,
    StrainName,
    Subgenus,
    app,
    db,
)


class MyView(BaseView):
    @expose("/")
    def index(self):
        return self.render("index.html")


admin = Admin(app)


class StrainView(ModelView):
    form_columns = ("id", "is_ex_type", "strain_names", "markers")
    form_widget_args = {
        "id": {"placeholder": "new id will be autocreated", "readonly": True},
    }
    inline_models = [
        (Marker, dict(form_columns=["id", "marker", "accession", "sequence"])),
        (StrainName, dict(form_columns=["id", "name"])),
    ]


class SpeciesView(ModelView):
    column_list = (
        "section.subgenus.genus",
        "epithet",
        "mycobank",
        "reference",
        "type",
        "strains",
        "markers"
    )
    column_sortable_list = (
        ("section.subgenus.genus", "section.subgenus.genus.name"),
        "epithet",
        "mycobank",
        "reference",
        "type",
    )
    column_searchable_list = (
        "section.subgenus.genus.name",
        "epithet",
        "mycobank",
        "reference",
        "type",
    )
    column_labels = {"section.subgenus.genus": "Genus"}
    inline_models = [StrainView(Strain, db.session)]


class GenusView(ModelView):
    inline_models = (Subgenus,)


# Taxonomy
admin.add_view(GenusView(Genus, db.session))
admin.add_view(ModelView(Subgenus, db.session))
admin.add_view(ModelView(Section, db.session))

# Organism editor
admin.add_view(SpeciesView(Species, db.session))
# admin.add_view(StrainView(Strain, db.session))


app.run()
