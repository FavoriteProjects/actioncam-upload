#!/usr/bin/env python
# -*- coding: utf-8 -*-

# https://realpython.com/python-testing/

# Running the tests:
# $ python -m unittest -v test
# Checking the coverage of the tests:
# $ coverage run --include=actioncam-upload.py test.py && coverage html

import unittest
import sys
import logging
import datetime
import tempfile
import shutil
import os
import copy

sys.path.append('.')
target = __import__("actioncam-upload")


sample_sequences = [
    [
        {'duration': 300.0, 'file_path': '/tmp/vids/20190121_085007.MOV', 'creation_time': datetime.datetime(2019, 1, 21, 8, 50, 7)},
        {'duration': 300.0, 'file_path': '/tmp/vids/20190121_085508.MOV', 'creation_time': datetime.datetime(2019, 1, 21, 8, 55, 8)},
        {'duration': 300.0, 'file_path': '/tmp/vids/20190121_090008.MOV', 'creation_time': datetime.datetime(2019, 1, 21, 9, 0, 8)},
        {'duration': 216.75, 'file_path': '/tmp/vids/20190121_090508.MOV', 'creation_time': datetime.datetime(2019, 1, 21, 9, 5, 8)}
    ],
    [
        {'duration': 300.0, 'file_path': '/tmp/vids/20190125_162220.MOV', 'creation_time': datetime.datetime(2019, 1, 25, 16, 22, 20)},
        {'duration': 300.0, 'file_path': '/tmp/vids/20190125_162721.MOV', 'creation_time': datetime.datetime(2019, 1, 25, 16, 27, 21)},
        {'duration': 300.0, 'file_path': '/tmp/vids/20190125_163221.MOV', 'creation_time': datetime.datetime(2019, 1, 25, 16, 32, 21)},
        {'duration': 300.0, 'file_path': '/tmp/vids/20190125_163721.MOV', 'creation_time': datetime.datetime(2019, 1, 25, 16, 37, 21)}
    ],
    [
        {'duration': 300.0, 'file_path': '/tmp/vids/20190129_082825.MOV', 'creation_time': datetime.datetime(2019, 1, 29, 8, 28, 26)},
        {'duration': 300.0, 'file_path': '/tmp/vids/20190129_083327.MOV', 'creation_time': datetime.datetime(2019, 1, 29, 8, 33, 27)},
        {'duration': 286.0, 'file_path': '/tmp/vids/20190129_083826.MOV', 'creation_time': datetime.datetime(2019, 1, 29, 8, 38, 27)}
    ]
]

class TestCompressMergeAndUploadSequences(unittest.TestCase):
    def test_compress_merge_and_upload_sequences_no_net(self):
        """
        Test the compress_merge_and_upload_sequences() function
        """
        args = target.parse_args(['--no-net', '--verbose'])
        youtube = None
        # Using a deep copy of the sequence, otherwise running compress_sequence()
        # without --dry-run modifies the elements, and the sample_sequences array
        # gets modified which messes up other tests later on.
        target.compress_merge_and_upload_sequences(copy.deepcopy(sample_sequences), youtube, args)
        # Nothing to assert (the individual functions are tested separately for
        # their returns), just confirming no Exception is thrown.

    def test_compress_merge_and_upload_sequences_no_net_no_compression(self):
        """
        Test the compress_merge_and_upload_sequences() function
        """
        args = target.parse_args(['--no-net', '--verbose', '--no-compression'])
        youtube = None
        target.compress_merge_and_upload_sequences(sample_sequences, youtube, args)
        # Nothing to assert (the individual functions are tested separately for
        # their returns), just confirming no Exception is thrown.

