from __future__ import unicode_literals

import datetime
import logging
import math

from django.conf import settings
from django.core.management.base import BaseCommand

from geo_ez.models import PostalCode
from geo_ez.utility_functions import points_within_radius

logger = logging.getLogger(__name__)

settings.DEBUG = False


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

        home_location = PostalCode.objects.get(postal_code="13212")
        # remote_location = PostalCode.objects.get(postal_code='13057')
        # zip_codes = postal_codes_within_radius(home_location.latitude, home_location.longitude, radius=5)
        zip_codes = points_within_radius(PostalCode, home_location.latitude, home_location.longitude, radius=5)

        for zip_code in zip_codes:
            print(zip_code.place_name, zip_code.postal_code, zip_code.distance)

        self._timer()
