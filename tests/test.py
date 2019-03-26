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

# Used to test manual entry when using the --interactive flag
mock_raw_input_counter = 0
mock_raw_input_values = []
def mock_raw_input(s):
    global mock_raw_input_counter
    global mock_raw_input_values
    mock_raw_input_counter += 1
    return mock_raw_input_values[mock_raw_input_counter - 1]
target.input = mock_raw_input

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

def createTempFolderWithDummyMOVFiles():
    """
    Create a temporary folder with 5 dummy files, 3 of which with .MOV extension
    """
    tempdir = tempfile.mkdtemp()
    (ignore, mov_file_1) = tempfile.mkstemp(suffix=".MOV", dir=tempdir)
    (ignore, mov_file_2) = tempfile.mkstemp(suffix=".MOV", dir=tempdir)
    (ignore, mov_file_3) = tempfile.mkstemp(suffix=".MOV", dir=tempdir)
    tempfile.mkstemp(dir=tempdir)
    tempfile.mkstemp(dir=tempdir)
    return (tempdir, mov_file_1, mov_file_2, mov_file_3)

# class TestCompressMergeAndUploadSequences(unittest.TestCase):
    # def test_compress_merge_and_upload_sequences_no_net(self):
    #     """
    #     Test the compress_merge_and_upload_sequences() function with --no-net
    #     """
    #     args = target.parse_args(['--no-net', '--verbose'])
    #     youtube = None
    #     # Using a deep copy of the sequence, otherwise running compress_sequence()
    #     # without --dry-run modifies the elements, and the sample_sequences array
    #     # gets modified which messes up other tests later on.
    #     target.compress_merge_and_upload_sequences(copy.deepcopy(sample_sequences), [], youtube, args)
    #     # Nothing to assert (the individual functions are tested separately for
    #     # their returns), just confirming no Exception is thrown.
    #
    # def test_compress_merge_and_upload_sequences_dry_run(self):
    #     """
    #     Test the compress_merge_and_upload_sequences() function with --dry-run
    #     """
    #     args = target.parse_args(['--dry-run', '--verbose'])
    #     youtube = None
    #     # Using a deep copy of the sequence, otherwise running compress_sequence()
    #     # without --dry-run modifies the elements, and the sample_sequences array
    #     # gets modified which messes up other tests later on.
    #     target.compress_merge_and_upload_sequences(copy.deepcopy(sample_sequences), [], youtube, args)
    #     # Nothing to assert (the individual functions are tested separately for
    #     # their returns), just confirming no Exception is thrown.
    #
    # def test_compress_merge_and_upload_sequences_no_net_no_compression(self):
    #     """
    #     Test the compress_merge_and_upload_sequences() function
    #     """
    #     args = target.parse_args(['--no-net', '--verbose', '--no-compression'])
    #     youtube = None
    #     target.compress_merge_and_upload_sequences(sample_sequences, [], youtube, args)
    #     # Nothing to assert (the individual functions are tested separately for
    #     # their returns), just confirming no Exception is thrown.

    # def test_compress_merge_and_upload_sequences_no_arguments(self):
    #     """
    #     Test the compress_merge_and_upload_sequences() function with our sample video, without arguments
    #     """
    #     args = target.parse_args(['--verbose'])
    #     youtube = None
    #     # Using a deep copy of the sequence, otherwise running compress_sequence()
    #     # without --dry-run modifies the elements, and the sample_sequences array
    #     # gets modified which messes up other tests later on.
    #     # Since we're not passing a real "youtube" argument, this call will raise an Exception
    #     with self.assertRaises(AttributeError) as cm:
    #         target.compress_merge_and_upload_sequences(copy.deepcopy(sample_sequences), [], youtube, args)
    #     self.assertEqual(str(cm.exception), "'NoneType' object has no attribute 'videos'")

class TestMergeSequence(unittest.TestCase):
    def test_merge_sequence_dry_run(self):
        """
        Test the merge_sequence() function with --dry-run (doesn't run the ffmpeg command)
        """
        args = target.parse_args(['--dry-run', '--verbose'])
        file_to_upload = target.merge_sequence(sample_sequences[0], args.dry_run, args.logging_level)
        self.assertEqual(file_to_upload, "/tmp/%s" % os.path.split(sample_sequences[0][0]["file_path"])[1])

    # def test_merge_sequence_ffmpeg_verbose(self):
    #     """
    #     Test the merge_sequence() function, running the FFmpeg merge command with --verbose
    #     """
    #     args = target.parse_args(['--verbose'])
    #     file_to_upload = target.merge_sequence(sample_sequences[0], args.dry_run, args.logging_level)
    #     self.assertEqual(file_to_upload, "/tmp/%s" % os.path.split(sample_sequences[0][0]["file_path"])[1])

    # def test_merge_sequence_ffmpeg_debug(self):
    #     """
    #     Test the merge_sequence() function, running the FFmpeg merge command with --debug
    #     This will cause the output of ffmpeg (including the following error
    #     message) to be displayed in the output of the test suite, this is NOT a problem:
    #         Impossible to open '/tmp/vids/20190121_085007.MOV'
    #         /tmp/actioncam-upload-files.txt: No such file or directory
    #     """
    #     args = target.parse_args(['--debug'])
    #     file_to_upload = target.merge_sequence(sample_sequences[0], args.dry_run, args.logging_level)
    #     self.assertEqual(file_to_upload, "/tmp/%s" % os.path.split(sample_sequences[0][0]["file_path"])[1])

