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

from youtube import VALID_PRIVACY_STATUSES
from youtube import HttpError
from youtube import yt_get_authenticated_service
from youtube import yt_get_my_uploads_list
from youtube import yt_list_my_uploaded_videos
from youtube import yt_initialize_upload








def upload_sequence(file_to_upload, sequence_title, youtube, args):
    logging.info("Preparing to upload file \"%s\"." % file_to_upload)

    try:
        yt_initialize_upload(file_to_upload, sequence_title, youtube, args)
    except HttpError as e:
        logging.error('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

def merge_sequence(seq, dry_run, logging_level):
    concat_string = None
    file_path = None
    logging.debug("Preparing to merge %d files." % len(seq))
    logging.debug(seq)

    # Output the list of video files to a temporary file, used as input by FFmpeg to concatenate
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

    logging.info("Preparing to run FFmpeg concat command...")

    logging.debug(" ".join(command))
    if dry_run:
        logging.info("Not executing the FFmpeg concat command due to --dry-run parameter.")
    else:
        # Show FFmpeg output only if in INFO or DEBUG mode
        if logging_level in ("INFO", "DEBUG"):
            pipe = sp.Popen(command)
        else:
            pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT)
        out, err = pipe.communicate()
        logging.info("FFmpeg concat command done.")

    return output_file

def merge_and_upload_sequences(new_sequences, dry_run, logging_level, no_net, youtube, args):
    num_sequences = len(new_sequences)
    logging.info("Preparing to merge and upload %d sequences." % num_sequences)

    for idx, seq in enumerate(new_sequences):
        if len(seq) > 1:
            # Combine this sequence into an individual file
            logging.info("Merging sequence %d/%d, which contains %d files." % (idx + 1, num_sequences, len(seq)))
            file_to_upload = merge_sequence(seq, dry_run, logging_level)
        else:
            # No need to merge, as there is only one file
            logging.info("Sequence %d/%d has only one file, no need to merge files." % (idx + 1, num_sequences))
            file_to_upload = seq[0]["file_path"]

        if no_net:
            logging.info("Not uploading sequence %d/%d due to --no-net parameter." % (idx + 1, num_sequences))
        elif dry_run:
            logging.info("Not uploading sequence %d/%d due to --dry-run parameter." % (idx + 1, num_sequences))
        else:
            # Upload the merged sequence
            logging.info("Uploading sequence %d/%d." % (idx + 1, num_sequences))
            sequence_title = get_sequence_title(seq[0]["creation_time"])
            upload_sequence(file_to_upload, sequence_title, youtube, args)

        # Delete the merged file
        logging.info("Deleting merged file for sequence %d/%d." % (idx + 1, num_sequences))
        #TODO: Delete the merged file

def get_sequence_title(creation_time):
    return creation_time.strftime("%Y-%m-%d %H:%M:%S")

def analyze_sequences(sequences, no_net, youtube):
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
            uploads_playlist_id = yt_get_my_uploads_list(youtube)
            if uploads_playlist_id:
                uploaded_videos = yt_list_my_uploaded_videos(uploads_playlist_id, youtube)
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
    parser.add_argument("-t", '--title', help='Will be prepended to the video title')
    parser.add_argument("-ds", '--description', help='Video description')
    parser.add_argument("-c", '--category', help='Numeric video category. See https://developers.google.com/youtube/v3/docs/videoCategories/list')
    parser.add_argument("-k", '--keywords', help='Video keywords, comma separated')
    parser.add_argument("-p", '--privacyStatus', choices=VALID_PRIVACY_STATUSES, default='private', help='Video privacy status.')
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
        logging.info("Authenticating on YouTube...")
        youtube = yt_get_authenticated_service(args)

    # Analyze the files to identify continuous sequences
    sequences = analyze_files(files)
    if(len(sequences) > 0):

        # Check which sequences have already been uploaded and which ones are new
        new_sequences = analyze_sequences(sequences, args.no_net, youtube)
        if(len(new_sequences) > 0):

            # Combine new sequences into individual files and upload the combined files
            merge_and_upload_sequences(new_sequences, args.dry_run, args.logging_level, args.no_net, youtube, args)

    logging.info("Done, exiting.")
