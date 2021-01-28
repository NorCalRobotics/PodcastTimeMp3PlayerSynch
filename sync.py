# Synchronizer for PodcastTime app to MP3 Players
# Script to synchronize downloaded MP3 files from the Podcast Time app
# from the Windows 10 Store with a destination directory (an MP3 player [USB Mass Storage Controller])
# Podcast Time is:
#     Published by Marek Chlebik
#     Developed by Marek Chlebik
#     Release date: 4/21/2017
#     https://www.microsoft.com/en-us/p/podcast-time/9nblggh4t1wz

# import required python modules:
import os
import sys
import json
import argparse
import id3reader
# C:\Python27\Scripts\pip.exe install hashlib
import hashlib
import shutil


# creates a CLI argument parser
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", action="store", required=True)
    parser.add_argument("--src", action="store", default=None)
    return parser


# creates a list of all MP3 filenames within a given dir
def walk_mp3_dir(dir_name):
    filename_list = list()

    def visit(fn_list, root, filenames):
        for filename in filenames:
            subname = os.path.join(root, filename)

            if os.path.isdir(subname):
                continue

            _, ext = os.path.splitext(filename)
            if ext.lower() != ".mp3":
                continue

            fn_list.append(subname)

    os.path.walk(dir_name, visit, filename_list)

    return filename_list


# Automatically finds the dir where the app stores MP3 files
def find_podcast_time_app_dir():
    found_dirs_list = list()

    app_data = os.environ.get("APPDATA")
    # assert os.name == 'nt'
    # assert sys.platform == 'win32'
    assert app_data is not None

    possible_app_data, data_type = os.path.split(app_data)
    if data_type.lower() in ["roaming", "local", "locallow"]:
        app_data = possible_app_data

        # Speed up the search for the directory
        possible_app_data = os.path.join(app_data, "Local")
        if os.path.isdir(possible_app_data):
            app_data = possible_app_data
            possible_app_data = os.path.join(app_data, "Packages")
            if os.path.isdir(possible_app_data):
                app_data = possible_app_data

    def visit(fd_list, root, dirnames):
        for dirname in dirnames:
            subname = os.path.join(root, dirname)

            if not os.path.isdir(subname):
                continue

            # AppData\Local\Packages\4924MarekChlebik.PodcastTime_hy1rn8tk6kd4y
            if "marekchlebik.podcasttime" not in dirname.lower():
                continue

            fd_list.append(subname)
            break

    os.path.walk(app_data, visit, found_dirs_list)

    return found_dirs_list


# Prints details about a given MP3 file to stdout
def print_mp3_file_details(mp3_filename):
    id3r = id3reader.Reader(mp3_filename)
    print mp3_filename
    print "album:     " + str(id3r.getValue('album'))
    print "performer: " + str(id3r.getValue('performer'))
    print "title:     " + str(id3r.getValue('title'))
    print "year:      " + str(id3r.getValue('year'))
    print hashlib.sha256(open(mp3_filename, "r").read()).hexdigest()[0:16]


# main function:
def main():
    # handle CLI arguments:
    parser = create_arg_parser()
    argv = parser.parse_args()

    # Determine the source dir for MP3 files:
    if argv.src is None:
        print "Searching for Podcast Time App's directory...",
        app_dir_list = find_podcast_time_app_dir()
        print "DONE"
    else:
        app_dir_list = [argv.src]
    # print app_dir_list

    # Collect a list of all MP3 files from the App:
    app_files = list()
    for app_dir in app_dir_list:
        app_files += walk_mp3_dir(app_dir)
    # print app_files

    # Collect a list of all MP3 files from the MP3 Player:
    mp3_player_files = walk_mp3_dir(argv.dest)
    # print mp3_player_files

    # Simplify the lists down to just filename, for list checking:
    app_mp3_list = [os.path.basename(mp3_filename) for mp3_filename in app_files]
    mp3_player_mp3_list = [os.path.basename(mp3_filename) for mp3_filename in mp3_player_files]

    # Set JSON filenames for records of the previous run:
    json_filename = os.path.join(sys.path[0], "previous_run.json")

    # Load the record of the previous run:
    try:
        previous_run = json.load(open(json_filename, "r"))
        previous_run_app_mp3_list = previous_run["app_mp3_list"]
        previous_run_mp3_player_mp3_list = previous_run["mp3_player_mp3_list"]
    except IOError:
        previous_run_app_mp3_list = list()
        previous_run_mp3_player_mp3_list = list()
    except KeyError:
        previous_run_app_mp3_list = list()
        previous_run_mp3_player_mp3_list = list()

    # Create list of all files deleted by user from App since previous run:
    app_deletions = list()
    for basename in previous_run_app_mp3_list:
        if basename not in app_mp3_list:
            app_deletions.append(basename)

    # Create list of all files deleted by user from MP3 Player since previous run:
    mp3_player_deletions = list()
    for basename in previous_run_mp3_player_mp3_list:
        if basename not in mp3_player_mp3_list:
            mp3_player_deletions.append(basename)

    # Check all of the App's MP3 files to see if any actions are required:
    for mp3_filename in app_files:
        print_mp3_file_details(mp3_filename)
        basename = os.path.basename(mp3_filename)
        if basename in mp3_player_deletions:
            print "Deleting MP3 file %s from App" % basename
            os.remove(mp3_filename)
            app_mp3_list.remove(basename)
        elif basename not in mp3_player_mp3_list:
            print "Copying MP3 file %s from App to MP3 Player" % basename
            shutil.copyfile(mp3_filename, os.path.join(argv.dest, basename))
            mp3_player_mp3_list.append(basename)
        print ""

    # Check all of the MP3 Player's MP3 files to see if any actions are required:
    for mp3_filename in mp3_player_files:
        # print_mp3_file_details(mp3_filename)
        basename = os.path.basename(mp3_filename)
        if basename in app_deletions:
            print "Deleting MP3 file %s from MP3 Player" % basename
            os.remove(mp3_filename)
            mp3_player_mp3_list.remove(basename)
        elif basename not in app_mp3_list:
            print "Note: found an MP3 file %s on MP3 Player, not in the App. Skipping..." % basename

    # Save the record of this run:
    run_record = dict()
    run_record["app_mp3_list"] = app_mp3_list
    run_record["mp3_player_mp3_list"] = mp3_player_mp3_list
    json.dump(run_record, open(json_filename, "w"))


if __name__ == "__main__":
    main()