class TestCompressSequence(unittest.TestCase):
    def test_compress_sequence_invalid_file(self):
        """
        Test the compress_sequence() function with --dry-run
        Nothing should change to the sequence
        """
        args = target.parse_args(['--dry-run', '--verbose'])
        tempdir = tempfile.mkdtemp()
        with self.assertRaises(SystemExit) as cm:
            # Call the function with the first sequence from sample_sequences
            # Since it's a non-existing file, process will close with code 15
            seq = target.compress_sequence(sample_sequences[0], tempdir, args.dry_run, args.logging_level, 1, len(sample_sequences))
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 15)
        # Delete the temporary folder
        shutil.rmtree(tempdir)




#     def test_compress_sequence_dry_run(self):
#         """
#         Test the compress_sequence() function with --dry-run
#         Nothing should change to the sequence
#         """
#         args = target.parse_args(['--dry-run', '--verbose'])
#         tempdir = tempfile.mkdtemp()
#         # Call the function with the first sequence from sample_sequences
#         seq = target.compress_sequence(sample_sequences[0], tempdir, args.dry_run, args.logging_level, 1, len(sample_sequences))
#         # The returned sequence should be the same as the first sample_sequences (due to --dry-run)
#         for idx, files in enumerate(seq):
#             for data in ["creation_time", "duration", "file_path"]:
#                 self.assertEqual(files[data], sample_sequences[0][idx][data])
#         # Delete the temporary folder
#         shutil.rmtree(tempdir)
#
#     def test_compress_sequence_ffmpeg_verbose(self):
#         """
#         Test the compress_sequence() function, running the FFmpeg merge command with --verbose
#         The path to the files will be different (compressed to a temporary file)
#         """
#         args = target.parse_args(['--verbose'])
#         tempdir = tempfile.mkdtemp()
#         # Call the function with the first sequence from sample_sequences
#         # Using a deep copy of the sequence, otherwise running compress_sequence()
#         # without --dry-run modifies the elements, and the sample_sequences array
#         # gets modified which messes up other tests later on.
#         seq = target.compress_sequence(copy.deepcopy(sample_sequences[0]), tempdir, args.dry_run, args.logging_level, 1, len(sample_sequences))
#         # The returned sequence should be the same as the first sample_sequences (due to --dry-run)
#         for idx, files in enumerate(seq):
#             for data in ["creation_time", "duration"]:
#                 self.assertEqual(files[data], sample_sequences[0][idx][data])
#             # The file path is different, now a new temporary folder (because the file has been compressed)
#             # Should start with the path to the temporary folder and end with the sequence's first file name.
#             self.assertTrue(files["file_path"].startswith(tempfile.gettempdir()))
#             self.assertTrue(files["file_path"].endswith(os.path.split(sample_sequences[0][idx]["file_path"])[1]))
#         # Delete the temporary folder
#         shutil.rmtree(tempdir)
#
#     def test_compress_sequence_ffmpeg_debug(self):
#         """
#         Test the compress_sequence() function, running the FFmpeg merge command with --debug
#         The path to the files will be different (compressed to a temporary file)
#         This will cause the output of ffmpeg (including the following error
#         message) to be displayed in the output of the test suite, this is NOT a problem:
#             /tmp/vids/20190121_085007.MOV: No such file or directory
#         """
#         args = target.parse_args(['--debug'])
#         tempdir = tempfile.mkdtemp()
#         # Call the function with the first sequence from sample_sequences
#         # Using a deep copy of the sequence, otherwise running compress_sequence()
#         # without --dry-run modifies the elements, and the sample_sequences array
#         # gets modified which messes up other tests later on.
#         seq = target.compress_sequence(copy.deepcopy(sample_sequences[0]), tempdir, args.dry_run, args.logging_level, 1, len(sample_sequences))
#         # The returned sequence should be the same as the first sample_sequences (due to --dry-run)
#         for idx, files in enumerate(seq):
#             for data in ["creation_time", "duration"]:
#                 self.assertEqual(files[data], sample_sequences[0][idx][data])
#             # The file path is different, now a new temporary folder (because the file has been compressed)
#             # Should start with the path to the temporary folder and end with the sequence's first file name.
#             self.assertTrue(files["file_path"].startswith(tempfile.gettempdir()))
#             self.assertTrue(files["file_path"].endswith(os.path.split(sample_sequences[0][idx]["file_path"])[1]))
#         # Delete the temporary folder
#         shutil.rmtree(tempdir)

