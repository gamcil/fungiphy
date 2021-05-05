from flask import Blueprint
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.model.form import InlineFormAdmin

from fungphy.database import session
from fungphy.models import (
    Genus,
    Marker,
    MarkerType,
    Section,
    Species,
    Strain,
    StrainName,
    Subgenus,
)


class MyView(BaseView):
    @expose("/")
    def index(self):
        return self.render("index.html")


class MarkerView(ModelView):
    form_columns = ("id", "marker_type", "accession", "sequence")
    form_widget_args = {
        "id": {
            "placeholder": "new id will be autocreated",
            "readonly": True
        },
    }


class StrainView(ModelView):
    form_columns = ("id", "is_ex_type", "markers")
    form_widget_args = {
        "id": {
            "placeholder": "new id will be autocreated",
            "readonly": True
        },
    }
    inline_models = [
        MarkerView(Marker, session),
        StrainName,
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
    inline_models = [StrainView(Strain, session)]


class GenusView(ModelView):
    inline_models = (Subgenus,)


admin = Admin(template_mode="bootstrap3")
admin.add_view(GenusView(Genus, session))
admin.add_view(ModelView(Subgenus, session))
admin.add_view(ModelView(Section, session))
admin.add_view(SpeciesView(Species, session))
admin.add_view(ModelView(MarkerType, session))
