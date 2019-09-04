# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import PostalCode, StreetAddress


@admin.register(PostalCode)
class PostalCodeAdmin(admin.ModelAdmin):
    list_display = (
        "country_code",
        "postal_code",
        "place_name",
        "admin_name1",
        "admin_code1",
        "admin_name2",
        "admin_code2",
        "admin_name3",
        "admin_code3",
        "latitude",
        "longitude",
        "accuracy",
    )
    list_filter = ("admin_name1",)
    search_fields = ("place_name", "postal_code", "admin_name1", "admin_code1", "admin_name2")


@admin.register(StreetAddress)
class StreetAddressAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "address1",
        "address2",
        "city",
        "state",
        "zip_code",
    )
    list_filter = ("postal_code", "state", "validated")
    search_fields = ("name", "city", "state", "zip_code")

    def save_model(self, request, obj, form, change):
        super(StreetAddressAdmin, self).save_model(request, obj, form, change)

        obj.link_postal_code()
        obj.normalize()
        obj.geocode()