class TestPreCopy(unittest.TestCase):
    def test_pre_copy(self):
        """
        Test the pre_copy() function
        """
        # Simulate files on the actioncam
        temp_actioncam_dir = tempfile.mkdtemp()

        new_sequences = copy.deepcopy(sample_sequences)

        # Create temporary files and use these in the sample_sequences
        mov_files = {}
        for idx, seq in enumerate(new_sequences):
            mov_files[idx] = {}
            for idx2, files in enumerate(seq):
                (ignore, mov_files[idx][idx2]) = tempfile.mkstemp(suffix=".MOV", dir=temp_actioncam_dir)
                files["file_path"] = mov_files[idx][idx2]

        # Confirm that there are 11 dummy files in the temporary actioncam folder
        self.assertEqual(len([name for name in os.listdir(temp_actioncam_dir) if os.path.isfile(os.path.join(temp_actioncam_dir, name))]), 11)

        # Copy the files from the "actioncam" folder to new temporary folders
        (new_sequences, pre_copy_folders) = target.pre_copy(new_sequences)

        for idx, seq in enumerate(new_sequences):
            # Confirm the number of files in that sequence's temporary folder is correct
            self.assertEqual(len([name for name in os.listdir(pre_copy_folders[idx]) if os.path.isfile(os.path.join(pre_copy_folders[idx], name))]), len(seq))
            for idx2, files in enumerate(seq):
                # concatenate that sequence's temp folder with that file's filename
                fname = os.path.join(pre_copy_folders[idx], os.path.split(mov_files[idx][idx2])[1])
                self.assertEqual(files["file_path"], fname)
            # Delete the new temporary folders (and files)
            shutil.rmtree(pre_copy_folders[idx])

        # Confirm the original files are still left in the temporary actioncam folder (it's a copy, not a move)
        self.assertEqual(len([name for name in os.listdir(temp_actioncam_dir) if os.path.isfile(os.path.join(temp_actioncam_dir, name))]), 11)
        # Delete the temporary actioncam folder
        shutil.rmtree(temp_actioncam_dir)

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

    def test_analyze_sequences_interactive_no_net(self):
        """
        Test the analyze_sequences() function, passing a valid sequences array, --interactive (just Enter) and --no-net
        This means all the sequences should be identified as new
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = [""]
        args = target.parse_args(['--interactive', '--no-net'])
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

    def test_analyze_sequences_interactive_length_restriction(self):
        """
        Test the analyze_sequences() function, passing a valid sequences array, --interactive (just Enter) and both --min-length and --max-length
        Only one sequence should be identified as new
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = [""]
        args = target.parse_args(['--interactive', '--no-net', '--min-length', '15', '--max-length', '19'])
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

