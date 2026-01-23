#!/bin/bash

set -ex

TMP_FILE="/tmp/dbus-huaweisun2000-pvinverter.zip"

if [ "$1" == "dev" ] ; then
    # head of main branch
    URL="https://github.com/kcbam/dbus-huaweisun2000-pvinverter/archive/refs/heads/main.zip"
else
    # latest release
    URL="https://github.com/kcbam/dbus-huaweisun2000-pvinverter/releases/latest/download/project.zip"
fi

rm -f ${TMP_FILE}

mkdir -p /data/dbus-huaweisun2000-pvinverter

wget -q -O ${TMP_FILE} ${URL}
if [ "$1" == "dev" ] ; then
    unzip -o ${TMP_FILE} -d /tmp
    rm -rf /tmp/dbus-huaweisun2000-pvinverter-main/.git*
    cp -a /tmp/dbus-huaweisun2000-pvinverter-main/* /data/dbus-huaweisun2000-pvinverter/
    rm -rf /tmp/dbus-huaweisun2000-pvinverter-main
else
    unzip -o ${TMP_FILE} -d /data/dbus-huaweisun2000-pvinverter
fi
rm -f ${TMP_FILE}

chmod a+x /data/dbus-huaweisun2000-pvinverter/install.sh

/data/dbus-huaweisun2000-pvinverter/install.sh