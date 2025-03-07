from setuptools import setup, find_packages

setup(
    name="openvpn3-gui-pro",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'pycairo',
        'PyGObject',
        'keyring',
        'psutil'
    ],
    entry_points={
        'gui_scripts': [
            'openvpn3-gui-pro=openvpn3_gui.__main__:main'
        ]
    },
    data_files=[
        ('share/applications', ['data/openvpn3-gui-pro.desktop']),
        ('share/icons', ['data/openvpn3-gui-pro.png'])
    ]
)