#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import os
import logging
import glob
import ffprobe
import tempfile
import shutil
from datetime import timedelta
import subprocess as sp

from youtube import VALID_PRIVACY_STATUSES
from youtube import HttpError
from youtube import yt_get_authenticated_service
from youtube import yt_get_my_uploads_list
from youtube import yt_list_my_uploaded_videos
from youtube import yt_initialize_upload








def upload_sequence(file_to_upload, sequence_title, youtube, args):
    logging.debug("Preparing to upload file \"%s\"." % file_to_upload)

    try:
        yt_initialize_upload(file_to_upload, sequence_title, youtube, args)
    except HttpError as e:
        logging.error('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
        logging.critical("Exiting...")
        sys.exit(13)
    except KeyboardInterrupt as e:
        logging.warning("Aborting upload (KeyboardInterrupt)")

def merge_sequence(seq, dry_run, logging_level):
    concat_string = None
    file_path = None
    temp_file_ffmpeg = "/tmp/actioncam-upload-files.txt"
    logging.debug("Preparing to merge %d files." % len(seq))
    logging.debug(seq)

    # Output the list of video files to a temporary file, used as input by FFmpeg to concatenate
    file_paths = [f["file_path"] for f in seq]
    with open(temp_file_ffmpeg, 'w') as f:
        print("file '%s'" % "'\nfile '".join(file_paths), file=f)

    output_file = "/tmp/%s" % os.path.split(seq[0]["file_path"])[1] #Use the filename of the first file in this sequence

    #ffmpeg -f concat -safe 0 -i /tmp/actioncam-upload-files.txt -c copy /tmp/output.mov
    command = ["ffmpeg",
               "-y",
               "-f", "concat",
               "-safe", "0",
               "-i", "/tmp/actioncam-upload-files.txt",
               "-c", "copy",
               output_file
              ]
    logging.debug("Running FFmpeg concat command...")
    logging.debug(" ".join(command))

    if dry_run:
        logging.info("Not executing the FFmpeg concat command due to --dry-run parameter.")
    else:
        # Show FFmpeg output only if in INFO or DEBUG mode
        if "DEBUG" == logging_level:
            pipe = sp.Popen(command)
        else:
            pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT)
        out, err = pipe.communicate()
        if 0 != pipe.returncode:
            logging.error("The FFmpeg concat command returned a non-zero code: %d" % pipe.returncode)
            logging.critical("Exiting...")
            sys.exit(17)
        logging.debug("FFmpeg concat command done.")

    logging.debug("Deleting temporary FFmpeg merge file.")
    if os.path.isfile(temp_file_ffmpeg):
        os.remove(temp_file_ffmpeg)
        logging.debug("File '%s' removed." % temp_file_ffmpeg)

    return output_file

def compress_sequence(seq, tempdir, dry_run, logging_level, id_sequence, num_sequences):
    logging.debug("Preparing to compress files into temporary directory '%s'." % tempdir)
    logging.debug(seq)

    for idx, f in enumerate(seq):
        compressed_file = "%s/%s" % (tempdir, os.path.split(f["file_path"])[1])

        # Exit if input file doesn't exist (could happen if the actioncam got unplugged)
        if not os.path.isfile(f["file_path"]):
            logging.error("The file doesn't exist (actioncam disconnected?): '%s'" % f["file_path"])
            logging.critical("Exiting...")
            sys.exit(15)

        # Reduce the resolution by 4 (1/2h 1/2w) and reduce framerate to 25 images/second
        #ffmpeg -i 20190121_085007.MOV -vf "scale=iw/2:ih/2" -r 25 20190121_085007-div2-r25.mov
        command = ["ffmpeg",
                   "-i", f["file_path"],
                   "-vf", "scale=iw/2:ih/2",
                   "-r", "25",
                   compressed_file
                  ]
        logging.info("Running FFmpeg compress command for file %d/%d of sequence %d/%d..." % (idx + 1, len(seq), id_sequence, num_sequences))
        logging.debug(" ".join(command))

        if dry_run:
            logging.info("Not executing the FFmpeg compress command due to --dry-run parameter.")
        else:
            # Show FFmpeg output only if in INFO or DEBUG mode
            if "DEBUG" == logging_level:
                pipe = sp.Popen(command)
            else:
                pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT)
            out, err = pipe.communicate()
            if 0 != pipe.returncode:
                logging.error("The FFmpeg compress command returned a non-zero code: %d" % pipe.returncode)
                logging.critical("Exiting...")
                sys.exit(16)
            logging.debug("FFmpeg compress command done.")
            # Update the sequence information with the path to the new compressed file
            f["file_path"] = compressed_file

    if not dry_run:
        logging.debug("Updated sequence with paths to the temporary compressed files:")
        logging.debug(seq)
    return seq

