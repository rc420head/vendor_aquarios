#!/usr/bin/env python

# Copyright (C) 2013 Cybojenix <anthonydking@gmail.com>
# Copyright (C) 2013 The OmniROM Project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import os.path
import sys
import urllib2
import json
import re
import subprocess
from xml.etree import ElementTree
from urllib2 import urlopen, Request

product = sys.argv[1];

if len(sys.argv) > 2:
    depsonly = sys.argv[2]
else:
    depsonly = None

try:
    device = product[product.index("_") + 1:]
except:
    device = product

if not depsonly:
    print "Device %s not found. Attempting to retrieve device repository from AquariOS Devices Github (http://github.com/Aqua-devices)." % device

repositories = []

# repo check
branch_check = r'external/bson'
if os.path.exists(branch_check):
    aqua_branch = "x-ng";
else:
    aqua_branch = "x";

# gapps
repo_check = r'vendor/pixelgapps'
gapps_location = 'vendor/pixelgapps'
gapps_git = 'https://gitlab.com/AquariOS/vendor_pixelgapps'
gapps_branch = 'x'

# vendor_images
repo_check = r'vendor/images'
images_location = 'vendor/images'
images_git = 'https://gitlab.com/DirtyUnicorns/android_vendor_images'
images_branch = 'q10x'

page = 1
while not depsonly:
    request = Request("https://api.github.com/users/Aqua-devices/repos?page=%d" % page)
    api_file = os.getenv("HOME") + '/api_token'
    if (os.path.isfile(api_file)):
        infile = open(api_file, 'r')
        token = infile.readline()
        request.add_header('Authorization', 'token %s' % token.strip())
    result = json.loads(urllib2.urlopen(request).read())
    if len(result) == 0:
        break
    for res in result:
        repositories.append(res)
    page = page + 1

local_manifests = r'.repo/local_manifests'
if not os.path.exists(local_manifests): os.makedirs(local_manifests)

def exists_in_tree(lm, repository):
    for child in lm.getchildren():
        if child.attrib['path'].endswith(repository):
            return child
    return None

def exists_in_tree_device(lm, repository):
    for child in lm.getchildren():
        if child.attrib['name'].endswith(repository):
            return child
    return None

# in-place prettyprint formatter
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def get_from_manifest(devicename):
    try:
        lm = ElementTree.parse(".repo/local_manifests/aqua_manifest.xml")
        lm = lm.getroot()
    except:
        lm = ElementTree.Element("manifest")

    for localpath in lm.findall("project"):
        if re.search("android_device_.*_%s$" % device, localpath.get("name")):
            return localpath.get("path")

    # Devices originally from AOSP are in the main manifest...
    try:
        mm = ElementTree.parse(".repo/manifest.xml")
        mm = mm.getroot()
    except:
        mm = ElementTree.Element("manifest")

    for localpath in mm.findall("project"):
        if re.search("android_device_.*_%s$" % device, localpath.get("name")):
            return localpath.get("path")

    return None

def is_in_manifest(projectname, branch):
    try:
        lm = ElementTree.parse(".repo/local_manifests/aqua_manifest.xml")
        lm = lm.getroot()
    except:
        lm = ElementTree.Element("manifest")

    for localpath in lm.findall("project"):
        if localpath.get("name") == projectname and localpath.get("revision") == branch:
            return 1

    return None

def add_to_manifest_dependencies(repositories):
    try:
        lm = ElementTree.parse(".repo/local_manifests/aqua_manifest.xml")
        lm = lm.getroot()
    except:
        lm = ElementTree.Element("manifest")

    for repository in repositories:
        repo_name = repository['repository']
        repo_target = repository['target_path']
        existing_project = exists_in_tree(lm, repo_target)
        if existing_project != None:
            if existing_project.attrib['name'] != repository['repository']:
                print 'Updating dependency %s' % (repo_name)
                existing_project.set('name', repository['repository'])
            if existing_project.attrib['revision'] == repository['branch']:
                print 'Aqua-devices/%s already exists' % (repo_name)
            else:
                print 'updating branch for %s to %s' % (repo_name, repository['branch'])
                existing_project.set('revision', repository['branch'])
            continue

        print 'Adding dependency: %s -> %s' % (repo_name, repo_target)
        project = ElementTree.Element("project", attrib = { "path": repo_target,
            "remote": "github", "name": repo_name, "revision": aqua_branch })

        if 'branch' in repository:
            project.set('revision',repository['branch'])

        lm.append(project)

    indent(lm, 0)
    raw_xml = ElementTree.tostring(lm)
    raw_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml

    f = open('.repo/local_manifests/aqua_manifest.xml', 'w')
    f.write(raw_xml)
    f.close()