class TestMergeSequence(unittest.TestCase):
    def test_merge_sequence_dry_run(self):
        """
        Test the merge_sequence() function with --dry-run (doesn't run the ffmpeg command)
        """
        args = target.parse_args(['--dry-run', '--verbose'])
        file_to_upload = target.merge_sequence(sample_sequences[0], args.dry_run, args.logging_level)
        self.assertEqual(file_to_upload, "/tmp/%s" % os.path.split(sample_sequences[0][0]["file_path"])[1])

    def test_merge_sequence_ffmpeg_verbose(self):
        """
        Test the merge_sequence() function, running the FFmpeg merge command with --verbose
        """
        args = target.parse_args(['--verbose'])
        file_to_upload = target.merge_sequence(sample_sequences[0], args.dry_run, args.logging_level)
        self.assertEqual(file_to_upload, "/tmp/%s" % os.path.split(sample_sequences[0][0]["file_path"])[1])

    def test_merge_sequence_ffmpeg_debug(self):
        """
        Test the merge_sequence() function, running the FFmpeg merge command with --debug
        This will cause the output of ffmpeg (including the following error
        message) to be displayed in the output of the test suite, this is NOT a problem:
            Impossible to open '/tmp/vids/20190121_085007.MOV'
            /tmp/actioncam-upload-files.txt: No such file or directory
        """
        args = target.parse_args(['--debug'])
        file_to_upload = target.merge_sequence(sample_sequences[0], args.dry_run, args.logging_level)
        self.assertEqual(file_to_upload, "/tmp/%s" % os.path.split(sample_sequences[0][0]["file_path"])[1])

class TestCompressSequence(unittest.TestCase):
    def test_compress_sequence_dry_run(self):
        """
        Test the compress_sequence() function with --dry-run
        Nothing should change to the sequence
        """
        args = target.parse_args(['--dry-run', '--verbose'])
        tempdir = tempfile.mkdtemp()
        # Call the function with the first sequence from sample_sequences
        seq = target.compress_sequence(sample_sequences[0], tempdir, args.dry_run, args.logging_level, 1, len(sample_sequences))
        # The returned sequence should be the same as the first sample_sequences (due to --dry-run)
        for idx, files in enumerate(seq):
            for data in ["creation_time", "duration", "file_path"]:
                self.assertEqual(files[data], sample_sequences[0][idx][data])

    def test_compress_sequence_ffmpeg_verbose(self):
        """
        Test the compress_sequence() function, running the FFmpeg merge command with --verbose
        The path to the files will be different (compressed to a temporary file)
        """
        args = target.parse_args(['--verbose'])
        tempdir = tempfile.mkdtemp()
        # Call the function with the first sequence from sample_sequences
        # Using a deep copy of the sequence, otherwise running compress_sequence()
        # without --dry-run modifies the elements, and the sample_sequences array
        # gets modified which messes up other tests later on.
        seq = target.compress_sequence(copy.deepcopy(sample_sequences[0]), tempdir, args.dry_run, args.logging_level, 1, len(sample_sequences))
        # The returned sequence should be the same as the first sample_sequences (due to --dry-run)
        for idx, files in enumerate(seq):
            for data in ["creation_time", "duration"]:
                self.assertEqual(files[data], sample_sequences[0][idx][data])
            # The file path is different, now a new temporary folder (because the file has been compressed)
            # Should start with the path to the temporary folder and end with the sequence's first file name.
            self.assertTrue(files["file_path"].startswith(tempfile.gettempdir()))
            self.assertTrue(files["file_path"].endswith(os.path.split(sample_sequences[0][idx]["file_path"])[1]))

    def test_compress_sequence_ffmpeg_debug(self):
        """
        Test the compress_sequence() function, running the FFmpeg merge command with --debug
        The path to the files will be different (compressed to a temporary file)
        This will cause the output of ffmpeg (including the following error
        message) to be displayed in the output of the test suite, this is NOT a problem:
            /tmp/vids/20190121_085007.MOV: No such file or directory
        """
        args = target.parse_args(['--debug'])
        tempdir = tempfile.mkdtemp()
        # Call the function with the first sequence from sample_sequences
        # Using a deep copy of the sequence, otherwise running compress_sequence()
        # without --dry-run modifies the elements, and the sample_sequences array
        # gets modified which messes up other tests later on.
        seq = target.compress_sequence(copy.deepcopy(sample_sequences[0]), tempdir, args.dry_run, args.logging_level, 1, len(sample_sequences))
        # The returned sequence should be the same as the first sample_sequences (due to --dry-run)
        for idx, files in enumerate(seq):
            for data in ["creation_time", "duration"]:
                self.assertEqual(files[data], sample_sequences[0][idx][data])
            # The file path is different, now a new temporary folder (because the file has been compressed)
            # Should start with the path to the temporary folder and end with the sequence's first file name.
            self.assertTrue(files["file_path"].startswith(tempfile.gettempdir()))
            self.assertTrue(files["file_path"].endswith(os.path.split(sample_sequences[0][idx]["file_path"])[1]))

