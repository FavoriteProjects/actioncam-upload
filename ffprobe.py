#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Adapted from https://stackoverflow.com/a/36743499
# Author: https://stackoverflow.com/users/451718/andrew-1510

#
# Command line use of 'ffprobe':
#
# ffprobe -loglevel quiet -print_format json \
#         -show_format    -show_streams \
#         video-file-name.mp4
#
# man ffprobe # for more information about ffprobe
#

import subprocess as sp
import json
import datetime


def probe(vid_file_path):
    ''' Give a json from ffprobe command line

    @vid_file_path : The absolute (full) path of the video file, string.
    '''
    if type(vid_file_path) != str:
        raise Exception('Gvie ffprobe a full file path of the video')
        return

    command = ["ffprobe",
            "-loglevel",  "quiet",
            "-print_format", "json",
             "-show_format",
             "-show_streams",
             vid_file_path
             ]

    pipe = sp.Popen(command, stdout=sp.PIPE, stderr=sp.STDOUT)
    out, err = pipe.communicate()
    return json.loads(out.decode('utf-8'))


def duration(metadata_json):
    ''' Video's duration in seconds, return a float number
    '''

    if 'format' in metadata_json:
        if 'duration' in metadata_json['format']:
            return float(metadata_json['format']['duration'])

    if 'streams' in metadata_json:
        # commonly stream 0 is the video
        for s in metadata_json['streams']:
            if 'duration' in s:
                return float(s['duration'])

    # if everything didn't happen,
    # we got here because no single 'return' in the above happen.
    raise Exception('I found no duration')


def creation_time(metadata_json):
    ''' Video's creation time, return a datetime
    '''

    if 'format' in metadata_json:
        if 'tags' in metadata_json['format']:
            if 'creation_time' in metadata_json['format']['tags']:
                return datetime.datetime.strptime((metadata_json['format']['tags']['creation_time']), "%Y-%m-%d %H:%M:%S")

    # if everything didn't happen,
    # we got here because no single 'return' in the above happen.
    raise Exception('I found no creation time')
    #return None
