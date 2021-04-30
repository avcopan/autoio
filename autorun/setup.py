""" Install autorun
"""
from distutils.core import setup


setup(name="autorun",
      version="0.1.0",
      packages=["autorun",
                "autorun.tests",
                "autorun.tests.data"],
      package_data={
          'autorun': ['autorun/tests/data/*']})
               # "autorun.tests"])
               # "autorun.aux"])#,
               # "autorun.tests"])