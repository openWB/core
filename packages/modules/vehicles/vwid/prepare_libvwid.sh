echo "downloading libvwid.py  from github to libvwid.org"
curl -sS -o libvwid.org https://raw.githubusercontent.com/skagmo/ha_vwid/main/custom_components/vwid/libvwid.py

echo "apply known flake8 fixes to libvwid.org, direct logging to soc.log"
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

# add backup and restore of refreshToken to avoid both tokens to be replaced when accessToken is refreshed
echo "add backup / restore of refreshToken accessToken renewal"
ex -s libvwid.mod <<EOF
/# Use the newly received access token/-3 a

        self.refreshTokenBackup = self.tokens['refreshToken']    # remember current refreshToken
.
/# Use the newly received access token/-2 a
        self.tokens['refreshToken'] = self.refreshTokenBackup    # restore previous refreshToken
.
wq
EOF

echo "checking libvwid.mod for flake8 issues"
flake8 libvwid.mod > libvwid.flake8
l=`wc -l libvwid.flake8 | awk '{print $1}'`
if [ $l -eq 0 ]
then
   echo "libvwid is flake8 clean"
   echo "diff to previous libvwid.py"
   diff libvwid.py libvwid.mod
   echo "replace libvwid.py by libvwid.mod?(Y)"
   read a
   if [ "$a" == "Y" ]
   then
      mv libvwid.mod libvwid.py
   else
      echo "libvwid.py is not replaced"
   fi
else
   echo "found flake8 issues:"
   cat libvwid.flake8
fi

echo "preparation if libvwid.py completed"
