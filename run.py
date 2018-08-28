from logging.config import fileConfig
import getopt
import sys
import logging
import os

# Initialize logger
fileConfig('logging_config.ini')
log = logging.getLogger()


def dupx(the_directory):
    for r, d, f in os.walk(the_directory):
        for directory in d:
            dupx(directory)
        list_files = []
        for file in f:
            if ".jar" in file and "9.0.0" in file:
                # log.debug("XXX: " + os.path.join(r, file))
                list_files.append(file)
        if len(list_files) > 1:
            new_list_files_clean = []
            for file in list_files:
                new_list_files_clean.append(file[0:(file.index('9.0.0')-1)])
            pos = 0
            print_once = True
            for file in new_list_files_clean:
                if new_list_files_clean.count(file) > 1:
                    if print_once:
                        log.debug('Found duplicate Jars with different version on directory: ' + os.path.abspath(r))
                        print_once = False
                    log.debug("Jar: " + list_files[pos])
                pos += 1


def duplicate(installation_dir):
    log.debug('Going to check duplicate jars in Pentaho installation [' + installation_dir + ']')

    dupx(installation_dir)

    #    for file in f:
    #        if ".docx" in file:
    #            print(os.path.join(r, file))


def main():
    count = len(sys.argv)
    if count == 1:
        log.debug('No parameters specified!')
        sys.exit(2)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "i:d", ["installation=", "duplicate="])
    except getopt.GetoptError as err:
        log.debug(err)
        sys.exit(2)

    count = len(opts)
    if count == 0:
        log.debug('No parameters specified!')

    installation_dir = ''
    is_duplicate = False
    for opt, arg in opts:
        if opt in ('-i', '--installation'):
            installation_dir = arg
        elif opt in ('-d', '--duplicate'):
            is_duplicate = True
            log.debug('Let\'s check duplicate jars')

    if installation_dir == '':
        log.error('Specified the installation path for Pentaho')
        sys.exit(2)

    if is_duplicate:
        duplicate(installation_dir)
    else:
        log.error('Incomplete arguments!')
        log.error('-i --installation : path for the directory. e.g. C:\Release\9.0\pdi-ee-client-9.0.0.0-142\data-integration')
        log.error('-d --duplicate : to check on the directory specified for duplicate files but with different versions')
        log.error('Support -i and -d in combination.')


# -------------------------------------------------------
#
#                     BEGIN
#
# -------------------------------------------------------
if __name__ == "__main__":
    main()