class TestAnalyzeSequences(unittest.TestCase):
    def test_analyze_sequences_no_net(self):
        """
        Test the analyze_sequences() function, passing a valid sequences array and only --no-net
        This means all the sequences should be identified as new
        """
        args = target.parse_args(['--no-net'])
        youtube = None
        new_sequences = target.analyze_sequences(sample_sequences, youtube, args)
        # Confirm 3 sequences were identified as new
        self.assertEqual(len(new_sequences), 3)
        # Check the content of each sequence
        for idx, seq in enumerate(new_sequences):
            self.assertEqual(len(seq), len(sample_sequences[idx]))
            for idx2, files in enumerate(seq):
                for data in ["creation_time", "duration", "file_path"]:
                    self.assertEqual(files[data], sample_sequences[idx][idx2][data])

    def test_analyze_sequences_length_restriction(self):
        """
        Test the analyze_sequences() function, passing a valid sequences array and both --min-length and --max-length
        Only one sequence should be identified as new
        """
        args = target.parse_args(['--no-net', '--min-length', '15', '--max-length', '19'])
        youtube = None
        new_sequences = target.analyze_sequences(sample_sequences, youtube, args)
        # Confirm only one sequence were identified as new, the first of the sample sequences
        self.assertEqual(len(new_sequences), 1)
        # Check the content of each sequence
        for idx, seq in enumerate(new_sequences):
            self.assertEqual(len(seq), len(sample_sequences[0]))
            for idx2, files in enumerate(seq):
                for data in ["creation_time", "duration", "file_path"]:
                    self.assertEqual(files[data], sample_sequences[0][idx2][data])

class TestIdentifySequences(unittest.TestCase):
    def test_identify_sequences_valid(self):
        """
        Test the identify_sequences() function, passing a valid array of files
        """
        videos_by_creation_time = {
            datetime.datetime(2019, 1, 21, 8, 50, 7): {'duration': 300.0, 'file_path': '/tmp/vids/20190121_085007.MOV'},
            datetime.datetime(2019, 1, 25, 16, 22, 20): {'duration': 300.0, 'file_path': '/tmp/vids/20190125_162220.MOV'},
            datetime.datetime(2019, 1, 21, 9, 5, 8): {'duration': 216.75, 'file_path': '/tmp/vids/20190121_090508.MOV'},
            datetime.datetime(2019, 1, 29, 8, 28, 26): {'duration': 300.0, 'file_path': '/tmp/vids/20190129_082825.MOV'},
            datetime.datetime(2019, 1, 29, 8, 38, 27): {'duration': 286.0, 'file_path': '/tmp/vids/20190129_083826.MOV'},
            datetime.datetime(2019, 1, 29, 8, 33, 27): {'duration': 300.0, 'file_path': '/tmp/vids/20190129_083327.MOV'},
            datetime.datetime(2019, 1, 25, 16, 37, 21): {'duration': 300.0, 'file_path': '/tmp/vids/20190125_163721.MOV'},
            datetime.datetime(2019, 1, 25, 16, 27, 21): {'duration': 300.0, 'file_path': '/tmp/vids/20190125_162721.MOV'},
            datetime.datetime(2019, 1, 21, 8, 55, 8): {'duration': 300.0, 'file_path': '/tmp/vids/20190121_085508.MOV'},
            datetime.datetime(2019, 1, 21, 9, 0, 8): {'duration': 300.0, 'file_path': '/tmp/vids/20190121_090008.MOV'},
            datetime.datetime(2019, 1, 25, 16, 32, 21): {'duration': 300.0, 'file_path': '/tmp/vids/20190125_163221.MOV'}
        }
        creation_times = [
            datetime.datetime(2019, 1, 25, 16, 37, 21),
            datetime.datetime(2019, 1, 25, 16, 27, 21),
            datetime.datetime(2019, 1, 25, 16, 32, 21),
            datetime.datetime(2019, 1, 21, 8, 55, 8),
            datetime.datetime(2019, 1, 25, 16, 22, 20),
            datetime.datetime(2019, 1, 29, 8, 33, 27),
            datetime.datetime(2019, 1, 21, 9, 5, 8),
            datetime.datetime(2019, 1, 29, 8, 28, 26),
            datetime.datetime(2019, 1, 21, 8, 50, 7),
            datetime.datetime(2019, 1, 21, 9, 0, 8),
            datetime.datetime(2019, 1, 29, 8, 38, 27)
        ]

        sequences = target.identify_sequences(videos_by_creation_time, creation_times)

        # Confirm 3 sequences were identified
        self.assertEqual(len(sequences), 3)
        # Check the content of each sequence
        for idx, seq in enumerate(sequences):
            self.assertEqual(len(seq), len(sample_sequences[idx]))
            for idx2, files in enumerate(seq):
                for data in ["creation_time", "duration", "file_path"]:
                    self.assertEqual(files[data], sample_sequences[idx][idx2][data])

