from setuptools import setup
import os
from setuptools.command.install import install
from setuptools.command.build_py import build_py

class PreInstall(install):
    def run(self):
        os.symlink("config.example.ini", "llmchat/config.example.ini")
        install.run(self)
        os.unlink("llmchat/config.example.ini")


class PreBuild(build_py):
    def run(self):
        os.symlink("config.example.ini", "llmchat/config.example.ini")
        build_py.run(self)
        os.unlink("llmchat/config.example.ini")


setup(
    cmdclass={
        'install': PreInstall,
        'build_py': PreBuild
    }
)
