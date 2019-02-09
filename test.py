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

sys.path.append('.')
target = __import__("actioncam-upload")

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

class TestArgparse(unittest.TestCase):
    def test_arg_dry_run(self):
        """
        Test the --dry-run argument
        """
        parser = target.parse_args(['--dry-run'])
        self.assertTrue(parser.dry_run)

    def test_arg_dry_run_shorthand(self):
        """
        Test the -dr argument
        """
        parser = target.parse_args(['-dr'])
        self.assertTrue(parser.dry_run)

    def test_arg_no_net(self):
        """
        Test the --no-net argument
        """
        parser = target.parse_args(['--no-net'])
        self.assertTrue(parser.no_net)

    def test_arg_no_net_shorthand(self):
        """
        Test the -nn argument
        """
        parser = target.parse_args(['-nn'])
        self.assertTrue(parser.no_net)

    def test_arg_debug(self):
        """
        Test the --debug argument
        """
        parser = target.parse_args(['--debug'])
        self.assertEqual(parser.loglevel, logging.DEBUG)

    def test_arg_debug_shorthand(self):
        """
        Test the -d argument
        """
        parser = target.parse_args(['-d'])
        self.assertEqual(parser.loglevel, logging.DEBUG)

    def test_arg_verbose(self):
        """
        Test the --verbose argument
        """
        parser = target.parse_args(['--verbose'])
        self.assertEqual(parser.loglevel, logging.INFO)

    def test_arg_verbose_shorthand(self):
        """
        Test the -v argument
        """
        parser = target.parse_args(['-v'])
        self.assertEqual(parser.loglevel, logging.INFO)

    def test_arg_privacyStatus_valid(self):
        """
        Test the --privacyStatus argument with a valid value
        """
        parser = target.parse_args(['--privacyStatus', 'private'])
        self.assertEqual(parser.privacyStatus, 'private')

    def test_arg_min_length_valid(self):
        """
        Test the --min-length argument with a valid value
        """
        parser = target.parse_args(['--min-length', '6'])
        self.assertEqual(parser.min_length, 6)

    def test_arg_max_length_valid(self):
        """
        Test the --max-length argument with a valid value
        """
        parser = target.parse_args(['--max-length', '48'])
        self.assertEqual(parser.max_length, 48)

if __name__ == '__main__':
    unittest.main()
