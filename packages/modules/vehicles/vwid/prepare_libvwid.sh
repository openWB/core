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
/get_status(self):/s/get_status(self):/get_status(self):\n        url = API_BASE + "\/vehicles\/" + self.vin + "\/selectivestatus?jobs=all"/
/get(API_BASE/s/(.*,/(url,/
/self\.log = /s/(.*)/("soc."+__name__)/
' < libvwid.org > libvwid.mod

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
		chmod +x libvwid.py
	else
		echo "libvwid.py is not replaced"
	fi
else
	echo "found flake8 issues:"
	cat libvwid.flake8
fi

echo "preparation if libvwid.py completed"
