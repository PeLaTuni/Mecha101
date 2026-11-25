from setuptools import find_packages, setup

package_name = 'turtur'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='peetu.lahtinen@tuni.fi',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'forward = turtur.ros2_goforward:main',
            "nav3 = turtur.nav3:main",
            "nav4 = turtur.nav4:main",
        ],
    },
)
