import os
import shutil
import subprocess
import sys
import argparse
import ctypes
import platform


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def check_disk_space_vs_file(path, file_to_pull):

    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None, None, ctypes.pointer(free_bytes))
        st = free_bytes.value
    else:
        st = os.statvfs(path)

    remote_size = os.path.getsize(file_to_pull)
    print "Space free locally:", sizeof_fmt(st)
    print ""

    if remote_size * 2 > st:
        print " Not enough free space to process file of size", sizeof_fmt(remote_size)
        return False
    else:
        return True


def init():
    parser = argparse.ArgumentParser(description='Convert MKV files tp MP4.')
    parser.add_argument('--scan', action='store_true',
                        help='True/False: Only scan files and do not convert')
    parser.add_argument('--noscan', action='store_false',
                        help='True/False: Only scan files and do not convert')
    global args
    args = parser.parse_args()

    if not os.path.exists(local_location):
        print "Local working dir", local_location, " does not exist  - creating"
        os.makedirs(local_location)


def copy_file(from_file, to_file):
    print "Copying", from_file, "to", to_file
    shutil.copy2(from_file, to_file)
    print "Copied ", from_file, "to", to_file


def remove_file(file_to_delete):
    print "Removing ", file_to_delete
    os.remove(file_to_delete)
    print "Removed ", file_to_delete


def convert_file(local_file):
    print "Converting "+local_file

    handbrakecommand = "\"D:\\Program Files\\HandBrakeCLI.exe \" " \
                       "--preset-import-gui --preset \"Fast 1080p30\"" \
                       " -s \"1,2,3,4,5,6\" " \
                       " -i "
    output_file = local_file.__str__().replace(".mkv", ".m4v")
    full_command = handbrakecommand+"\""+local_file+"\" -o \""+output_file+"\""

    return_code = subprocess.call(full_command, shell=True, cwd=local_location)

    if return_code == 0:
        local_file_size_gb = sizeof_fmt(os.path.getsize(local_location+local_file))
        output_file_size_gb = sizeof_fmt(os.path.getsize(local_location+output_file))
        print output_file, ": Filesize reduced from ", local_file_size_gb, "to", output_file_size_gb

        if os.path.getsize(local_location+output_file) > os.path.getsize(local_location+local_file):
            print "ERROR: Converted file shouldn't be bigger than original! Lets bail " \
                  "and add this file to an exception list!"
            sys.exit(-1)
        else:
            return local_location+output_file
    else:
        sys.exit(-1)


global args
remote_location = "z:\\Media\\TV"
#remote_location = "z:\\Media\\Films"
local_location = "d:\\videos\\brake\\"
extension = '.mkv'
file_names = []
total_filesize_to_convert = 0.0
exception_files = ['District.9.2009.720p.BrRip.YIFY.mkv',
                   'Argo.mkv',
                   'The Big Lebowski.mkv']

init()


for root, dirs, files in os.walk(unicode(remote_location)):
    for name in files:
        if name not in exception_files:
            if name.endswith(extension):
                file_names.append((os.path.join(root, name)))
                total_filesize_to_convert += os.path.getsize(root+"\\"+name)


print "Found", file_names.__len__(), "mkv file(s) to convert"
print file_names
print "Total filesize is", sizeof_fmt(total_filesize_to_convert)

if args.scan:
    sys.exit(1)


for file_to_copy in file_names:
    local_file_mkv = os.path.basename(file_to_copy)
    remote_file_dir = os.path.dirname(file_to_copy)
    
    if check_disk_space_vs_file(local_location, file_to_copy):
        # Copy the file locally
        copy_file(file_to_copy, local_location)
        # Convert the file
        converted_file = convert_file(local_file_mkv)
        # remove the remote file (backup is locally anyway)
        remove_file(file_to_copy)
        # copy up new file from whence it came
        copy_file(converted_file, remote_file_dir)
        # now remove the new file locally to save space
        remove_file(converted_file)
    else:
        sys.exit(-1)