def add_to_manifest(repositories):
    try:
        lm = ElementTree.parse(".repo/local_manifests/aqua_manifest.xml")
        lm = lm.getroot()
    except:
        lm = ElementTree.Element("manifest")

    for repository in repositories:
        repo_name = repository['repository']
        repo_target = repository['target_path']
        existing_project = exists_in_tree_device(lm, repo_name)
        if existing_project != None:
            if existing_project.attrib['revision'] == repository['branch']:
                print 'Aqua-devices/%s already exists' % (repo_name)
            else:
                print 'updating branch for Aqua-devices/%s to %s' % (repo_name, repository['branch'])
                existing_project.set('revision', repository['branch'])
            continue

        print 'Adding dependency: Aqua-devices/%s -> %s' % (repo_name, repo_target)
        project = ElementTree.Element("project", attrib = { "path": repo_target,
            "remote": "github", "name": "Aqua-devices/%s" % repo_name, "revision": aqua_branch })

        if 'branch' in repository:
            project.set('revision', repository['branch'])

        lm.append(project)

    indent(lm, 0)
    raw_xml = ElementTree.tostring(lm)
    raw_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml

    f = open('.repo/local_manifests/aqua_manifest.xml', 'w')
    f.write(raw_xml)
    f.close()

def git(*args):
    return subprocess.check_call(['git'] + list(args))

def add_gitlab_to_manifest(repositories):
    try:
        lm = ElementTree.parse(".repo/local_manifests/aqua_manifest.xml")
        lm = lm.getroot()
    except:
        lm = ElementTree.Element("manifest")

    for repository in repositories:
        repo_name = repository['repository']
        repo_target = repository['target_path']
        existing_project = exists_in_tree_device(lm, repo_name)
        if existing_project != None:
            if existing_project.attrib['revision'] == repository['branch']:
                print 'Nothing to see here'
            else:
                existing_project.set('revision', repository['branch'])
            continue

        project = ElementTree.Element("project", attrib = { "path": repo_target,
            "remote": "gitlab", "name": repo_name, "revision": aqua_branch })

        if 'branch' in repository:
            project.set('revision', repository['branch'])

        lm.append(project)

    indent(lm, 0)
    raw_xml = ElementTree.tostring(lm)
    raw_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml

    f = open('.repo/local_manifests/aqua_manifest.xml', 'w')
    f.write(raw_xml)
    f.close()

def fetch_pixel_gapps(repo_path):
    gapps_path = repo_path + '/aquarios.mk'
    with open(gapps_path, 'r') as f:
        for line in f.readlines():
            if 'pixelgapps' in line:
                print 'Fetching project ' + gapps_git.replace("https://gitlab.com/", "")
                git("clone", gapps_git, "-b", gapps_branch, gapps_location)
                add_gitlab_to_manifest([{'repository':gapps_git.replace("https://gitlab.com/", ""),'target_path':gapps_location,'branch':gapps_branch}])

def fetch_vendor_images(repo_path):
    images_path = repo_path + '/aquarios.mk'
    with open(images_path, 'r') as f:
        for line in f.readlines():
            if 'BOARD_PREBUILT_VENDORIMAGE' in line:
                print 'Fetching project ' + images_git.replace("https://gitlab.com/", "")
                git("clone", images_git, "-b", images_branch, images_location)
                add_gitlab_to_manifest([{'repository':images_git.replace("https://gitlab.com/", ""),'target_path':images_location,'branch':images_branch}])

def fetch_dependencies(repo_path):
    print 'Looking for dependencies'
    dependencies_path = repo_path + '/aqua.dependencies'
    syncable_repos = []

    if os.path.exists(dependencies_path):
        dependencies_file = open(dependencies_path, 'r')
        dependencies = json.loads(dependencies_file.read())
        fetch_list = []

        for dependency in dependencies:
            if not is_in_manifest("%s" % dependency['repository'], "%s" % dependency['branch']):
                fetch_list.append(dependency)
                syncable_repos.append(dependency['target_path'])

        dependencies_file.close()

        if len(fetch_list) > 0:
            print 'Adding dependencies to manifest'
            add_to_manifest_dependencies(fetch_list)
    else:
        print 'Dependencies file not found, bailing out.'

    if len(syncable_repos) > 0:
        print 'Syncing dependencies'
        if not os.path.exists(repo_check):
            fetch_pixel_gapps(repo_path)
            fetch_vendor_images(repo_path)
        os.system('repo sync %s' % ' '.join(syncable_repos))

if depsonly:
    repo_path = get_from_manifest(device)
    if repo_path:
        fetch_dependencies(repo_path)
    else:
        print "Trying dependencies-only mode on a non-existing device tree?"

    sys.exit()

else:
    for repository in repositories:
        repo_name = repository['name']
        if repo_name.startswith("device_") and repo_name.endswith("_" + device):
            print "Found repository: %s" % repository['name']
            manufacturer = repo_name.replace("device_", "").replace("_" + device, "")

            repo_path = "device/%s/%s" % (manufacturer, device)

            add_to_manifest([{'repository':repo_name,'target_path':repo_path,'branch':aqua_branch}])

            print "Syncing repository to retrieve project."
            os.system('repo sync %s' % repo_path)
            print "Repository synced!"

            fetch_dependencies(repo_path)
            print "Done"
            sys.exit()

print "Repository for %s not found in the AquariOS Devices Github repository list. If this is in error, you may need to manually add it to .repo/local_manifests/aqua_manifest.xml" % device
