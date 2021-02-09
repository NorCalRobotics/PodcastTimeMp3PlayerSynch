# Unique MP3 Copier; Script to copy only MP3 files from a source to a destination that have a different SHA

# import required python modules:
import os
from sync import walk_mp3_dir
# C:\Python27\Scripts\pip.exe install hashlib
import hashlib
import shutil
import argparse


# creates a CLI argument parser
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", action="store", required=True)
    parser.add_argument("--src", action="store", required=True)
    parser.add_argument("--print_dest_files", action="store_true", default=False)
    parser.add_argument("--print_dupe_notifications", action="store_true", default=False)
    parser.add_argument("--do_not_print_new_files_in_src_dir", action="store_true", default=False)
    return parser


# main function:
def main():
    # handle CLI arguments:
    parser = create_arg_parser()
    argv = parser.parse_args()

    src_dir = argv.src  # 'F:\\'  # 'D:\\Backups\\mp3s'
    dest_dir = argv.dest  # 'E:\\'

    print_dest_files = argv.print_dest_files
    print_dupe_notifications = argv.print_dupe_notifications
    print_new_files_in_src_dir = not argv.do_not_print_new_files_in_src_dir

    already_known = dict()

    print "Scanning destination dir for MP3 files..."
    filename_list = walk_mp3_dir(dest_dir)
    print "Inspecting MP3 files in destination dir..."
    for mp3_filename in filename_list:
        sha = hashlib.sha256(open(mp3_filename, "r").read()).hexdigest()
        sha_16d = sha[0:16]
        already_known[sha] = mp3_filename
        if print_dest_files:
            print "%s:\t%s" % (sha_16d, mp3_filename)

    print "Scanning source dir for MP3 files..."
    filename_list = walk_mp3_dir(src_dir)
    print "Inspecting MP3 files in source dir..."
    for mp3_filename in filename_list:
        sha = hashlib.sha256(open(mp3_filename, "r").read()).hexdigest()
        sha_16d = sha[0:16]
        if sha in already_known:
            if print_dupe_notifications:
                dupe_filename = already_known[sha]
                print "Skipping duplicate: %s:\t%s\t(dupe of %s)" % (sha_16d, mp3_filename, dupe_filename)
        else:
            dest_filename = os.path.join(dest_dir, os.path.basename(mp3_filename))
            if print_new_files_in_src_dir:
                print "%s:\t%s --> %s" % (sha_16d, mp3_filename, dest_filename)
            shutil.copyfile(mp3_filename, dest_filename)
            already_known[sha] = mp3_filename


if __name__ == "__main__":
    main()
