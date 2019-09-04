from math import radians, cos, sin, asin, sqrt

from django.db import models
from django.db.models import DO_NOTHING

from geo_ez.constants import ACCURACY_CHOICES
from geo_ez.us_census_class import USCensus
from geo_ez.usps_class import USPS


class GISPoint(models.Model):
    name = models.CharField(max_length=180, blank=True, null=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "%s,%s" % (str(self.latitude), str(self.longitude))

    def distance_from(self, latitude, longitude, **kwargs):
        use_miles = kwargs.get("use_miles", True)
        distance_unit = float(3959 if use_miles else 6371)

        latitude1 = radians(float(latitude))
        latitude2 = radians(float(self.latitude))

        longitude1 = radians(float(longitude))
        longitude2 = radians(float(self.longitude))

        distance_longitude = longitude2 - longitude1
        distance_latitude = latitude2 - latitude1

        a = sin(distance_latitude / 2) ** 2 + cos(latitude1) * cos(latitude2) * sin(distance_longitude / 2) ** 2
        c = 2 * asin(sqrt(a))

        distance = c * distance_unit

        return distance

    def in_radius(self, latitude, longitude, radius, **kwargs):
        return self.distance_from(latitude, longitude, **kwargs) < radius


class PostalCode(GISPoint):
    country_code = models.CharField(max_length=2, blank=True, null=True)  # iso country code, 2 characters
    postal_code = models.CharField(max_length=20, blank=True, null=True)  # varchar(20)
    place_name = models.CharField(max_length=180, blank=True, null=True)  # varchar(180)
    admin_name1 = models.CharField(max_length=100, blank=True, null=True)  # 1. order subdivision (state) varchar(100)
    admin_code1 = models.CharField(max_length=20, blank=True, null=True)  # 1. order subdivision (state) varchar(20)
    admin_name2 = models.CharField(
        max_length=100, blank=True, null=True
    )  # 2. order subdivision (county/province) varchar(100)
    admin_code2 = models.CharField(
        max_length=20, blank=True, null=True
    )  # 2. order subdivision (county/province) varchar(20)
    admin_name3 = models.CharField(
        max_length=100, blank=True, null=True
    )  # 3. order subdivision (community) varchar(100)
    admin_code3 = models.CharField(max_length=20, blank=True, null=True)  # 3. order subdivision (community) varchar(20)
    accuracy = models.IntegerField(
        null=True, choices=ACCURACY_CHOICES
    )  # accuracy of lat/lng from 1=estimated, 4=geonameid, 6=centroid of addresses or shape
    updated = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return self.place_name


class StreetAddress(GISPoint):
    address1 = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=180, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    plus_four = models.CharField(max_length=20, blank=True, null=True)
    postal_code = models.ForeignKey(PostalCode, blank=True, null=True, on_delete=DO_NOTHING)
    validated = models.BooleanField(default=False)

    def dict(self):
        return dict(
            address1=self.address1, address2=self.address2, city=self.city, state=self.state, zip_code=self.zip_code
        )

    def geocode(self, **kwargs):
        retn = False

        valid_address = self.normalize()

        usc = USCensus()

        geocoded = usc.geocode(query=valid_address)
        if geocoded:
            retn = True
            self.latitude = geocoded.get("latitude")
            self.longitude = geocoded.get("longitude")

        return retn

    def link_postal_code(self):
        retn = False
        try:
            self.postal_code = PostalCode.objects.get(postal_code=self.zip_code)

        except PostalCode.DoesNotExist:
            pass

        else:
            retn = True
            self.save()

        return retn

    def normalize(self):
        valid_address = dict(
            address1=self.address1,
            address2=self.address2,
            city=self.city,
            state=self.state,
            zip_code=self.zip_code,
            plus_four=self.plus_four,
        )

        if not self.validated:
            search_address = self.dict()

            ps = USPS()
            valid_address = ps.address(**search_address)

            self.address1 = valid_address.get("address1", self.address1)
            self.address2 = valid_address.get("address2", self.address2)
            self.city = valid_address.get("city", self.city)
            self.state = valid_address.get("state", self.state)
            self.zip_code = valid_address.get("zip_code", self.zip_code)
            self.plus_four = valid_address.get("plus_four", self.plus_four)
            self.validated = True
            self.save()

        return valid_address
