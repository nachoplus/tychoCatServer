from setuptools import setup, find_packages
from setuptools.command.build import build
import subprocess



def compile_and_install_software():
    """Used the subprocess module to compile/install the C software."""
    src_path = './ucac4.src/'
    print("Installing ucac4 swig rutines")
    cmd='swig -python ucac4.i'
    subprocess.check_call(cmd, cwd=src_path, shell=True)    
    cmd='gcc -c ucac4.c ucac4_wrap.c  -fPIC $(pkg-config --cflags python3) -fno-stack-protector'
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='ld -shared ucac4.o ucac4_wrap.o -o _ucac4.so $(pkg-config --libs python3)'
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='cp _ucac4.so  ucac4.py ../build/lib/tychoCatServer'
    subprocess.check_call(cmd, cwd=src_path, shell=True)

    #First pass
    src_path = './lunar/'
    cmd='make clean'
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='export PREFIX=../build && make '
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='export PREFIX=../build && make install'
    subprocess.check_call(cmd, cwd=src_path, shell=True) 

    src_path = './jpl_eph/'
    cmd='make clean'
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='export PREFIX=../build && make'
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='export PREFIX=../build && make install'
    subprocess.check_call(cmd, cwd=src_path, shell=True)    

    #Lunar second pass
    src_path = './lunar/'
    cmd='make clean'
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='export PREFIX=../build && make integrat'
    subprocess.check_call(cmd, cwd=src_path, shell=True)
    cmd='cp integrat ../build/lib/tychoCatServer'
    subprocess.check_call(cmd, cwd=src_path, shell=True)     





class CustomBuild(build):
    """Custom handler for the 'build' command."""
    def run(self):
        super().run()
        compile_and_install_software()
        



with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="tychoCatServer",
    setup_requires=['setuptools-git-versioning'],
    author="nachomas",
    author_email="mas.ignacio@gmail.com",
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nachoplus/tychoCatServer.git",
    packages=find_packages(),
    install_requires=[
        'astropy~=7.0.1',
        'certifi~=2025.1.31',
        'DateTime~=5.5',
        'ephem~=4.2',
        'numpy~=2.2.3',
        'pytz~=2025.1',
        'recordtype~=1.4',
        'regex~=2024.11.6',
        'requests~=2.32.3',
        'simplejson~=3.20.1',
        'urllib3~=2.3.0',
        'urlparse2~=1.1.1',
        'XlsxWriter~=3.2.2',
        'click~=8.1'
    ],
    extras_require={

    },
    setuptools_git_versioning={
        "enabled": True,
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    cmdclass={'build': CustomBuild},
    include_package_data=True
)
