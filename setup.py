from setuptools import setup, find_packages
import re

requirements = []
with open("Pipfile") as f:
    pipfile = f.read()
    pipfile_packages = re.findall(r"\[packages\](\n(?:.*\n)+?)\n", pipfile)[0]
    for package_line in pipfile_packages.strip().split("\n"):
        requirements.append(package_line.split("=")[0].strip())

version = ""
with open("lusportscentre/__init__.py") as f:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE
    ).group(1)


setup(
    name="lusportscentre",
    url="https://www.github.com/ravenkls/lusportscentre/",
    version=version,
    packages=find_packages(),
    license="MIT",
    description="A simple wrapper for the Lancaster Sports Centre API, allowing you to book sessions etc.",
    install_requires=requirements,
    python_requires=">=3.8.0",
)