def compress_merge_and_upload_sequences(new_sequences, pre_copy_folders, youtube, args):
    tempdir = None
    num_sequences = len(new_sequences)
    logging.debug("Preparing to compress, merge and upload %d sequences." % num_sequences)

    for idx, seq in enumerate(new_sequences):
        if args.no_compression:
            logging.info("Not compressing sequence %d/%d due to --no-compression parameter." % (idx + 1, num_sequences))
        else:
            # Create a temporary folder to hold the compressed files
            # Do create (and delete) a new folder for each sequence, to save disk space
            tempdir = tempfile.mkdtemp()
            # Reduce resolution and framerate
            logging.info("Compressing sequence %d/%d, which contains %d files." % (idx + 1, num_sequences, len(seq)))
            seq = compress_sequence(seq, tempdir, args.dry_run, args.logging_level, idx + 1, num_sequences)
            # seq[] now contains the paths to the temporary compressed files

        if len(seq) > 1:
            # Combine this sequence into an individual file
            logging.info("Merging sequence %d/%d, which contains %d files." % (idx + 1, num_sequences, len(seq)))
            file_to_upload = merge_sequence(seq, args.dry_run, args.logging_level)
        else:
            # No need to merge, as there is only one file
            logging.info("Sequence %d/%d has only one file, no need to merge files." % (idx + 1, num_sequences))
            file_to_upload = seq[0]["file_path"]

        if args.no_net:
            logging.info("Not uploading sequence %d/%d due to --no-net parameter." % (idx + 1, num_sequences))
        elif args.dry_run:
            logging.info("Not uploading sequence %d/%d due to --dry-run parameter." % (idx + 1, num_sequences))
        else:
            # Upload the merged sequence
            logging.info("Uploading sequence %d/%d." % (idx + 1, num_sequences))
            sequence_title = get_sequence_title(seq[0]["creation_time"])
            try:
                upload_sequence(file_to_upload, sequence_title, youtube, args)
            except Exception as e:
                # Delete the temporary folders and files, since the program execution stops here
                delete_temporary_files(seq, file_to_upload, idx, num_sequences, args, tempdir, pre_copy_folders)
                raise
        # Delete the temporary folders and files
        delete_temporary_files(seq, file_to_upload, idx, num_sequences, args, tempdir, pre_copy_folders)

def delete_temporary_files(seq, file_to_upload, idx, num_sequences, args, tempdir, pre_copy_folders):
    if len(seq) > 1:
        # Delete the merged file (if there is only one file, no temporary merged file was created, so no need to delete)
        if os.path.isfile(file_to_upload):
            logging.debug("Deleting merged file for sequence %d/%d." % (idx + 1, num_sequences))
            os.remove(file_to_upload)
            logging.debug("File '%s' removed." % file_to_upload)

    if not args.no_compression:
        # Delete the compressed files' temporary folder
        shutil.rmtree(tempdir)
        logging.debug("The temporary folder with the compressed files for this sequence has been removed.")

    if pre_copy_folders != []:
        # Delete the temporary folder and files where the original files where copied to
        shutil.rmtree(pre_copy_folders[idx])
        logging.debug("The temporary folder where the original files where copied to has been removed.")

def get_sequence_title(creation_time):
    return creation_time.strftime("%Y-%m-%d %H:%M:%S")

def pre_copy(new_sequences):
    logging.debug("Pre-copying the files from the actioncam to a temporary folder")
    pre_copy_folders = []
    for idx, seq in enumerate(new_sequences):
        # Create a new temporary folder for this sequence's files
        pre_copy_folders.append(tempfile.mkdtemp())
        for idx2, files in enumerate(seq):
            logging.info("Pre-copying file %d/%d of sequence %d/%d..." % (idx2 + 1, len(seq), idx + 1, len(new_sequences)))
            # Copy the files from that sequence to that new temporary folder
            new_filename = os.path.join(pre_copy_folders[idx], os.path.split(files["file_path"])[1])
            shutil.copy(files["file_path"], new_filename)
            # Update that file's path to the new temporary path
            files["file_path"] = new_filename
    return (new_sequences, pre_copy_folders)

