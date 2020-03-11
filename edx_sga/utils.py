"""
Utility functions for the SGA XBlock
"""
import hashlib
import os
import datetime
import time
from functools import partial
import pytz
import six
import json

from django.conf import settings
from django.core.files.storage import default_storage

from edx_sga.constants import BLOCK_SIZE

import logging
log = logging.getLogger(__name__)

def utcnow():
    """
    Get current date and time in UTC
    """
    return datetime.datetime.now(tz=pytz.utc)

def utc_to_local(utc_dt):
    """
    Convert UTC time to MSK
    """
    try:
        local_tz = pytz.timezone('Europe/Moscow')
        local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_tz.normalize(local_dt)
    except AttributeError:
        return None

def msknow():
    """
    Get current date and time in MSK
    """
    return datetime.datetime.now(tz=pytz.timezone('Europe/Moscow'))


def is_finalized_submission(submission_data):
    """
    Helper function to determine whether or not a Submission was finalized by the instructor
    """
    if submission_data and submission_data.get('answer') is not None:
        return submission_data['answer'].get('finalized')
    return False

def data_finalized(submission_data):
    """
    Helper function to give date of finalizing submission
    """
    if submission_data and submission_data['answer'].get('date_fin') is not None:
        return submission_data['answer'].get('date_fin')
    return None

def freshen_answer(module, fresh):
    """
    Helper function to make submission fresh
    """
    state = json.loads(module.state)
    state['fresh'] = fresh
    module.state = json.dumps(state)
    module.save()

def get_file_modified_time_utc(file_path):
    """
    Gets the UTC timezone-aware modified time of a file at the given file path
    """
    file_timezone = (
        # time.tzname returns a 2 element tuple:
        #   (local non-DST timezone, e.g.: 'EST', local DST timezone, e.g.: 'EDT')
        # pytz.timezone(time.tzname[0])
        pytz.timezone(settings.TIME_ZONE)
        if settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage'
        else pytz.utc
    )
    return file_timezone.localize(
        default_storage.modified_time(file_path)
    ).astimezone(
        pytz.utc
    )


def get_sha1(file_descriptor):
    """
    Get file hex digest (fingerprint).
    """
    sha1 = hashlib.sha1()
    for block in iter(partial(file_descriptor.read, BLOCK_SIZE), ''):
        sha1.update(block)
    file_descriptor.seek(0)
    return sha1.hexdigest()


def get_file_storage_path(locator, file_hash, original_filename):
    """
    Returns the file path for an uploaded SGA submission file
    """
    return (
        six.u(
            '{loc.org}/{loc.course}/{loc.block_type}/{loc.block_id}/{file_hash}{ext}'
        ).format(
            loc=locator,
            file_hash=file_hash,
            ext=os.path.splitext(original_filename)[1]
        )
    )


def file_contents_iter(file_path):
    """
    Returns an iterator over the contents of a file located at the given file path
    """
    file_descriptor = default_storage.open(file_path)
    return iter(partial(file_descriptor.read, BLOCK_SIZE), '')
