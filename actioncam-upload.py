#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import os
import logging
import glob
import ffprobe
from datetime import timedelta
import subprocess as sp

#import argparse
#import httplib
import httplib2
# import os
# import random
# import time
#
# import google.oauth2.credentials
# import google_auth_oauthlib.flow
# from googleapiclient.http import MediaFileUpload



from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run_flow




# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
# RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
#   httplib.IncompleteRead, httplib.ImproperConnectionState,
#   httplib.CannotSendRequest, httplib.CannotSendHeader,
#   httplib.ResponseNotReady, httplib.BadStatusLine)
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = 'client_secret.json'

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly',
          'https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

VALID_PRIVACY_STATUSES = ('public', 'private', 'unlisted')

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def yt_get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=SCOPES, message=MISSING_CLIENT_SECRETS_MESSAGE)
    storage = Storage("actioncam-upload-oauth2.json")
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)
    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials, cache_discovery=False)

def yt_get_my_uploads_list():
    # Retrieve the contentDetails part of the channel resource for the
    # authenticated user's channel.
    channels_response = youtube.channels().list(
        mine=True,
        part='contentDetails'
    ).execute()

    for channel in channels_response['items']:
        # From the API response, extract the playlist ID that identifies the list
        # of videos uploaded to the authenticated user's channel.
        return channel['contentDetails']['relatedPlaylists']['uploads']
    return None

def yt_list_my_uploaded_videos(uploads_playlist_id):
    uploaded_videos = []
    # Retrieve the list of videos uploaded to the authenticated user's channel.
    playlistitems_list_request = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part='snippet',
        maxResults=5
    )

    logging.info('Videos in list %s' % uploads_playlist_id)
    while playlistitems_list_request:
        playlistitems_list_response = playlistitems_list_request.execute()

        # Print information about each video.
        for playlist_item in playlistitems_list_response['items']:
            title = playlist_item['snippet']['title']
            video_id = playlist_item['snippet']['resourceId']['videoId']
            uploaded_videos.append(title)
            logging.info("Title: '%s' (ID: %s)" % (title, video_id))

        playlistitems_list_request = youtube.playlistItems().list_next(playlistitems_list_request, playlistitems_list_response)
    return uploaded_videos








def upload_sequence(merged_file):
    logging.info("Preparing to upload merged file \"%s\"." % merged_file)

def merge_sequence(seq, dry_run, logging_level):
    concat_string = None
    file_path = None
    logging.debug("Preparing to merge %d files." % len(seq))
    logging.debug(seq)

    # Output the list of video files to a temporary file, used as input by ffmpeg to concatenate
    file_paths = [f["file_path"] for f in seq]
    with open('/tmp/actioncam-upload-files.txt', 'w') as f:
        print("file '%s'" % "'\nfile '".join(file_paths), file=f)

    output_file = "/tmp/%s" % os.path.split(seq[0]["file_path"])[1] #Use the filename of the first file in this sequence

    #ffmpeg -f concat -safe 0 -i /tmp/actioncam-upload-files.txt -c copy /tmp/output.mov
    command = ["ffmpeg",
               "-y",
               "-f",  "concat",
               "-safe",  "0",
               "-i", "/tmp/actioncam-upload-files.txt",
               "-c", "copy",
               output_file
              ]

    logging.info("Preparing to run ffmpeg concat command...")

    logging.debug(" ".join(command))
    if dry_run:
        logging.info("Not executing the ffmpeg concat command due to --dry-run parameter.")
    else:
        # Show ffmpeg output only if in INFO or DEBUG mode
        if logging_level in ("INFO", "DEBUG"):
            pipe = sp.Popen(command)
        else:
            pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT)
        out, err = pipe.communicate()
        logging.info("ffmpeg concat command done.")

    return output_file

