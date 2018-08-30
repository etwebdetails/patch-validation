from logging.config import fileConfig
import getopt
import sys
import logging
import os

# Initialize logger
fileConfig('logging_config.ini')
log = logging.getLogger()

list_me_bundles_to_ignore = ['netty', 'pentaho-streaming', 'rxjava', 'javax.jms-api','guava', 'jboss', 'jgroups', 'javax.json', 'johnzon-core', 'jms', 'mqtt', 'pentaho-connections', 'pentaho-analyzer-xsd', 'paz-plugin-ce', 'icu4j', 'pentaho-camel', 'pentaho-monitoring', 'pentaho-requirejs-osgi-manager', 'pentaho-kettle-repository','pentaho-pdi-platform','tinkerpop','metaverse', 'java-semver', 'servicemix', 'spring-security']
list_di_bundles_to_ignore = ['servicemix', 'spring-security', 'geronimo']
list_rd_bundles_to_ignore = ['netty', 'pentaho-streaming', 'rxjava', 'javax.jms-api','guava', 'jboss', 'jgroups', 'javax.json', 'johnzon-core', 'jms', 'mqtt', 'pentaho-connections', 'pentaho-analyzer-xsd', 'paz-plugin-ce', 'icu4j', 'pentaho-camel', 'pentaho-monitoring', 'pentaho-requirejs-osgi-manager', 'pentaho-kettle-repository','pentaho-pdi-platform','tinkerpop','metaverse', 'java-semver', 'servicemix', 'spring-security']
list_ps_bundles_to_ignore = ['pdi-engine-configuration-ui', 'pentaho-connections', 'pentaho-analyzer-xsd', 'paz-plugin-ce', 'icu4j', 'geronimo', 'spring-aspects', 'spring-instrument', 'spring-jdbc', 'spring-jms', 'spring-test', 'spring-orm', 'spring-oxm', 'spring-tx', 'spring-web', 'portlet-api', 'pentaho-kettle-repository-locator-impl-spoon', 'activation-api', 'asm-all', 'jetty-all-server', 'pentaho-pdi-platform']


#################################################
#
#   The method works recursive to identify duplicate jars with different versions.
#
#################################################
def validate_duplicate_jars(the_directory, branch):
    for r, d, f in os.walk(the_directory):
        for directory in d:
            validate_duplicate_jars(directory, branch)
        list_files = []
        for file in f:
            if ".jar" in file and branch in file:
                # log.debug("XXX: " + os.path.join(r, file))
                list_files.append(file)
        if len(list_files) > 1:
            new_list_files_clean = []
            for file in list_files:
                new_list_files_clean.append(file[0:(file.index(branch) - 1)])
            pos = 0
            print_once = True
            for file in new_list_files_clean:
                if new_list_files_clean.count(file) > 1:
                    if print_once:
                        log.debug('Found duplicate Jars with different version on directory: ' + os.path.abspath(r))
                        print_once = False
                    log.debug("Jar: " + list_files[pos])
                pos += 1


#################################################
#
#   Method to validate duplicate jars
#
#################################################
def duplicate(installation_dir, branch):
    log.debug(
        'Going to check duplicate jars in Pentaho installation [' + installation_dir + '] for the branch [' + branch + ']')
    validate_duplicate_jars(installation_dir, branch)


