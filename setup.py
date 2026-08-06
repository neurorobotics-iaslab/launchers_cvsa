from setuptools import setup

package_name = "launchers_bci"

setup(
    name=package_name,
    version="0.0.1",
    packages=[],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (
            f"share/{package_name}/launch",
            [
                "launch/bci.launch.py",
                "launch/mi_pipeline.launch.xml",
                "launch/calibration.launch.py",
                "launch/evaluation.launch.py",
                "launch/control.launch.py",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Paolo",
    maintainer_email="forin.paolo98@gmail.com",
    description="General launch files for the ros2neuro BCI pipeline.",
    license="Apache-2.0",
)
