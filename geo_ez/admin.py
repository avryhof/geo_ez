# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import PostalCode


@admin.register(PostalCode)
class PostalCodeAdmin(admin.ModelAdmin):
    list_display = (
        "country_code",
        "postal_code",
        "place_name",
        "admin_name1",
    )
    list_filter = ("country_code",)
    search_fields = ("place_name", "postal_code", "admin_name1", "admin_code1", "admin_name2")
