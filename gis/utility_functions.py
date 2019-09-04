import csv
import datetime

from django.db.models.expressions import RawSQL
from django.utils.timezone import make_aware

from gis.models import PostalCode


def points_within_radius(gismodel, latitude, longitude, **kwargs):
    radius = kwargs.get("radius", False)
    use_miles = kwargs.get("use_miles", True)

    if radius:
        radius = float(radius)

    distance_unit = float(3959 if use_miles else 6371)

    # Great circle distance formula
    gcd_formula = (
        "%s * acos(least(greatest(cos(radians(%s)) * cos(radians(latitude)) * cos(radians(longitude) - "
        "radians(%s)) + sin(radians(%s)) * sin(radians(latitude)), -1), 1))"
    )
    distance_raw_sql = RawSQL(gcd_formula, (distance_unit, latitude, longitude, latitude))
    qs = gismodel.objects.all().annotate(distance=distance_raw_sql).order_by("distance")

    if radius:
        qs = qs.filter(distance__lt=radius)

    return qs


def postal_codes_within_radius(latitude, longitude, **kwargs):
    return points_within_radius(PostalCode, latitude, longitude, **kwargs)


def import_postal_codes_csv(data_file_path, **kwargs):
    delimiter = kwargs.get("delimiter", "\t")

    data_file = open(data_file_path, "rU", encoding="utf-8")

    rows = csv.reader(data_file, delimiter=delimiter)

    insert_list = []
    for row in rows:
        if len(row) > 0 and row[11]:
            try:
                postal_code = PostalCode.objects.get(postal_code=row[1], name=row[2], place_name=row[2])

            except PostalCode.DoesNotExist:
                insert_list.append(
                    PostalCode(
                        country_code=row[0],
                        postal_code=row[1],
                        name=row[2],
                        place_name=row[2],
                        admin_name1=row[3],
                        admin_code1=row[4],
                        admin_name2=row[5],
                        admin_code2=row[6],
                        admin_name3=row[7],
                        admin_code3=row[8],
                        latitude=row[9],
                        longitude=row[10],
                        accuracy=row[11],
                        updated=make_aware(datetime.datetime.now()),
                    )
                )

            else:
                postal_code.country_code = row[0]
                postal_code.postal_code = row[1]
                postal_code.name = row[2]
                postal_code.place_name = row[2]
                postal_code.admin_name1 = row[3]
                postal_code.admin_code1 = row[4]
                postal_code.admin_name2 = row[5]
                postal_code.admin_code2 = row[6]
                postal_code.admin_name3 = row[7]
                postal_code.admin_code3 = row[8]
                postal_code.latitude = row[9]
                postal_code.longitude = row[10]
                postal_code.accuracy = row[11]
                postal_code.updated = make_aware(datetime.datetime.now())
                postal_code.save()

    data_file.close()

    PostalCode.objects.bulk_create(insert_list)
