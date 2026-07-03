# EquiPilot AI - Package Setup
# Required for Railway deployment

from setuptools import find_packages, setup

setup(
    name="equipilot-ai",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.12",
)