from distutils.core import Extension, setup
from Cython.Build import cythonize

# define an extension that will be cythonized and compiled
ext = Extension(name="runs.mqttpub", sources=["runs/mqttpub.py"])
setup(ext_modules=cythonize(ext, build_dir="build"))
