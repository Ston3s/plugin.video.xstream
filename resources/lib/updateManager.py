import urllib
import os
import xml.etree.ElementTree as ET
import json
import zipfile
import logger
import xbmc
import xbmcgui
from resources.lib.config import cConfig
try:
    from distutils.version import LooseVersion as V
except:
    from resources.lib.version import LooseVersion as V
from resources.lib.common import addonPath, profilePath
from resources.lib.download import cDownload

## Installation path.
ROOT_DIR = addonPath
XSTREAM_DIRNAME = os.path.basename(ROOT_DIR)

## Remote path to download plugin.zip and version file.
REMOTE_URL_MASTER = "https://api.github.com/repos/Lynx187/plugin.video.xstream/git/refs/tags/"
REMOTE_URL_BETA = "https://github.com/Lynx187/plugin.video.xstream/archive/master.zip"
REMOTE_URL_NIGHTLY = "https://github.com/xStream-Kodi/plugin.video.xstream/archive/nightly.zip"

## Full path of the remote file version.
REMOTE_VERSION_FILE_MASTER = "https://raw.githubusercontent.com/Lynx187/plugin.video.xstream/master/addon.xml"

## Filename of the update File.
LOCAL_FILE_NAME = "xStream_update.zip"
LOCAL_NIGHTLY_VERSION = os.path.join(profilePath, "nightly_commit_sha")


def checkforupdates():
    logger.info("xStream checkforupdates")

    if cConfig().getSetting('UpdateSetting') == "Nightly":
        nightlycommitsXML = urllib.urlopen("https://api.github.com/repos/StoneOffStones/plugin.video.xstream/commits/nightly").read()

        try:
            if not os.path.exists(LOCAL_NIGHTLY_VERSION) or open(LOCAL_NIGHTLY_VERSION).read() != \
                    json.loads(nightlycommitsXML)['sha']:
                update(REMOTE_URL_NIGHTLY)
                open(LOCAL_NIGHTLY_VERSION, 'w').write(json.loads(nightlycommitsXML)['sha'])
        except Exception as e:
            logger.info("Ratelimit reached")
            logger.info(e)

    elif cConfig().getSetting('UpdateSetting') == "Stable":
        oLocalVer = getLocalVersion()

        oRemoteVer = getLastMasterVersion()

        if oLocalVer is not None and oRemoteVer is not None and oRemoteVer > oLocalVer:
            update(getLastMasterDownloadUrl())

    elif cConfig().getSetting('UpdateSetting') == "Beta":
        oLocalVer = getLocalVersion()
        oRemoteVer = getRemoteVersion(REMOTE_VERSION_FILE_MASTER)

        if oLocalVer is not None and oRemoteVer is not None and oRemoteVer > oLocalVer:
            update(REMOTE_URL_BETA)


def getLastMasterVersion():
    lastUrl = getLastMasterDownloadUrl()
    return V(lastUrl.split('/')[-1][1:])


def getLastMasterDownloadUrl():
    apiJson = urllib.urlopen(REMOTE_URL_MASTER).read()
    oJson = json.loads(apiJson)

    lastVersionUrl = next(x['url'] for x in reversed(oJson))
    return lastVersionUrl.replace('git/', 'zipball/')


def getLocalVersion():
    xml = open(os.path.join(ROOT_DIR, "addon.xml")).read()
    version = getVersionFromXML(xml);
    logger.info("xStream Localversion: " + (version.vstring if version is not None else "Unbekannt"))
    return version


def getRemoteVersion(REMOTE_VERSION_URL):
    xml = urllib.urlopen(REMOTE_VERSION_URL).read()
    version = getVersionFromXML(xml);
    logger.info("xStream Remoteversion: " + (version.vstring if version is not None else "Unbekannt"))
    return version


def getVersionFromXML(sXML):
    oEle = getElementTreeFromString(sXML)

    if oEle is not None and 'version' in oEle.attrib:
        version = V(oEle.attrib['version'])
        return version


def getElementTreeFromString(sXML):
    try:
        tree = ET.fromstring(sXML)
        return tree
    except ET.ParseError:
        pass


def update(REMOTE_PATH):
    logger.info("xStream Update URL: " + REMOTE_PATH)
    cDownload().download(REMOTE_PATH, LOCAL_FILE_NAME, False, "Updating xStream")

    updateFile = zipfile.ZipFile(os.path.join(profilePath, LOCAL_FILE_NAME))

    removeFilesNotInRepo(updateFile)

    for index, n in enumerate(updateFile.namelist()):
        if n[-1] != "/":
            dest = os.path.join(ROOT_DIR, "/".join(n.split("/")[1:]))
            destdir = os.path.dirname(dest)
            if not os.path.isdir(destdir):
                os.makedirs(destdir)
            data = updateFile.read(n)
            if os.path.exists(dest):
                os.remove(dest)
            f = open(dest, 'wb')
            f.write(data)
            f.close()
    updateFile.close()

    logger.info("Update Successful")

def removeFilesNotInRepo(updateFile):
    updateFileNameList = [i.split("/")[-1] for i in updateFile.namelist()]

    for root, dirs, files in os.walk(ROOT_DIR):
        if ".git" in root or "pydev" in root or ".idea" in root:
            continue
        else:
            for file in files:
                if file not in updateFileNameList:
                    os.remove(os.path.join(root, file))