def check_bundle_exist(feature_file, karaf_dir):
    # Read the file
    # Extract the bundle info
    # for each bundle info, check if exist in karaf directory
    # > if exist GOOD
    # > doesn't print the bundle missing
    print_feature_file_info = True
    with open(feature_file, "r") as fh:
        line = fh.readline()
        while line:
            if line.find('<bundle') > 0 and line.find('<!--') == -1 :
                # process line that contain bundle info
                theline = line.strip()
                process_line = True
                # metadata-editor
                if 'metadata-editor' in feature_file:
                    process_line = not [s for s in list_me_bundles_to_ignore if s in theline]
                elif 'data-integration' in feature_file:
                    process_line = not [s for s in list_di_bundles_to_ignore if s in theline]
                elif 'report-designer' in feature_file:
                    process_line = not [s for s in list_rd_bundles_to_ignore if s in theline]
                elif 'pentaho-server' in feature_file:
                    process_line = not [s for s in list_ps_bundles_to_ignore if s in theline]

                if process_line:
                    # build the jar path
                    first_slash = theline.find('/')
                    second_slash = theline.find('/', first_slash+1)
                    group_id = theline[theline.find('mvn')+4:first_slash]
                    bundle_name = theline[first_slash+1:second_slash]
                    version = theline[second_slash+1:len(theline)-9]
                    file_to_check = ''
                    if 'zip' in version:
                        version = version[0:len(version)-4]
                        file_to_check = os.path.normpath(os.path.join(karaf_dir, group_id.replace('.', os.path.sep), bundle_name, version, bundle_name + '-' + version + '.zip'))
                    elif 'xml' in version:
                        # ignore bundle lines that after version contains xml - this occurs on pentaho-karaf-features
                        file_to_check = ''
                    else:
                        file_to_check = os.path.normpath(os.path.join(karaf_dir, group_id.replace('.', os.path.sep), bundle_name, version, bundle_name + '-' + version + '.jar'))

                    # check if the file exist
                    if file_to_check is not '':
                        if not os.path.isfile(file_to_check):
                            if print_feature_file_info:
                                log.debug('-------------------------')
                                log.debug('ISSUES ON FEATURE')
                                log.debug(feature_file)
                                print_feature_file_info = False
                            log.debug('Bundle jar doesnt exist [' + file_to_check + ']')
            line = fh.readline()


def invalid_bundle_jars(the_directory):
    data_integration_dir_print_once = False
    metadata_editor_dir_print_once = False
    report_designer_dir_print_once = False
    pentaho_server_dir_print_once = False
    for r, d, f in os.walk(the_directory):
        for file in f:
            if "aggregation-designer" in file and "schema-workbench" in file:
                # Discard "aggregation-designer" and "schema-workbench" since they don't have feature .xml file
                continue
            if ".xml" in file and "feature" in file:
                if "data-integration" in r:
                    data_integration_dir = os.path.normpath(os.path.join(r[0:r.index('data-integration')], 'data-integration'))
                    if not data_integration_dir_print_once:
                        log.debug('>> Analysing component: ' + data_integration_dir)
                        data_integration_dir_print_once = True
                    karaf_dir = os.path.normpath(os.path.join(data_integration_dir, 'system', 'karaf', 'system'))
                    karaf_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho'))
                    karaf_com_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'com', 'pentaho'))
                    karaf_org_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'org', 'pentaho'))
                    karaf_pentaho_features_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho-karaf-features'))
                    if (karaf_pentaho_dir in r) or (karaf_com_pentaho_dir in r) or (karaf_org_pentaho_dir in r) or (karaf_pentaho_features_dir in r):
                        feature_file = os.path.join(r, file)
                        check_bundle_exist(feature_file, karaf_dir)
                elif "metadata-editor" in r:
                    metadata_editor_dir = os.path.join(r[0:r.index('metadata-editor')], 'metadata-editor')
                    if not metadata_editor_dir_print_once:
                        log.debug('>> Analysing component: ' + metadata_editor_dir)
                        metadata_editor_dir_print_once = True
                    karaf_dir = os.path.normpath(os.path.join(metadata_editor_dir, 'system', 'karaf', 'system'))
                    karaf_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho'))
                    karaf_com_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'com', 'pentaho'))
                    karaf_org_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'org', 'pentaho'))
                    karaf_pentaho_features_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho-karaf-features'))
                    if (karaf_pentaho_dir in r) or (karaf_com_pentaho_dir in r) or (karaf_org_pentaho_dir in r) or (karaf_pentaho_features_dir in r):
                        feature_file = os.path.join(r, file)
                        check_bundle_exist(feature_file, karaf_dir)
                elif "report-designer" in r:
                    report_designer_dir = os.path.join(r[0:r.index('report-designer')], 'report-designer')
                    if not report_designer_dir_print_once:
                        log.debug('>> Analysing component: ' + report_designer_dir)
                        report_designer_dir_print_once = True
                    karaf_dir = os.path.normpath(os.path.join(report_designer_dir, 'system', 'karaf', 'system'))
                    karaf_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho'))
                    karaf_com_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'com', 'pentaho'))
                    karaf_org_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'org', 'pentaho'))
                    karaf_pentaho_features_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho-karaf-features'))
                    if (karaf_pentaho_dir in r) or (karaf_com_pentaho_dir in r) or (karaf_org_pentaho_dir in r) or (karaf_pentaho_features_dir in r):
                        feature_file = os.path.join(r, file)
                        check_bundle_exist(feature_file, karaf_dir)
                elif "pentaho-server" in r:
                    pentaho_server_dir = os.path.join(r[0:r.index('pentaho-server')], 'pentaho-server')
                    if not pentaho_server_dir_print_once:
                        log.debug('>> Analysing component: ' + pentaho_server_dir)
                        pentaho_server_dir_print_once = True
                    karaf_dir = os.path.normpath(os.path.join(pentaho_server_dir, 'pentaho-solutions', 'system', 'karaf', 'system'))
                    karaf_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho'))
                    karaf_com_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'com', 'pentaho'))
                    karaf_org_pentaho_dir = os.path.normpath(os.path.join(karaf_dir, 'org', 'pentaho'))
                    karaf_pentaho_features_dir = os.path.normpath(os.path.join(karaf_dir, 'pentaho-karaf-features'))
                    if (karaf_pentaho_dir in r) or (karaf_com_pentaho_dir in r) or (karaf_org_pentaho_dir in r) or (karaf_pentaho_features_dir in r):
                        feature_file = os.path.join(r, file)
                        check_bundle_exist(feature_file, karaf_dir)
                else:
                    log.debug("The directory" + r)


