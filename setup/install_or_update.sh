#!/bin/bash

set -ex

TMP_FILE="/tmp/dbus-huaweisun2000-pvinverter.zip"
PICKED_VERSION=""

if [ "$1" == "dev" ] ; then
    # head of main branch
    URL="https://github.com/kcbam/dbus-huaweisun2000-pvinverter/archive/refs/heads/main.zip"
elif [ -z "$1" ]; then
    # latest release
    URL="https://github.com/kcbam/dbus-huaweisun2000-pvinverter/releases/latest/download/project.zip"
elif [[ "$1" =~ ^v ]]; then
    PICKED_VERSION="$1"
    URL="https://github.com/kcbam/dbus-huaweisun2000-pvinverter/releases/download/${PICKED_VERSION}/project.zip"
else
    URL="${1}"
fi

rm -f ${TMP_FILE}

mkdir -p /data/dbus-huaweisun2000-pvinverter

wget -q -O ${TMP_FILE} ${URL}
if [ "$1" == "dev" ] || [ -z "${PICKED_VERSION}" ] || [ -n "$1" ]; then
    unzip -o ${TMP_FILE} -d /tmp
    ZIPDIR="`unzip -l ${TMP_FILE} | grep dbus-huaweisun2000 | head -n 2 | tail -n 1 | awk '{ print $4 }'`"
    if [ ! -d /tmp/${ZIPDIR} ]; then
        echo "ERROR: Expected the zipfile to unzip into /tmp/${ZIPDIR} but it seems to not be the case. Please check."
        exit 1
    fi
    rm -rf /tmp/${ZIPDIR}/.git*
    cp -a /tmp/${ZIPDIR}/* /data/dbus-huaweisun2000-pvinverter/
    rm -rf /tmp/${ZIPDIR}
else
    unzip -o ${TMP_FILE} -d /data/dbus-huaweisun2000-pvinverter
fi
rm -f ${TMP_FILE}

chmod a+x /data/dbus-huaweisun2000-pvinverter/install.sh

/data/dbus-huaweisun2000-pvinverter/install.sh
/data/dbus-huaweisun2000-pvinverter/restart.sh