def merge_and_upload_sequences(new_sequences, dry_run, logging_level, no_net):
    num_sequences = len(new_sequences)
    logging.info("Preparing to merge and upload %d sequences." % num_sequences)

    for idx, seq in enumerate(new_sequences):
        # Combine this sequence into an individual file
        logging.info("Merging sequence %d/%d, which contains %d files." % (idx + 1, num_sequences, len(seq)))
        merged_file = merge_sequence(seq, dry_run, logging_level)

        if no_net:
            logging.info("Not uploading sequence %d/%d due to --no-net parameter." % (idx + 1, num_sequences))
        elif dry_run:
            logging.info("Not uploading sequence %d/%d due to --dry-run parameter." % (idx + 1, num_sequences))
        else:
            # Upload the merged sequence
            logging.info("Uploading sequence %d/%d." % (idx + 1, num_sequences))
            upload_sequence(merged_file)

        # Delete the merged file
        logging.info("Deleting merged file for sequence %d/%d." % (idx + 1, num_sequences))
        #TODO: Delete the merged file

def get_sequence_title(creation_time):
    return creation_time.strftime("%Y-%m-%d %H:%M:%S")

def analyze_sequences(sequences, no_net):
    sequence_title = None
    new_sequences = []
    uploaded_videos = []

    num_sequences = len(sequences)
    logging.debug("Starting to analyze %d sequences." % num_sequences)

    if no_net:
        logging.info("Not getting the list of videos uploaded to YouTube due to --no-net parameter.")
    else:
        # Get the list of videos uploaded to YouTube
        try:
            uploads_playlist_id = yt_get_my_uploads_list()
            if uploads_playlist_id:
                uploaded_videos = yt_list_my_uploaded_videos(uploads_playlist_id)
                logging.debug("Uploaded videos: %s" % uploaded_videos)
            else:
                logging.info('There is no uploaded videos playlist for this user.')
        except HttpError as e:
            logging.debug('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

    for idx, seq in enumerate(sequences):
        logging.info("Analyzing sequence %d/%d, which contains %d files." % (idx + 1, num_sequences, len(seq)))
        logging.debug(seq)
        if len(seq) < 1:
            raise Exception("No files in sequence (should never happen, something has gone wrong...)")

        # Use the creation time of the first file in the sequence as name for the entire sequence
        sequence_title = get_sequence_title(seq[0]["creation_time"])

        # Check if this sequence has already uploaded
        logging.info("Checking if sequence %s has already been uploaded." % sequence_title)
        if sequence_title in uploaded_videos:
            logging.info("This sequence %s is NOT new!" % sequence_title)
        else:
            logging.info("This sequence %s is new!" % sequence_title)
            new_sequences.append(seq)

    logging.info("There are %d new sequences to upload." % len(new_sequences))
    logging.debug(new_sequences)
    return new_sequences


def analyze_files(files):
    sequences = []
    new_sequence = []
    video_metadata = None
    duration = None
    videos_by_creation_time = {}
    creation_times = []
    previous_end_time = None

    num_files = len(files)
    logging.debug("Starting to analyze %d video files." % num_files)

    for idx, f in enumerate(files):
        logging.info("Analyzing file %d/%d: '%s'" % (idx + 1, num_files, f))
        video_metadata = ffprobe.probe(f)
        duration = ffprobe.duration(video_metadata)
        creation_time = ffprobe.creation_time(video_metadata)
        logging.info("File '%s': Duration: '%.3f', Creation Time: '%s'" %(f, duration, creation_time))
        creation_times.append(creation_time)
        videos_by_creation_time[creation_time] = {"file_path": f, "duration": duration}

    # Sort the creation dates
    creation_times.sort()
    logging.debug("creation_times: %s" % creation_times)

    # Loop over the sorted creation times, identify adjacent videos to recreate full sequences
    for ts in creation_times:
        v = videos_by_creation_time[ts]
        if not previous_end_time:
            new_sequence = [{"file_path": v["file_path"], "duration": v["duration"], "creation_time": ts}]
        else:
            # Videos less than 30 seconds apart are considered part of the same sequence
            if ts - previous_end_time < timedelta(seconds=30):
                # Add this video to the current sequences
                new_sequence.append({"file_path": v["file_path"], "duration": v["duration"], "creation_time": ts})
            else:
                # Save the previous sequence and start a new sequence
                sequences.append(new_sequence)
                new_sequence = [{"file_path": v["file_path"], "duration": v["duration"], "creation_time": ts}]
        # Save this video's end time to compare with the next video's start time
        previous_end_time = ts + timedelta(seconds=videos_by_creation_time[ts]["duration"])

    # Store the last new sequence
    if new_sequence:
        sequences.append(new_sequence)
    logging.info("Sequences identified: %d" % len(sequences))
    logging.debug(sequences)

    return sequences

def analyze_folder(folder):
    #pattern = "%s/*.mp4" % folder
    pattern = "%s/*.MOV" % folder
    logging.debug("Checking files matching pattern '%s'" % pattern)
    files = glob.glob(pattern)
    logging.info("There are %d files matching the pattern '%s':\n%s" % (len(files), pattern, '\n'.join(files)))

    return files if len(files) > 0 else None

def detect_folder(args):
    folder = None
    files = None
    if args.folder:
        check_folder = os.path.abspath(args.folder)
        logging.debug("Checking if provided folder '%s' is valid." % check_folder)
        # Check if provided folder is valid
        if not os.path.exists(check_folder):
            logging.critical("Provided folder does not exist. Exiting...")
            sys.exit(1)
        folder = check_folder
        logging.info("The provided folder '%s' exists." % folder)
        files = analyze_folder(folder)
        if not files:
            logging.critical("The provided folder '%s' does not contain any processable video files. Exiting..." % check_folder)
            sys.exit(1)
    else:
        # Try to identify the folder automatically
        logging.debug("Start automatic folder detection.")
        # TODO
        if not folder:
            logging.critical("Automatic folder detection failed. Exiting...\n(You can point to an explicit folder using the `--folder` argument).")
            sys.exit(1)
    logging.info("Continuing with the %d video files in folder '%s'." % (len(files), folder))
    return (folder, files)

if __name__ == "__main__":
    folder = None
    files = None
    sequences = None
    new_sequences = None
    youtube = None

    parser = argparse.ArgumentParser(description="Automatically upload videos from an Action Cam to YouTube.")
    parser.add_argument("-f", "--folder", required=False, help="Path to folder containing the video files.")
    parser.add_argument("-dr", "--dry-run", action='store_true', required=False, help="Do not combine files or upload.")
    parser.add_argument("-nn", "--no-net", action='store_true', required=False, help="Do not use the network (no checking on YouTube or upload)")
    parser.add_argument(
        '-d', '--debug',
        help="Print lots of debugging statements",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '-v', '--verbose',
        help="Be verbose",
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    args = parser.parse_args()

    if args.loglevel:
        logging.basicConfig(level=args.loglevel)
        args.logging_level = logging.getLevelName(logging.getLogger().getEffectiveLevel())
    args.noauth_local_webserver = True

    # Validate if the provided folder is valid, or try to automatically detect the folder
    (folder, files) = detect_folder(args)

    if args.no_net:
        logging.info("Not authenticating on YouTube due to --no-net parameter.")
    else:
        # Authenticate on YouTube
        youtube = yt_get_authenticated_service(args)

    # Analyze the files to identify continuous sequences
    sequences = analyze_files(files)
    if(len(sequences) > 0):

        # Check which sequences have already been uploaded and which ones are new
        new_sequences = analyze_sequences(sequences, args.no_net)
        if(len(new_sequences) > 0):

            # Combine new sequences into individual files and upload the combined files
            merge_and_upload_sequences(new_sequences, args.dry_run, args.logging_level, args.no_net)

    logging.info("Done, exiting.")