#################################################
#
#   Method to validate duplicate jars
#
#################################################
def invalid_bundle(installation_dir):
    log.debug('Going to check invalid bundles in Pentaho installation [' + installation_dir + ']')
    invalid_bundle_jars(installation_dir)
    log.debug('Done - check above if anything found!')


#################################################
#
#   Main
#   -> python run.py -d C:\Release\9.0\pdi-ee-client-9.0.0.0-142\data-integration -b 9.0.0
#   -> python run.py -i C:\Release\9.0\pdi-ee-client-9.0.0.0-142\data-integration
#
#################################################
def main():
    count = len(sys.argv)
    if count == 1:
        log.debug('No parameters specified!')
        sys.exit(2)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "d:b:i:", ["duplicate=", "branch=", "invalidbundle="])
    except getopt.GetoptError as err:
        log.debug(err)
        sys.exit(2)

    count = len(opts)
    if count == 0:
        log.debug('No parameters specified!')

    installation_dir = ''
    branch = ''
    is_duplicate = False
    is_invalid = False
    for opt, arg in opts:
        if opt in ('-b', '--branch'):
            branch = arg
        elif opt in ('-d', '--duplicate'):
            is_duplicate = True
            installation_dir = arg
            log.debug('Let\'s check duplicate jars')
        elif opt in ('-i', '--invalidbundle'):
            is_invalid = True
            installation_dir = arg

    if not os.path.isdir(installation_dir):
        log.error('You need to specified a valid directory')
        sys.exit(2)

    if is_duplicate:
        if len(branch) == 0:
            log.error('The branch must be indicated not empty')
            sys.exit(2)
        duplicate(installation_dir, branch)
    if is_invalid:
        invalid_bundle(installation_dir)

    if not is_invalid and not is_duplicate:
        log.error('Incomplete arguments!')
        log.error(
            '-i --installation : path for the directory. e.g. C:\Release\9.0\pdi-ee-client-9.0.0.0-142\data-integration')
        log.error(
            '-d --duplicate : to check on the directory specified for duplicate files but with different versions')
        log.error('Support -i and -d in combination.')


# -------------------------------------------------------
#
#                     BEGIN
#
# -------------------------------------------------------
if __name__ == "__main__":
    main()
