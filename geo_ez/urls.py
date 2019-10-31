from django.urls import re_path

from geo_ez.views import get_zipcodes_in_radius

urlpatterns = [
    re_path(
        r"^zip-code/(?P<zip_code>\d+)/(?P<radius>[0-9\.]+)/(?P<distance_units>[a-zA-Z]+)/$",
        get_zipcodes_in_radius,
        name="get_zipcodes_in_radius",
    )
]