def analyze_sequences(sequences, youtube, args):
    sequence_title = None
    new_sequences = []
    uploaded_videos = []

    num_sequences = len(sequences)
    logging.debug("Starting to analyze %d sequences." % num_sequences)

    if args.no_net:
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
            logging.critical("Exiting...")
            sys.exit(14)

    if args.interactive:
        print("Entering Interactive mode:")

    for idx, seq in enumerate(sequences):
        logging.debug("Analyzing sequence %d/%d, which contains %d files." % (idx + 1, num_sequences, len(seq)))
        logging.debug(seq)
        if len(seq) < 1:
            raise Exception("No files in sequence (should never happen, something has gone wrong...)")

        # Use the creation time of the first file in the sequence as name for the entire sequence
        sequence_title = get_sequence_title(seq[0]["creation_time"])

        # Check if this sequence has already uploaded
        if sequence_title in uploaded_videos:
            extra_info = "%s (%d files)." % (sequence_title, len(seq))
            if not args.interactive:
                logging.info("OLD  sequence %2d/%d %s" % (idx + 1, num_sequences, extra_info))
            else:
                print("[%d] OLD  sequence %s" % (idx, extra_info))
        else:
            is_new_sequence = True
            # If bounds supplied, check if the duration of this sequence is within them
            if args.min_length or args.max_length:
                # Calculate duration of this sequence
                sequence_length = 0
                for idx2, vid in enumerate(seq):
                    sequence_length += vid["duration"]
                sequence_length /= 60 # Convert seconds in minutes
                if args.min_length and sequence_length < args.min_length:
                    extra_info = "%s (%d files), duration %.1f < --min-length=%d." % (sequence_title, len(seq), sequence_length, args.min_length)
                    if not args.interactive:
                        logging.info("SKIP sequence %2d/%d %s" % (idx + 1, num_sequences, extra_info))
                    else:
                        print("[%d] SKIP sequence %s" % (idx, extra_info))
                    is_new_sequence = False
                elif args.max_length and sequence_length > args.max_length:
                    extra_info = "%s (%d files), duration %.1f > --max-length=%d." % (sequence_title, len(seq), sequence_length, args.max_length)
                    if not args.interactive:
                        logging.info("SKIP sequence %2d/%d %s" % (idx + 1, num_sequences, extra_info))
                    else:
                        print("[%d] SKIP sequence %s" % (idx, extra_info))
                    is_new_sequence = False
            if is_new_sequence:
                extra_info = "%s (%d files)." % (sequence_title, len(seq))
                if not args.interactive:
                    logging.info("NEW  sequence %2d/%d %s" % (idx + 1, num_sequences, extra_info))
                else:
                    print("[%d] NEW  sequence %s" % (idx, extra_info))
                new_sequences.append(seq)

    logging.info("There are %d new sequences to upload." % len(new_sequences))
    logging.debug(new_sequences)

    if args.interactive:
        new_sequences = interactive_sequence_selection(sequences, new_sequences)
    return new_sequences

def interactive_sequence_selection(sequences, new_sequences):
    if len(sequences) < 1:
        raise Exception("No sequences were passed (should never happen, something has gone wrong...)")
    new_seq_ids = []
    num_sequences = len(sequences)
    if len(new_sequences) > 0:
        extra_string = "Press ENTER to upload the %d NEW sequences above, 'q' to stop the program" % len(new_sequences)
    else:
        extra_string = "Press ENTER or 'q' to stop the program"
    s = input("Press ENTER to %s or indicate an individual sequence ID to upload: " % extra_string)
    while s != "":
        if s.lower() == "q":
            print("Exiting...")
            sys.exit(18)
        try:
            seq_id = int(s)
            if seq_id < 0 or seq_id > num_sequences - 1:
                print("Please enter a number between 0 and %d" % (num_sequences - 1))
            else:
                if seq_id not in new_seq_ids:
                    new_seq_ids.append(seq_id)
                else:
                    print("ALREADY IN LIST")
        except ValueError:
            print("'%s' is not a number, please try again." % s)
        s = input("Press ENTER to stop selecting new sequences, or indicate an individual sequence ID to upload: ")
    if new_seq_ids == []:
        # Nothing to change in new_sequences
        logging.info("Continue uploading the sequences already in 'new_sequences'")
    else:
        # Empty new_sequences and populate with the chosen sequences
        new_sequences = []
        for s in new_seq_ids:
            new_sequences.append(sequences[s])
    return new_sequences

