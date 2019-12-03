import datetime
import decimal
import logging
import math
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from geo_ez.models import PostalCode, TimeZone, TimeZoneMap
from geo_ez.python3_compatibility import compatible_urlretrieve
from geo_ez.utility_functions import csv_to_dicts

logger = logging.getLogger(__name__)

settings.DEBUG = False

countries = ["US", "AS", "GU", "MP", "PR", "VI", "AZ"]

insert_threshold = getattr(settings, "INSERT_THRESHOLD", 10000)
data_dir = getattr(settings, "DATA_DIR", os.path.join(settings.MEDIA_ROOT, "DATA"))


class Command(BaseCommand):
    help = "Import Postal Codes from GeoNames."
    verbosity = 0
    current_file = None
    log_file_name = None
    log_file = False

    init_time = None
    existing_drug_list = []
    drug_insert_list = []

    # def add_arguments(self, parser):
    #     parser.add_argument("address", type=str)

    def _log_message(self, message):
        log_message = "%s: %s\n" % (datetime.datetime.now().isoformat()[0:19], message)

        logger.info(message)

        if self.verbosity > 0:
            self.stdout.write(log_message)

    def _timer(self):
        if not self.init_time:
            self.init_time = datetime.datetime.now()
            self._log_message("Command initiated.")
        else:
            self._log_message("Command completed.")

            complete_time = datetime.datetime.now()
            command_total_seconds = (complete_time - self.init_time).total_seconds()
            command_minutes = math.floor(command_total_seconds / 60)
            command_seconds = command_total_seconds - (command_minutes * 60)

            self._log_message("Command took %i minutes and %i seconds to run." % (command_minutes, command_seconds))

    def handle(self, *args, **options):
        self.verbosity = int(options["verbosity"])

        self._timer()

        countries = sorted(list(set(list(PostalCode.objects.all().values_list("country_code", flat=True)))))

        self._log_message("Processing: %s" % ",".join(countries))

        import_filename = "timeZones.txt"
        import_file_path = os.path.join(data_dir, "geonames")
        import_file = os.path.join(import_file_path, import_filename)

        if not os.path.exists(import_file_path):
            os.makedirs(import_file_path)

        if os.path.exists(import_file):
            os.remove(import_file)

        compatible_urlretrieve("http://download.geonames.org/export/dump/%s" % import_filename, import_file)

        rows = csv_to_dicts(import_file, delimiter="\t")

        for row in rows:
            country_code = row.get("CountryCode")
            timezone_id = row.get("TimeZoneId")
            gmt_offset_jan = float(row.get("GMT offset 1. Jan 2019"))
            gmt_offset_jul = float(row.get("DST offset 1. Jul 2019"))
            raw_offset = float(row.get("rawOffset (independant of DST)"))

            if country_code in countries:
                try:
                    time_zone = TimeZone.objects.get(timezone_id=timezone_id)

                except TimeZone.DoesNotExist:
                    time_zone = TimeZone.objects.create(
                        country_code=country_code,
                        timezone_id=timezone_id,
                        gmt_offset_jan=gmt_offset_jan,
                        gmt_offset_jul=gmt_offset_jul,
                        raw_offset=raw_offset,
                    )
                else:
                    time_zone.country_code = country_code
                    time_zone.timezone_id = timezone_id
                    time_zone.gmt_offset_jan = gmt_offset_jan
                    time_zone.gmt_offset_jul = gmt_offset_jul
                    time_zone.raw_offset = raw_offset

                    time_zone.save()

        ztz_import_filename = "tz.data"
        ztz_import_file = os.path.join(import_file_path, import_filename)

        if os.path.exists(ztz_import_file):
            os.remove(ztz_import_file)

        compatible_urlretrieve(
            "https://raw.githubusercontent.com/infused/ziptz/master/data/%s" % ztz_import_filename, ztz_import_file
        )

        ztz_headers = ["zip_code", "timezone_id"]

        ztz_rows = csv_to_dicts(ztz_import_file, delimiter="=", fieldnames=ztz_headers)

        for ztz_row in ztz_rows:
            zipcode = ztz_row.get("zip_code")
            timezone_id = ztz_row.get("timezone_id")

            if "APO" not in timezone_id and "FPO" not in timezone_id:
                try:
                    tz_map = TimeZoneMap.objects.get(zip_code=zipcode)
                except TimeZoneMap.DoesNotExist:
                    try:
                        tz_map = TimeZoneMap.objects.create(zip_code=zipcode, time_zone_id=timezone_id)
                    except IntegrityError as e:
                        self._log_message(e)
                else:
                    tz_map.zip_code = zipcode
                    tz_map.time_zone_id = timezone_id
                    tz_map.save()

        self._timer()
