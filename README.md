# actioncam-upload
Automatically upload videos from an Action Cam to the web (YouTube)

[![Build Status](https://travis-ci.com/e2jk/actioncam-upload.svg?branch=master)](https://travis-ci.com/e2jk/actioncam-upload)

Usage:
======

```
usage: actioncam-upload.py [-h] [-f FOLDER] [-t TITLE] [-ds DESCRIPTION]
                           [-c CATEGORY] [-k KEYWORDS]
                           [-p {public,private,unlisted}] [-dr] [-nn] [-nc]
                           [-min MIN_LENGTH] [-max MAX_LENGTH] [-d] [-v]

Automatically upload videos from an Action Cam to YouTube.

optional arguments:
  -h, --help            show this help message and exit
  -f FOLDER, --folder FOLDER
                        Path to folder containing the video files.
  -t TITLE, --title TITLE
                        Will be prepended to the video title
  -ds DESCRIPTION, --description DESCRIPTION
                        Video description
  -c CATEGORY, --category CATEGORY
                        Numeric video category. See https://developers.google.
                        com/youtube/v3/docs/videoCategories/list
  -k KEYWORDS, --keywords KEYWORDS
                        Video keywords, comma separated
  -p {public,private,unlisted}, --privacyStatus {public,private,unlisted}
                        Video privacy status.
  -dr, --dry-run        Do not combine files or upload.
  -nn, --no-net         Do not use the network (no checking on YouTube or
                        upload).
  -nc, --no-compression
                        Do not compress the files before uploading.
  -min MIN_LENGTH, --min-length MIN_LENGTH
                        Do not consider sequences shorter than this number of
                        minutes.
  -max MAX_LENGTH, --max-length MAX_LENGTH
                        Do not consider sequences longer than this number of
                        minutes.
  -d, --debug           Print lots of debugging statements
  -v, --verbose         Be verbose
```
