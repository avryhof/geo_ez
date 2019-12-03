import datetime
import logging
import math
import os
import pprint

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DataError

from geo_ez.models import PostalCode, CountryData
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

        import_filename = "countryInfo.txt"
        import_file_path = os.path.join(data_dir, "geonames")
        import_file = os.path.join(import_file_path, "countryInfo.txt")

        if not os.path.exists(import_file_path):
            os.makedirs(import_file_path)

        if os.path.exists(import_file):
            os.remove(import_file)

        compatible_urlretrieve("http://download.geonames.org/export/dump/%s" % import_filename, import_file)

        headers = [
            "ISO",
            "ISO3",
            "ISO-Numeric",
            "fips",
            "Country",
            "Capital",
            "Area(in sq km)",
            "Population",
            "Continent",
            "tld",
            "CurrencyCode",
            "CurrencyName",
            "Phone",
            "Postal Code Format",
            "Postal Code Regex",
            "Languages",
            "geonameid",
            "neighbours",
            "EquivalentFipsCode",
        ]

        rows = csv_to_dicts(import_file, delimiter="\t", fieldnames=headers, has_comments=True)

        for row in rows:
            if row.get("ISO") in countries:
                try:
                    country = CountryData.objects.get(geonameid=row.get("geonameid"))

                except CountryData.DoesNotExist:
                    try:
                        country = CountryData.objects.create(
                            iso=row.get("ISO"),
                            iso3=row.get("ISO3"),
                            iso_numeric=row.get("ISO-Numeric"),
                            fips=row.get("fips"),
                            country=row.get("Country"),
                            capital=row.get("Capital"),
                            area_km=row.get("Area(in sq km)"),
                            population=row.get("Population"),
                            continent=row.get("Continent"),
                            tld=row.get("tld"),
                            currency_code=row.get("CurrencyCode"),
                            currency_name=row.get("CurrencyName"),
                            phone=row.get("Phone"),
                            postal_code_format=row.get("Postal Code Format"),
                            postal_code_ex=row.get("Postal Code Regex"),
                            languages=row.get("Languages"),
                            geonameid=row.get("geonameid"),
                            neighbors=row.get("neighbours"),
                            equivalent_fips_code=row.get("EquivalentFipsCode"),
                        )
                    except DataError as e:
                        print(e)
                        pprint.pprint(row)

                else:
                    country.iso = row.get("ISO")
                    country.iso3 = row.get("ISO3")
                    country.iso_numeric = row.get("ISO-Numeric")
                    country.fips = row.get("fips")
                    country.country = row.get("Country")
                    country.capital = row.get("Capital")
                    country.area_km = row.get("Area(in sq km)")
                    country.population = row.get("Population")
                    country.continent = row.get("Continent")
                    country.tld = row.get("tld")
                    country.currency_code = row.get("CurrencyCode")
                    country.currency_name = row.get("CurrencyName")
                    country.phone = row.get("Phone")
                    country.postal_code_format = row.get("Postal Code Format")
                    country.postal_code_ex = row.get("Postal Code Regex")
                    country.languages = row.get("Languages")
                    country.geonameid = row.get("geonameid")
                    country.neighbors = row.get("neighbours")
                    country.equivalent_fips_code = row.get("EquivalentFipsCode")
                    country.save()

        self._timer()
