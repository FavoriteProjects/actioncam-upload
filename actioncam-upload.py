#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import os
import logging
import glob

def analyzeFolder(folder):
    pattern = "%s/*.mp4" % folder
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
        # TODO
        if not folder:
            logging.critical("Automatic folder detection failed. Exiting...")
            sys.exit(1)
    logging.info("Continuing with the %d video files in folder '%s'." % (len(files), folder))
    return (folder, files)

if __name__ == "__main__":
    folder = None
    files = None

    parser = argparse.ArgumentParser(description="Automatically upload videos from an Action Cam to YouTube.")
    parser.add_argument("--folder", required=False, help="Path to folder containing the video files")
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Validate if the provided folder is valid, or try to automatically detect the folder
    (folder, files) = detectFolder(args)


    logging.info("Done, exiting.")
