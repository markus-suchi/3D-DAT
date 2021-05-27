import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
    
python_versions = '>=3.6, <3.9'  # restricted by availability of pyrender

requirements_default = [
    'numpy',       
    'open3d==0.9.0', # newer versions do not work with opencv for Ubuntu < 18.04
    'trimesh[easy]',
    'pyyaml',
    'tqdm',
    'opencv-python',
    'matplotlib',
    'pyrender'
]


# merge requirements and remove duplicates
reqs_all = list(set(requirements_default))

setuptools.setup(
    name='Test-toolkit',
    version='0.1',
    python_requires=python_versions,
    install_requires=reqs_all,
    packages=setuptools.find_packages(),
    url='',
    license='',
    author='',
    author_email='',
    description='dataset annotation toolkit',
    long_description=long_description
)
