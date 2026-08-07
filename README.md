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

Three GDF-playback pipeline files, one per `game_controller` mode (see its
README), each included by exactly one of the launchers below -- none of them
meant to be launched directly:

- **`calibration_pipeline.launch.xml`** -- acquisition
  (`ros2neuro_acquisition_xdf`) -> filters -> buffer, **no decoder/integrator**.
  Calibration doesn't need a classifier: `training_controller` drives the
  feedback itself via Autopilot and never reads `/integrated/raw` in that
  modality. Included by `calibration.launch.py`.
- **`evaluation_pipeline.launch.xml`** -- the full chain: acquisition ->
  filters -> buffer -> decoder -> integrator
  (`ros2neuro_integrator_buffer`'s `Buffer` plugin, the only integrator
  plugin in this workspace), ending on `/integrated/raw`. Modeled on
  `ros2neuro_decoder_py/launch/example_decoder.launch.xml`. Included by
  `evaluation.launch.py`. The integrator's `integrator.reset_event` is set
  to `781` (`CFeedback`, see `game_controller`'s `Events` struct), so its
  accumulator buffer resets to a neutral 1/n split right when each trial's
  continuous feedback starts -- otherwise the buffer just keeps accumulating
  across trials and the next trial would start biased by the previous one's
  classifier output. This is unrelated to the wheel's own end-of-trial
  reset (see `ros2neuro_feedback_wheel`'s README): one resets the actual
  classification signal at trial *start*, the other just moves the wheel's
  center line back at trial *end* -- neither triggers the other.
- **`asyncronous.launch.xml`** -- the same full chain as
  `evaluation_pipeline.launch.xml`, kept as its own file since it backs a
  different launcher/mode. Included by `control.launch.py` (the
  asynchronous/continuous game control path).

All three replay the bundled GDF file (`ros2neuro_decoder_py/extra/test_mi.gdf`
by default), and the two with a classifier default to the matching trained
model (`eegnet_mi_bhbf`).

All three of `calibration.launch.py` / `evaluation.launch.py` /
`control.launch.py` also start their own XDF recorder, so every session
produces a new GDF (e.g. calibration recordings are what you'd later train a
classifier on). Same `output_directory` / `subject` / `session` arguments as
`bci.launch.py` above; `calibration.launch.py` builds the recorder node
directly (no dependency on `ros2neuro_recorder_xdf`'s own launch file, same
as `training_controller`/`wheel`), the other two include it like
`bci.launch.py` does.

```bash
# training, calibration modality (fake feedback via Autopilot)
ros2 launch launchers_bci calibration.launch.py output_directory:=./recordings subject:=sub-01 session:=01

# training, evaluation modality (real classifier output from the GDF replay)
ros2 launch launchers_bci evaluation.launch.py output_directory:=./recordings subject:=sub-01 session:=01

# asynchronous game control -- also starts game_bridge; point a local game
# server at it first (see the top-level repo README's dummy-mode section)
ros2 launch launchers_bci control.launch.py output_directory:=./recordings subject:=sub-01 session:=01
```
