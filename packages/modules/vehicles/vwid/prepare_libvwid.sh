#echo "doenloading libvwid.py  from github to libvwid.org"
#curl -sS -o libvwid.org https://raw.githubusercontent.com/skagmo/ha_vwid/main/custom_components/vwid/libvwid.py

echo "apply known flake8 fixes to libvwid.org, resulting in libvwid.mod"
sed '
s/\t/    /g
/^import aiohttp/s/import/# import/
/^import asyncio/s/import/# import/
/^class vwid:/i
/action = /s/ % /\\\n                % /
s/^ *$//
s/ $//
/query = /s/ : /: /
/query = /s/) ]/)]/
/self\.log = /s/(.*)/("soc."+__name__)/
/self\.log\.debug(/s/log.debug("/log.debug("vwid.libvwid: /
/self\.log\.error(/s/log.error("/log.debug("vwid.libvwid: /
/self\.log\.warn(/s/log.warn("/log.debug("vwid.libvwid: /
/self\.log\.info(/s/log.info("/log.debug("vwid.libvwid: /
' < libvwid.org > libvwid.mod

echo "checking libvwid.mod for flake8 issues"
flake8 libvwid.mod > libvwid.flake8
l=`wc -l libvwid.flake8 | awk '{print $1}'`
if [ $l -eq 0 ]
then
   echo "libvwid is flake8 clean"
   echo "replace libvwid.py by libvwid.mod?(Y)"
   read a
   if [ "$a" == "Y" ]
   then
      mv libvwid.mod libvwid.py
   fi
else
   cat libvwid.flake8
fi

