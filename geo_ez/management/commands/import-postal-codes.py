from __future__ import unicode_literals

import datetime
import logging
import math
import os
import zipfile
from urllib.request import urlretrieve

from django.conf import settings
from django.core.management.base import BaseCommand

from geo_ez.utility_functions import import_postal_codes_csv

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

        media_root_normalized = os.path.join(*os.path.split(settings.MEDIA_ROOT))
        zip_file_path = os.path.join(media_root_normalized, 'geonames')
        zip_file = os.path.join(zip_file_path, 'US.zip')

        if not os.path.exists(zip_file_path):
            os.makedirs(zip_file_path)

        if os.path.exists(zip_file):
            os.remove(zip_file)

        urlretrieve("http://download.geonames.org/export/zip/US.zip", zip_file)

        zip_ref = zipfile.ZipFile(zip_file, "r")
        zip_ref.extractall(zip_file_path)
        zip_ref.close()
        os.remove(zip_file)

        data_file_path = os.path.join(zip_file_path, 'US.txt')
        import_postal_codes_csv(data_file_path)

        os.remove(data_file_path)

        self._timer()
