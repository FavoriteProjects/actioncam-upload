#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import os
import logging
import glob
import ffprobe
from datetime import timedelta


def uploadSequences(newSequences):
    pass

def mergeSequences(newSequences):
    pass

def analyzeSequences(sequences):
    pass

def analyzeFiles(files):
    sequences = []
    new_sequence = []
    videoMetadata = None
    duration = None
    videos_by_creation_time = {}
    creation_times = []
    previous_end_time = None

    for f in files:
        logging.debug("Analyzing file '%s'" % f)
        videoMetadata = ffprobe.probe(f)
        duration = ffprobe.duration(videoMetadata)
        creation_time = ffprobe.creation_time(videoMetadata)
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

def analyzeFolder(folder):
    #pattern = "%s/*.mp4" % folder
    pattern = "%s/*.MOV" % folder
    logging.debug("Checking files matching pattern '%s'" % pattern)
    files = glob.glob(pattern)
    logging.info("There are %d files matching the pattern '%s':\n%s" % (len(files), pattern, '\n'.join(files)))

    return files if len(files) > 0 else None

def detectFolder(args):
    folder = None
    files = None
    if args.folder:
        checkFolder = os.path.abspath(args.folder)
        logging.debug("Checking if provided folder '%s' is valid." % checkFolder)
        # Check if provided folder is valid
        if not os.path.exists(checkFolder):
            logging.critical("Provided folder does not exist. Exiting...")
            sys.exit(1)
        folder = checkFolder
        logging.info("The provided folder '%s' exists." % folder)
        files = analyzeFolder(folder)
        if not files:
            logging.critical("The provided folder '%s' does not contain any processable video files. Exiting..." % checkFolder)
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
    newSequences = None

    parser = argparse.ArgumentParser(description="Automatically upload videos from an Action Cam to YouTube.")
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
    parser.add_argument("-f", "--folder", required=False, help="Path to folder containing the video files")
    args = parser.parse_args()

    if args.loglevel:
        logging.basicConfig(level=args.loglevel)

    # Validate if the provided folder is valid, or try to automatically detect the folder
    (folder, files) = detectFolder(args)

    # Analyze the files to identify continuous sequences
    sequences = analyzeFiles(files)

    # Check which sequences have already been uploaded and which ones are new
    newSequences = analyzeSequences(sequences)

    # Combine new sequences into individual files
    mergeSequences(newSequences)

    # Upload new sequences
    uploadSequences(newSequences)

    logging.info("Done, exiting.")
