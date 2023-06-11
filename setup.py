import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
    
python_versions = '>=3.6'  # restricted by availability of pyrender

requirements_default = [
    'numpy',
    'open3d',
    'trimesh[easy]',
    'pyyaml',
    'tqdm',
    'opencv-python',
    'matplotlib',
    'pyglet==1.5.21',
    'pyrender',
    'configparser'
]


# merge requirements and remove duplicates
reqs_all = list(set(requirements_default))

setuptools.setup(
    name='v4r_dataset_toolkit',
    version='1.0',
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