def analyze_files(files):
    video_metadata = None
    duration = None
    videos_by_creation_time = {}
    creation_times = []

    num_files = len(files)
    logging.info("Starting to analyze %d video files..." % num_files)

    for idx, f in enumerate(files):
        logging.debug("Analyzing file %d/%d: '%s'" % (idx + 1, num_files, f))
        if not os.path.isfile(f):
            raise Exception("There is no file to analyze at '%s'" % f)
        video_metadata = ffprobe.probe(f)
        duration = ffprobe.duration(video_metadata)
        creation_time = ffprobe.creation_time(video_metadata)
        logging.debug("File '%s': Duration: '%.3f', Creation Time: '%s'" %(f, duration, creation_time))
        creation_times.append(creation_time)
        videos_by_creation_time[creation_time] = {"file_path": f, "duration": duration}

    return identify_sequences(videos_by_creation_time, creation_times)

def identify_sequences(videos_by_creation_time, creation_times):
    sequences = []
    new_sequence = []
    previous_end_time = None

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
    logging.info("There are %d files matching the pattern '%s'." % (len(files), pattern))
    logging.debug('\n'.join(files))

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
            sys.exit(10)
        folder = check_folder
        logging.debug("The provided folder '%s' exists." % folder)
        files = analyze_folder(folder)
        if not files:
            logging.critical("The provided folder '%s' does not contain any processable video files. Exiting..." % check_folder)
            sys.exit(11)
    else:
        # Try to identify the folder automatically
        logging.debug("Start automatic folder detection.")
        # TODO
        if not folder:
            logging.critical("Automatic folder detection failed. Exiting...\n(You can point to an explicit folder using the `--folder` argument).")
            sys.exit(12)
    logging.debug("Continuing with the %d files in folder '%s'." % (len(files), folder))
    return (folder, files)

def parse_args(arguments):
    parser = argparse.ArgumentParser(description="Automatically upload videos from an Action Cam to YouTube.")
    parser.add_argument("-f", "--folder", required=False, help="Path to folder containing the video files.")
    parser.add_argument("-t", '--title', help='Will be prepended to the video title')
    parser.add_argument("-ds", '--description', help='Video description')
    parser.add_argument("-c", '--category', help='Numeric video category. See https://developers.google.com/youtube/v3/docs/videoCategories/list')
    parser.add_argument("-k", '--keywords', help='Video keywords, comma separated')
    parser.add_argument("-p", '--privacyStatus', choices=VALID_PRIVACY_STATUSES, default='private', help='Video privacy status.')
    parser.add_argument("-i", '--interactive', action='store_true', required=False, help="Manually select which sequences to upload.")
    parser.add_argument("-pc", '--pre-copy', action='store_true', required=False, help="Copy the files from the actioncam to a temporary folder on the computer, useful in case the actioncam gets disconnected.")
    parser.add_argument("-dr", "--dry-run", action='store_true', required=False, help="Do not combine files or upload.")
    parser.add_argument("-nn", "--no-net", action='store_true', required=False, help="Do not use the network (no checking on YouTube or upload).")
    parser.add_argument("-nc", "--no-compression", action='store_true', required=False, help="Do not compress the files before uploading.")
    parser.add_argument("-min", "--min-length", type=int, help="Do not consider sequences shorter than this number of minutes.")
    parser.add_argument("-max", "--max-length", type=int, help="Do not consider sequences longer than this number of minutes.")
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
    args = parser.parse_args(arguments)

    # Add some more arguments
    if args.loglevel:
        logging.basicConfig(level=args.loglevel)
        args.logging_level = logging.getLevelName(args.loglevel)
    args.noauth_local_webserver = True

    return args

def main():
    folder = None
    files = None
    sequences = None
    new_sequences = None
    youtube = None

    # Parse the provided command-line arguments
    args = parse_args(sys.argv[1:])

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
        new_sequences = analyze_sequences(sequences, youtube, args)

        pre_copy_folders = []
        if(args.pre_copy):
            # Copy the files from the actioncam to a temporary folder on the computer, useful in case the actioncam gets disconnected
            (new_sequences, pre_copy_folders) = pre_copy(new_sequences)

        if(len(new_sequences) > 0):
            # Combine new sequences into individual files and upload the combined files
            compress_merge_and_upload_sequences(new_sequences, pre_copy_folders, youtube, args)

    logging.info("Done, exiting.")

def init():
    if __name__ == "__main__":
        main()

init()
