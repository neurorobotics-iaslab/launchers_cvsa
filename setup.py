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
            f"share/{package_name}/launch/gdf",
            [
                "launch/gdf/bci.launch.py",
                "launch/gdf/calibration_pipeline.launch.xml",
                "launch/gdf/evaluation_pipeline.launch.xml",
                "launch/gdf/asyncronous.launch.xml",
                "launch/gdf/calibration.launch.py",
                "launch/gdf/evaluation.launch.py",
                "launch/gdf/control.launch.py",
            ],
        ),
        (
            f"share/{package_name}/launch/lsl",
            [
                "launch/lsl/bci.launch.py",
                "launch/lsl/calibration_pipeline.launch.xml",
                "launch/lsl/evaluation_pipeline.launch.xml",
                "launch/lsl/asyncronous.launch.xml",
                "launch/lsl/calibration.launch.py",
                "launch/lsl/evaluation.launch.py",
                "launch/lsl/control.launch.py",
                "launch/lsl/visualizer.launch.py",
            ],
        ),
        (
            f"share/{package_name}/launch/gtec",
            [
                "launch/gtec/bci.launch.py",
                "launch/gtec/calibration_pipeline.launch.xml",
                "launch/gtec/evaluation_pipeline.launch.xml",
                "launch/gtec/asyncronous.launch.xml",
                "launch/gtec/calibration.launch.py",
                "launch/gtec/evaluation.launch.py",
                "launch/gtec/control.launch.py",
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
