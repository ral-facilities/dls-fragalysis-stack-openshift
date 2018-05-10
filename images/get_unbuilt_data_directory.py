#!/usr/bin/env python

"""get_unbuilt_data_directory.py

Prints the relative source data directory name if the most recent
data directory does not appear to be in the latest corresponding
Docker image.

Environment control the operation of this module: -

-   SOURCE_DATA_ROOT The root directory for source data
-   TARGET_IMAGE     The name of the image to build
-   FORCE_BUILD      Set to 'Yes' to always build a new image
-   HOURLY_BUILD     Set to Yes of the source data is expected to change
                     hourly. Data that changes hourly must use directory
                     namea odf the format YYYY-MM-DDTHH, i.e.
                     2018-01-02T10 for data available at 10AM
                     on the 2nd January 2018. If not set the data is expected
                     to change daily, using directory names of the format
                     YYYY-MM-DD.
-   INSIST_ON_READY  Set to 'Yes' to avoid building data unless the file
                     'READY' is present in the source directory.

Source data is expected in subdirectories of the SOURCE_DATA_ROOT
and the data is assumed to be 'ready for consumption' if the
file  'READY' exists in the dub-directory.

At the time of writing the Agent used in Jenkins has Python 2.7.5
installed so this is a Python 2.7-compliant module.
"""

from __future__ import print_function

import logging
from logging.config import dictConfig
import json
import os
import re
import subprocess
import sys
import yaml

# Extract environment variable values (with defaults)
SOURCE_DATA_ROOT = os.environ.get('SOURCE_DATA_ROOT', '/fragalysis/graph_data')
TARGET_IMAGE = os.environ.get('TARGET_IMAGE', 'fragalysis-cicd/graph-stream')

FORCE_BUILD = os.environ.get('FORCE_BUILD', 'No').lower() in ['y', 'yes']
HOURLY_DATA = os.environ.get('HOURLY_DATA', 'No').lower() in ['y', 'yes']
INSIST_ON_READY = os.environ.get('INSIST_ON_READY', 'No').lower() in ['y', 'yes']

# The image we'll be manufacturing...
REGISTRY  = 'docker-registry.default:5000'
TAG = 'latest'

# The key of the label value used to record
# the source data the image was built with.
# If the image was build from data from '2018-01-01'
# one of its 'Labels' will be 'data.origin':'2018-01-01'
DATA_ORIGIN_KEY = 'data.origin'

# Regular expression for each source data directory.
# These exist in the SOURCE_DATA_ROOT.
DATA_DIR_RE = '\d\d\d\d-\d\d-\d\d'
if HOURLY_DATA:
    DATA_DIR_RE += 'T\d\d'

# -----------------------------------------------------------------------------

# Load logger configuration (from cwd)...
# But only if the logging configuration is present!
LOGGING_CONFIG_FILE = 'logging.yml'
if os.path.isfile(LOGGING_CONFIG_FILE):
    LOGGING_CONFIG = None
    with open(LOGGING_CONFIG_FILE, 'r') as stream:
        try:
            LOGGING_CONFIG = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    dictConfig(LOGGING_CONFIG)
# Our logger...
LOGGER = logging.getLogger(os.path.basename(sys.argv[0])[:-3])

# -----------------------------------------------------------------------------

LOGGER.info('SOURCE_DATA_ROOT="%s"', SOURCE_DATA_ROOT)
LOGGER.info('TARGET_IMAGE="%s"', TARGET_IMAGE)
LOGGER.info('FORCE_BUILD=%s', FORCE_BUILD)
LOGGER.info('HOURLY_DATA=%s', HOURLY_DATA)
LOGGER.info('INSIST_ON_READY=%s', INSIST_ON_READY)

# Does the root data directory exist?
if not os.path.isdir(SOURCE_DATA_ROOT):
    LOGGER.warning('The data root directory does not exist'
                   ' (%s)', SOURCE_DATA_ROOT)
    sys.exit(0)

# Search the root data directory for sub-directories.
# We'll assume the last one holds the most recent data.
# There may not be any data directories.
most_recent_data_dir = None
DATA_DIRS = sorted(os.listdir(SOURCE_DATA_ROOT))
if DATA_DIRS:
    most_recent_data_dir = DATA_DIRS[-1]
else:
    # No data directories.
    LOGGER.warning('No data directories in the root (%s)', SOURCE_DATA_ROOT)
    sys.exit(0)
# Is the directory name correct?
if not re.match(DATA_DIR_RE, most_recent_data_dir):
    # Doesn't look right
    LOGGER.error('Most recent data directory name'
                 ' is not correct (%s)', most_recent_data_dir)
    sys.exit(0)
most_recent_data_path = os.path.join(SOURCE_DATA_ROOT, most_recent_data_dir)
if not os.path.isdir(most_recent_data_path):
    # Most recent does not look like a directory.
    LOGGER.error('Most recent data directory is not a directory'
                 ' (%s)', most_recent_data_dir)
    sys.exit(0)
# Check data is READY?
if INSIST_ON_READY and not os.path.exists(os.path.join(most_recent_data_path,
                                                       'READY')):
    # Directory exists but it's not 'ready'.
    LOGGER.info('Most recent data directory is not READY'
                ' (%s)', most_recent_data_dir)
    sys.exit(0)

# We have source data (that is READY) if we get here!
# Next stage build if the latest image does not contain this data
# (or build regardless if FORCE_BUILD is set).

if FORCE_BUILD:

    LOGGER.warning('Forcing build')

else:

    # Inspect the current image content and obtain the Labels.
    # One label will be the source data directory used to build the image
    # with the key DATA_ORIGIN_KEY and a value that is the directory
    # that housed the original data.
    #
    # We may not have an image, it may not have labels
    # or the label may be for an older data directory.
    # We need to build a new image for all these conditions.
    image = '%s/%s:%s' % (REGISTRY, TARGET_IMAGE, TAG)
    cmd = 'buildah inspect --type image %' % image
    image_str_info = None
    image_data_origin = None
    # Protect from failure...
    try:
        image_str_info = subprocess.check_output(cmd.split())
    except:
        LOGGER.warning('Failed inspecting the image (%s)', image)
    if image_str_info:
        image_json_info = json.loads(image_str_info)
        # If there are some labels
        # does one look like a data source label?
        # Labels should appear as a dictionary.
        labels = image_json_info['OCIv1']['config']['Labels']
        if labels and DATA_ORIGIN_KEY in labels:
            image_data_origin = labels[DATA_ORIGIN_KEY]
        else:
            LOGGER.warning('Image (%s) has no "%s" label (%s)',
                           image, DATA_ORIGIN_KEY, image)

    # If the current label matches the most recent data directory
    # then there's nothing to do -
    # the latest image is build from the latest data directory.
    if image_data_origin == most_recent_data_dir:
        LOGGER.info('The Latest image (%s) is built from'
                    'the most recent data directory (%s)',
                    image, image_data_origin)
        sys.exit(0)

    LOGGER.warning('Latest image (%s) is built from %s, not %s',
                   image, image_data_origin, most_recent_data_dir)

# There is no image, or its label does not match the
# most recent data directory and so we print the
# data directory, which can be used to trigger a build...
LOGGER.info('Data needs building (%s)', most_recent_data_dir)
print(most_recent_data_dir)
