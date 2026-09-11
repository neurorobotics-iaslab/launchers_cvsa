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
                "launch/gdf/calibration_pipeline.launch.xml",
                "launch/gdf/evaluation_pipeline.launch.xml",
                "launch/gdf/asyncronous.launch.xml",
                "launch/gdf/acquisition_gdf.launch.xml",
                "launch/gdf/calibration_gdf.launch.py",
                "launch/gdf/evaluation_gdf.launch.py",
                "launch/gdf/control_gdf.launch.py",
            ],
        ),
        (
            f"share/{package_name}/launch/lsl",
            [
                "launch/lsl/calibration_pipeline.launch.xml",
                "launch/lsl/evaluation_pipeline.launch.xml",
                "launch/lsl/asyncronous.launch.xml",
                "launch/lsl/acquisition_lsl.launch.xml",
                "launch/lsl/calibration_lsl.launch.py",
                "launch/lsl/evaluation_lsl.launch.py",
                "launch/lsl/control_lsl.launch.py",
                "launch/lsl/visualizer_lsl.launch.py",
            ],
        ),
        (
            f"share/{package_name}/launch/gtec",
            [
                "launch/gtec/calibration_pipeline.launch.xml",
                "launch/gtec/evaluation_pipeline.launch.xml",
                "launch/gtec/asyncronous.launch.xml",
                "launch/gtec/acquisition_gtec.launch.xml",
                "launch/gtec/filters_gtec.launch.xml",
                "launch/gtec/calibration_gtec.launch.py",
                "launch/gtec/evaluation_gtec.launch.py",
                "launch/gtec/controller_bridge_gtec.launch.xml",
                "launch/gtec/control_gtec_general.launch.py",
                "launch/gtec/control_gtec_pong.launch.py",
                "launch/gtec/visualizer_gtec.launch.py",
            ],
        ),
        (
            f"share/{package_name}/launch/test",
            [
                "launch/test/asyncronous_test.launch.xml",
                "launch/test/control_test.launch.py",
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
