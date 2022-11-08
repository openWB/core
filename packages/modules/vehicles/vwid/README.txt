Die python library libvwid.py dient als Basis und wird hier gepflegt:
https://github.com/skagmo/ha_vwid/blob/main/custom_components/vwid/libvwid.py

Folgende python Komponenten werden zusätzlich benötigt, diese werden in requirements.txt eingetragen:
lxml, aiohttp

The script prepare_libvwid.py downloads libvwid.py from github and applies fixes for flake8 issues, 
resulting in a flake8-clean version of libvwid.py
