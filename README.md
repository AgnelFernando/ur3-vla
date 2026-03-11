# Open VLA on UR3 Robot Arm

This repository documents my experiments with **[OpenVLA](https://github.com/openvla/openvla)** an open-source Vision-Language-Action (VLA) model designed to control robots through **visual** and **natural-language** inputs.
My goal was to evaluate how well OpenVLA generalizes to a **UR3 robotic arm** for tabletop manipulation tasks and to explore **fine-tuning** techniques such as **LoRA (Low-Rank Adaptation)** when zero-shot inference fails.

---

## Introduction

OpenVLA represents an exciting step toward general-purpose robot control. It’s the **first fully open-source VLA model**, whereas others like Google’s **RT-1**, **RT-2**, and **Octo** remain closed.

OpenVLA claims to **generalize across robotic platforms** without additional training (zero-shot). However, when deployed on the **UR3 arm**, I found it required task-specific fine-tuning to perform even simple pick-and-place operations.

This project captures my workflow from setting up the UR3 to collecting trajectory data, converting it into RLDS format, and integrating it with OpenVLA’s inference pipeline.

---

## What Is OpenVLA?

OpenVLA is a **Vision-Language-Action foundation model** built on **LLaMA 2**.
It processes:

* **An image** (RGB)
* **A natural-language instruction**

and outputs:

* **Low-level robot actions** (Δx, Δy, Δz, Δrx, Δry, Δrz, gripper Δ)

### Architecture Overview

* Dual visual encoders 
* LLM backbone (LLaMA 2) for semantic grounding
* Transformer-based joint decoder mapping **words + pixels → actions**

---

## Setup & Integration

### **Hardware**

* UR3 Robotic Arm
* Robotiq Hand-E Gripper
* RGB Camera (third-person view)

### **Software**

* **[RTDE](https://www.universal-robots.com/articles/ur/interface-communication/real-time-data-exchange-rtde-guide/)** — for direct control of UR3 and trajectory logging via Python sockets
* **[OpenVLA Repository](https://github.com/openvla/openvla)** — for model architecture and fine-tuning
* **[RLDS Dataset Builder](https://github.com/google-research/rlds)** — to convert collected data into the required training format

---

## Integration Challenges

While OpenVLA provides inference code, **execution on real hardware** is left as a placeholder understandably, since each robot uses a unique API.
This highlights an ongoing problem in robotics: the **lack of standardization** in control interfaces.
Even with ROS, commercial robots like the UR3 rely heavily on **proprietary SDKs**.

---

## Workflow

### Data Collection

OpenVLA was originally trained on the **Open X-Embodiment** dataset (simulation + teleoperation).
The paper suggests 10–20 episodes are enough for fine-tuning a new robot.

Since I didn’t use teleoperation, I adopted a **manual data-logging pipeline**:

1. Program motions using the **UR3 Teach Pendant**
2. Record trajectories using `record_robot_action.py` (CSV with waypoints + gripper states)
3. Capture synchronized **RGB frames** from a third-person camera
4. Generate observation-action pairs via `create_episode.py`
5. Convert to **RLDS format** using the **RLDS Dataset Builder**

---

### Inference Pipeline

During inference (`vla_inference.py`):

* **Inputs**

  * Natural-language command (e.g., “Pick up the red cube.”)
  * Real-time camera image
* **Model Outputs**

  * Predicted deltas (Δx, Δy, Δz, Δrx, Δry, Δrz)
  * Gripper delta value
* **Execution**

  * Apply deltas to the current pose
  * Send target pose + gripper command to UR3 via RTDE

---

## How VLA Interprets Instructions

1. **LLM grounding** — parses the instruction semantically
2. **Vision encoder** — localizes objects in the scene
3. **Joint transformer** — fuses language + visual context
4. **Action decoder** — outputs continuous motion commands

Essentially, the model **maps words and pixels to motion**.

---

## Key Learnings

### Model Limitations

* **Zero-shot ≠ universal:** UR3 was unseen during training, so the model required fine-tuning.
* **Data collection bottleneck:** Without teleoperation, gathering 10–20 episodes is tedious.
* **Single-arm assumption:** OpenVLA currently doesn’t handle multi-arm systems.

### Practical Takeaways

* **Fine-tuning works**, but demands consistent trajectory quality.
* **Standardization gap:** Robotics APIs remain fragmented hindering foundation model integration.
* **Embodiment matters:** Even small hardware differences affect policy transfer.

---

## Conclusion

Experimenting with OpenVLA on a UR3 arm offered a tangible glimpse of **language-conditioned robot control**.
We’ve come a long way from scripting joint trajectories to simply **telling a robot what to do**.

However, several gaps remain:

* Lack of standardized robot APIs
* Challenges in fine-tuning and dataset creation
* Limited generalization across embodiments

Still, this project reinforced how promising open-source models like **OpenVLA** are for the future of **general-purpose robotics**.
With growing community efforts, we may soon reach a point where **teaching a robot** is as easy as **showing and telling**.

---

## Future Work

* Automate teleoperation-based data collection
* Explore multi-arm and multi-object extensions
* Integrate with Isaac Sim for Sim2Real transfer
* Evaluate LoRA fine-tuning performance on UR3 vs UR10

---

## Acknowledgements

* **OpenVLA Team** for releasing the first open Vision-Language-Action model
* **Universal Robots** for the UR3 platform
* **DePaul ROME Lab** for resources and guidance

---

## License

This project follows the same license as the [OpenVLA repository](https://github.com/openvla/openvla).
Please refer to that repository for details.
