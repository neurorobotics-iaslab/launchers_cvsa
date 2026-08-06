# launchers_bci

General launch files for the ros2neuro BCI pipeline. This branch
(`cortical_peaks_challenge_2026`) starts fresh for the Cortical Peaks
Challenge 2026 setup -- the project's older CVSA/MI experiment code lives on
other branches (`ic_cvsa`, `lsl_vr`, `simple_cvsa`), unrelated to this one.

## `bci.launch.py`

Combines, via `IncludeLaunchDescription` (reusing each package's own launch
file rather than duplicating its parameters):

- **Acquisition** -- `ros2neuro_acquisition`'s `acquisition.launch.xml`,
  defaulted to the LSL backend's config
  (`ros2neuro_acquisition_lsl/config/lsl_configuration.yaml`). Override
  `acquisition_config` to point at a different backend (gusbamp, eegdev,
  dummy) once needed.
- **Recording** -- `ros2neuro_recorder_xdf`'s `xdf_recorder.launch.py`
  (XDF/GDF/BDF output via `xdffileio`).
- **Game control** -- `game_controller`'s `two_class_threshold.launch.py`.
- **Feedback wheel** -- `ros2neuro_feedback_wheel`'s `wheel.launch.xml`,
  `mode:=control`, `input_topic` pointed at the controller's `control_topic`.

Not included yet, deliberately -- to be added later: `game_bridge` and the
other acquisition backends. This launch file assumes real (or LSL-streamed)
hardware upstream of acquisition -- for testing the whole thing without
hardware, see the GDF-playback launchers below instead.

### Usage

```bash
ros2 launch launchers_bci bci.launch.py framerate:=512
ros2 launch launchers_bci bci.launch.py framerate:=512 subject:=sub-01 session:=01 threshold_1:=0.25
```

`framerate` has no default and must be passed explicitly -- it depends on
the actual EEG headset/stream, and a guessed default could silently produce
mis-timed recordings instead of failing loudly.

| Argument             | Default                                             | What                                  |
| --------------------- | ---------------------------------------------------- | -------------------------------------- |
| `acquisition_config`  | `ros2neuro_acquisition_lsl`'s `lsl_configuration.yaml` | Acquisition parameter file           |
| `framerate`            | *(required)*                                          | EEG framerate in Hz                   |
| `output_directory`     | `.`                                                   | Recorder output directory             |
| `subject`              | `unknown`                                             | Recorder subject id                   |
| `session`              | *(empty)*                                             | Recorder session id                   |
| `threshold_1..4`       | `0.3` / `0.4` / `0.6` / `0.7`                          | See `game_controller`'s README        |

## Testing without hardware: GDF playback

`mi_pipeline.launch.xml` replays a bundled GDF file
(`ros2neuro_decoder_py/extra/test_mi.gdf`, with the matching trained model
`eegnet_mi_bhbf`) through the full classification chain -- acquisition
(`ros2neuro_acquisition_xdf`) -> filters -> buffer -> decoder -> integrator
(`ros2neuro_integrator_buffer`'s `Buffer` plugin, the only integrator plugin
in this workspace) -- ending on `/integrated/raw`. Modeled on
`ros2neuro_decoder_py/launch/example_decoder.launch.xml`. Not meant to be
launched directly; it's included by the three launchers below, one per
`game_controller` mode (see its README):

```bash
# training, calibration modality (fake feedback via Autopilot)
ros2 launch launchers_bci calibration.launch.py

# training, evaluation modality (real classifier output from the GDF replay)
ros2 launch launchers_bci evaluation.launch.py

# asynchronous game control -- also starts game_bridge; point a local game
# server at it first (see the top-level repo README's dummy-mode section)
ros2 launch launchers_bci control.launch.py
```
