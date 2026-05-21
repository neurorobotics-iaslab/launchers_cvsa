# launchers_bci

Top-level ROS launch files that wire the full BCI+VR pipeline. All launchers target the **LiveAmp EEG amplifier** (LSL stream) and the **Pico 4 VR headset** (Unity/OpenXR over ROS-TCP-Endpoint).

---

## 1. Launchers

| File | Modality | sLDA | VR | Use |
|------|----------|------|----|-----|
| `calibration.launch` | calibration | Autopilot (synthetic) | ✓ | Collect calibration data — no real classifier |
| `evaluation.launch` | evaluation | real sLDA | ✓ | Online BCI session with live feedback |
| `test_evaluation.launch` | evaluation | real sLDA | ✗ | Pipeline smoke-test (no VR, no recorder) |
| `visualizer_lsl.launch` | — | — | — | Standalone LSL stream oscilloscope |

---

## 2. Paradigms

| Paradigm | arg value | Classes | EEG control | VR axis |
|----------|-----------|---------|-------------|---------|
| Motor Imagery | `mi` | 769, 770 | imagined LH/RH movement | cube vertical position |
| Covert Visual Spatial Attention | `cvsa` | 730, 731 | spatial attention L/R | cube transparency |
| Hybrid (Bayesian fusion) | `hybrid` | 750, 751 | MI + CVSA fused | both axes |

---

## 3. Nodes started by `evaluation.launch`

```
rosneuro_acquisition  (LSLDevice)     /neurodata
  ├─ processing_fbcsp_mi             /mi/eeg_fbcsp     (if paradigm = mi | hybrid)
  ├─ processing_fbcsp_cvsa           /cvsa/eeg_fbcsp   (if paradigm = cvsa | hybrid)
  └─ artifactDetector_node           /artifact_presence

/mi/eeg_fbcsp    → slda_node_mi    → /mi/neuroprediction/raw
/cvsa/eeg_fbcsp  → slda_node_cvsa  → /cvsa/neuroprediction/raw

integrator (rosneuro::integrator::Buffer)
  → /{paradigm}/neuroprediction/integrated/raw
  → /{paradigm}/neuroprediction/integrated/normalized

training_node   (state machine, event 781 per trial)
scene_manager   (selects Unity scene based on paradigm)
ros_tcp_endpoint (TCP bridge to Unity VR on Pico 4)
recorder        (GDF file to recordings/{subject}/{modality}/)
bag_node        (ROS bag + rosparam YAML dump, used by matlab_simulation)
```

In **calibration** mode `training_node` drives an `Autopilot` node (LinearPilot for active classes, SinePilot for rest) instead of real sLDA outputs.

---

## 4. Key parameters

### Common

| Arg | Default | Description |
|-----|---------|-------------|
| `paradigm` | `cvsa` | `mi` \| `cvsa` \| `hybrid` |
| `subject` | `c7` | Subject ID used in recording paths |
| `modality` | `evaluation` | `calibration` \| `evaluation` |
| `trials` | `[10, 10]` | Trials per class `[n_class1, n_class2]` |

### Acquisition (LSL)

| Arg | Default | Description |
|-----|---------|-------------|
| `samplerate` | `500` | EEG sample rate (Hz) |
| `framerate` | `20` | Processing rate (Hz); `chunkSize = samplerate / framerate` |
| `nchannels` | `32` | EEG channels (must match LiveAmp config) |
| `stream_name` | `LiveAmpSN-054211-0242` | LSL stream name |

### Frequency bands

| Arg | Default | Description |
|-----|---------|-------------|
| `filters_band_mi` | `"8.0 10.0; 10.0 12.0; 12.0 14.0; 8.0 14.0; 14.0 20.0; 20.0 28.0;"` | MI bandpass edges (semicolon-separated) |
| `filters_band_cvsa` | `"8.0 10.0; 10.0 12.0; 12.0 14.0; 8.0 14.0; 14.0 20.0;"` | CVSA bandpass edges |

> **Critical:** `filters_band_*` must match the `bands` field in the corresponding CSP yaml — `Fbcsp.cpp` aborts with a fatal error on mismatch (tolerance 1e-4 Hz).

### Integrator / buffer

| Arg | Default | Description |
|-----|---------|-------------|
| `bufferSize` | `40` | Integration window in chunks (40 / 20 Hz = 2 s) |
| `k_gain` | `1.5` | SOFT-mode step scaling (`step = k_gain × |p−0.5| × 2 / bufferSize`) |
| `thresholds` | `[1.0, 0.8]` | Per-class normalised trigger threshold — tune per subject |
| `init_val` | `[0.5, 0.5]` | Buffer initial value (reset at each event 781) |

### VR bridge

| Arg | Default | Description |
|-----|---------|-------------|
| `tcp_ip` | `10.9.2.20` | IP of the Unity/Pico 4 machine |
| `tcp_port` | `10000` | ROS-TCP-Endpoint port |

---

## 5. Model paths

| Arg | Default (test model — override for real subjects) |
|-----|--------------------------------------------------|
| `path_csp_mi` | `$(find processing_bci)/cfg/csp/mi/csp_mi_test.yaml` |
| `path_csp_cvsa` | `$(find processing_bci)/cfg/csp/cvsa/csp_cvsa_test.yaml` |
| `path_slda_model_mi` | `$(find slda_bci)/models/mi/slda_mi_test.yaml` |
| `path_slda_model_cvsa` | `$(find slda_bci)/models/cvsa/slda_cvsa_test.yaml` |

The CSP yaml is loaded **inside each `<node>` tag** (private namespace) so MI and CVSA instances don't collide. The sLDA yaml is passed as a node parameter `path_slda_model`.

---

## 6. Data saved

Recordings go to:

```
/home/paolo/bci_vr_ws/recordings/{subject}/{modality}/
  ├── {subject}_{task}_{timestamp}.gdf        ← raw EEG (rosneuro_recorder)
  ├── {subject}_{paradigm}_{modality}_{timestamp}.bag  ← ROS bag (bag_bci)
  └── {subject}_{paradigm}_{modality}_{timestamp}.yaml ← rosparam dump (bag_bci)
```

The companion YAML is the input to `matlab_simulation/main_simulate.m` and `main_evaluate_metrics.m` — it contains every node's parameters (CSP/sLDA paths, integrator settings, CAR, artifact thresholds) resolved at launch time.

---

## 7. Quick start

```bash
# Calibration (MI)
roslaunch launchers_bci calibration.launch paradigm:=mi subject:=S01

# Evaluation (CVSA, real sLDA, new model)
roslaunch launchers_bci evaluation.launch \
    paradigm:=cvsa subject:=S01 \
    path_csp_cvsa:=$(find processing_bci)/cfg/csp/cvsa/csp_S01_<timestamp>.yaml \
    path_slda_model_cvsa:=$(find slda_bci)/models/cvsa/slda_S01_<timestamp>.yaml

# Evaluation (Hybrid)
roslaunch launchers_bci evaluation.launch \
    paradigm:=hybrid subject:=S01 \
    path_csp_mi:=...   path_slda_model_mi:=... \
    path_csp_cvsa:=... path_slda_model_cvsa:=...

# Pipeline smoke-test (no VR)
roslaunch launchers_bci test_evaluation.launch paradigm:=mi subject:=S01

# LSL stream visualizer
roslaunch launchers_bci visualizer_lsl.launch
```