class TestInteractiveSequenceSelection(unittest.TestCase):
    def test_interactive_sequence_selection_empty_sequences(self):
        """
        Test the interactive_sequence_selection() function, passing an empty list of sequences
        (This scenario should not ever happen)
        """
        with self.assertRaises(Exception) as cm:
            new_sequences = target.interactive_sequence_selection([], [])
        self.assertEqual(str(cm.exception), "No sequences were passed (should never happen, something has gone wrong...)")

    def test_interactive_sequence_selection_quit(self):
        """
        Test the interactive_sequence_selection() function, mock quitting (enter "q")
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = ["q"]
        with self.assertRaises(SystemExit) as cm:
            new_sequences = target.interactive_sequence_selection([None, None], [None])
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 18)

    def test_interactive_sequence_selection_quit_no_new_sequences(self):
        """
        Same as previous test, but passing no suggested new_sequences
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = ["q"]
        with self.assertRaises(SystemExit) as cm:
            new_sequences = target.interactive_sequence_selection([None, None], [])
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 18)

    def test_interactive_sequence_selection_dummy_enter(self):
        """
        Test the interactive_sequence_selection() function, using dummy sequences and just pressing "Enter" (validating the automatic new_sequences)
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = [""]
        new_sequences = target.interactive_sequence_selection(["A", "B", "C"], ["C", "A"])
        self.assertEqual(new_sequences, ["C", "A"])

    def test_interactive_sequence_selection_dummy_2_0_1(self):
        """
        Test the interactive_sequence_selection() function, using dummy sequences and passing "2", "0" and "1"
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = ["2", "0", "1", ""]
        new_sequences = target.interactive_sequence_selection(["A", "B", "C"], [None])
        self.assertEqual(new_sequences, ["C", "A", "B"])

    def test_interactive_sequence_selection_dummy_2_0_2_1(self):
        """
        Test the interactive_sequence_selection() function, using dummy sequences and repeating one of the inputs
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = ["2", "0", "2", "1", ""]
        new_sequences = target.interactive_sequence_selection(["A", "B", "C"], [None])
        self.assertEqual(new_sequences, ["C", "A", "B"])

    def test_interactive_sequence_selection_dummy_2_0_A_1(self):
        """
        Test the interactive_sequence_selection() function, using dummy sequences and entering a non-digit
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = ["2", "0", "A", "1", ""]
        new_sequences = target.interactive_sequence_selection(["A", "B", "C"], [None])
        self.assertEqual(new_sequences, ["C", "A", "B"])

    def test_interactive_sequence_selection_dummy_2_0_99_1(self):
        """
        Test the interactive_sequence_selection() function, using dummy sequences and entering a positve out of range number
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = ["2", "0", "99", "1", ""]
        new_sequences = target.interactive_sequence_selection(["A", "B", "C"], [None])
        self.assertEqual(new_sequences, ["C", "A", "B"])

    def test_interactive_sequence_selection_dummy_2_0_min4_1(self):
        """
        Test the interactive_sequence_selection() function, using dummy sequences and entering a negative out of range number
        """
        global mock_raw_input_counter
        global mock_raw_input_values
        mock_raw_input_counter = 0
        mock_raw_input_values = ["2", "0", "-4", "1", ""]
        new_sequences = target.interactive_sequence_selection(["A", "B", "C"], [None])
        self.assertEqual(new_sequences, ["C", "A", "B"])

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
        (tempdir, mov_file_1, mov_file_2, mov_file_3) = createTempFolderWithDummyMOVFiles()

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

class TestInitMain(unittest.TestCase):
    def test_init_main_no_arguments(self):
        """
        Test the initialization code without any parameter
        """
        # Make the script believe we ran it directly
        target.__name__ = "__main__"
        # Pass it no arguments
        target.sys.argv = ["scriptname.py"]
        # Temporarily disable the logging output (we know this is "Critical")
        logger = logging.getLogger()
        logger.disabled = True
        # Expect the script to return with code 12 (automatic folder detection failed)
        with self.assertRaises(SystemExit) as cm:
            target.init()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 12)
        logger.disabled = False

    def test_init_main_help(self):
        """
        Test the initialization code like we had passed --help
        """
        # Make the script believe we ran it directly
        target.__name__ = "__main__"
        # Pass it the --test argument
        target.sys.argv = ["scriptname.py", "--help"]
        # Expect the script to return with code 0
        with self.assertRaises(SystemExit) as cm:
            target.init()
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 0)

    def test_init_main_folder_no_net_no_compression(self):
        """
        Test the initialization code like we had passed --folder, --no-net and --no-compression
        This simulates a full run of the program with a single file, without uploading or compressing
        """
        # Make the script believe we ran it directly
        target.__name__ = "__main__"
        target.sys.argv = ["scriptname.py", "--no-net", "--no-compression", "--folder", "sample_videos"]
        target.init()
        # Nothing to assert (the individual functions are tested separately for
        # their returns), just confirming no Exception is thrown.

    def test_init_main_folder_with_net(self):
        """
        Test the initialization code like we had passed --folder and network
        """
        # Make the script believe we ran it directly
        target.__name__ = "__main__"
        # Create a temporary folder with 5 dummy files, 3 of which with .MOV extension
        (tempdir, mov_file_1, mov_file_2, mov_file_3) = createTempFolderWithDummyMOVFiles()
        # Pass it the --folder argument pointing to our dummy folder and files
        target.sys.argv = ["scriptname.py", "--folder", tempdir]

        # Temporarily disable the logging output (we know this is "Critical")
        logger = logging.getLogger()
        logger.disabled = True

        # Test differently if we have the files for YouTube authentication (local) or not (Travis)
        if os.path.isfile("client_secret.json"):
            # Expect the script to throw an Exception since these are not real MOV files
            with self.assertRaises(Exception) as cm:
                target.init()
            self.assertEqual(str(cm.exception), "I found no duration")
        else:
            # Expect the script to throw an Exception since these are not real MOV files
            with self.assertRaises(SystemExit) as cm:
                target.init()
            self.assertTrue(str(cm.exception).startswith("The client secrets were invalid:"))
        logger.disabled = False

        # Delete the temporary folder and files
        shutil.rmtree(tempdir)

if __name__ == '__main__':
    unittest.main()
