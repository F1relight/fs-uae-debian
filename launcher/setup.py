from setuptools import setup, find_packages

setup(
name = "fs_uae_launcher",
version = "2.2.3",
author = "Frode Solheim",
author_email = "fs-uae@fengestad.no",
install_requires = ["wxPython", "pygame"],
packages = find_packages(),
package_data = {
    "": ["*.png", "*.dat"],
},
scripts=["scripts/fs-uae-launcher"],
)