class TestAnalyzeFiles(unittest.TestCase):
    def test_analyze_files_no_files(self):
        """
        Test the analyze_files() function, passing an empty list of files
        (This scenario should not ever happen)
        """
        sequences = target.analyze_files([])
        self.assertEqual(sequences, [])

    def test_analyze_files_invalid_files(self):
        """
        Test the analyze_files() function, passing list of non-existing files
        (This scenario should not ever happen)
        """
        with self.assertRaises(Exception) as cm:
            sequences = target.analyze_files([""])
        self.assertEqual(str(cm.exception), "There is no file to analyze at ''")

class TestDetectFolder(unittest.TestCase):
    def test_detect_folder_explicit_path_valid(self):
        """
        Test the detect_folder() function, explicitly passing it a valid path
        """
        # Create a temporary folder with 5 dummy files, 3 of which with .MOV extension
        tempdir = tempfile.mkdtemp()
        (ignore, mov_file_1) = tempfile.mkstemp(suffix=".MOV", dir=tempdir)
        (ignore, mov_file_2) = tempfile.mkstemp(suffix=".MOV", dir=tempdir)
        (ignore, mov_file_3) = tempfile.mkstemp(suffix=".MOV", dir=tempdir)
        tempfile.mkstemp(dir=tempdir)
        tempfile.mkstemp(dir=tempdir)

        # Run detect_folder()
        args = target.parse_args(['--folder', tempdir])
        (folder, files) = target.detect_folder(args)

        # Validate the return of detect_folder()
        self.assertEqual(folder, tempdir)
        self.assertEqual(len(files), 3)
        self.assertTrue(mov_file_1 in files)
        self.assertTrue(mov_file_2 in files)
        self.assertTrue(mov_file_3 in files)

        # Delete the temporary folder and files
        shutil.rmtree(tempdir)

    def test_detect_folder_explicit_path_invalid(self):
        """
        Test the detect_folder() function, explicitly passing it a invalid path
        """
        # Create a temporary folder and delete it directly
        tempdir = tempfile.mkdtemp()
        shutil.rmtree(tempdir)

        # Temporarily disable the logging output (we know this is "Critical")
        logger = logging.getLogger()
        logger.disabled = True

        # Pass that now non-existing path to detect_folder()
        args = target.parse_args(['--folder', tempdir])
        with self.assertRaises(SystemExit) as cm:
            (folder, files) = target.detect_folder(args)
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 10)
        logger.disabled = False

    def test_detect_folder_explicit_path_no_video_files(self):
        """
        Test the detect_folder() function, explicitly passing it a valid path containing no video files
        """
        # Create a temporary folder with a non .MOV file
        tempdir = tempfile.mkdtemp()
        tempfile.mkstemp(dir=tempdir)

        # Temporarily disable the logging output (we know this is "Critical")
        logger = logging.getLogger()
        logger.disabled = True

        # Pass that now non-existing path to detect_folder()
        args = target.parse_args(['--folder', tempdir])
        with self.assertRaises(SystemExit) as cm:
            (folder, files) = target.detect_folder(args)
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 11)
        logger.disabled = False

        # Delete the temporary folder and file
        shutil.rmtree(tempdir)

    def test_detect_folder_automatic_detection_fail(self):
        """
        Test the detect_folder() function, failing at automatic discovery
        """
        # Temporarily disable the logging output (we know this is "Critical")
        logger = logging.getLogger()
        logger.disabled = True

        # Pass that now non-existing path to detect_folder()
        args = target.parse_args([])
        with self.assertRaises(SystemExit) as cm:
            (folder, files) = target.detect_folder(args)
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 12)
        logger.disabled = False

class TestGetSequenceTitle(unittest.TestCase):
    def test_get_sequence_title(self):
        """
        Test the get_sequence_title() function
        """
        creation_time = datetime.datetime(2019, 1, 25, 16, 42, 21)
        sequence_title = target.get_sequence_title(creation_time)
        self.assertEqual(sequence_title, "2019-01-25 16:42:21")

class TestParseArgs(unittest.TestCase):
    def test_parse_args_dry_run(self):
        """
        Test the --dry-run argument
        """
        parser = target.parse_args(['--dry-run'])
        self.assertTrue(parser.dry_run)

    def test_parse_args_dry_run_shorthand(self):
        """
        Test the -dr argument
        """
        parser = target.parse_args(['-dr'])
        self.assertTrue(parser.dry_run)

    def test_parse_args_no_net(self):
        """
        Test the --no-net argument
        """
        parser = target.parse_args(['--no-net'])
        self.assertTrue(parser.no_net)

    def test_parse_args_no_net_shorthand(self):
        """
        Test the -nn argument
        """
        parser = target.parse_args(['-nn'])
        self.assertTrue(parser.no_net)

    def test_parse_args_debug(self):
        """
        Test the --debug argument
        """
        parser = target.parse_args(['--debug'])
        self.assertEqual(parser.loglevel, logging.DEBUG)
        self.assertEqual(parser.logging_level, "DEBUG")

    def test_parse_args_debug_shorthand(self):
        """
        Test the -d argument
        """
        parser = target.parse_args(['-d'])
        self.assertEqual(parser.loglevel, logging.DEBUG)
        self.assertEqual(parser.logging_level, "DEBUG")

    def test_parse_args_verbose(self):
        """
        Test the --verbose argument
        """
        parser = target.parse_args(['--verbose'])
        self.assertEqual(parser.loglevel, logging.INFO)
        self.assertEqual(parser.logging_level, "INFO")

    def test_parse_args_verbose_shorthand(self):
        """
        Test the -v argument
        """
        parser = target.parse_args(['-v'])
        self.assertEqual(parser.loglevel, logging.INFO)
        self.assertEqual(parser.logging_level, "INFO")

    def test_parse_args_privacyStatus_valid(self):
        """
        Test the --privacyStatus argument with a valid value
        """
        parser = target.parse_args(['--privacyStatus', 'private'])
        self.assertEqual(parser.privacyStatus, 'private')

    def test_parse_args_min_length_valid(self):
        """
        Test the --min-length argument with a valid value
        """
        parser = target.parse_args(['--min-length', '6'])
        self.assertEqual(parser.min_length, 6)

    def test_parse_args_max_length_valid(self):
        """
        Test the --max-length argument with a valid value
        """
        parser = target.parse_args(['--max-length', '48'])
        self.assertEqual(parser.max_length, 48)

if __name__ == '__main__':
    unittest.main()
