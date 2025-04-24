import dm_env
from dm_env import specs
import numpy as np
from rtde_client import RtdeClient
from image_capture import ImageCapture


class Ur3(dm_env.Environment):
  
  def __init__(self, ur3_arm: RtdeClient, seed: int = 1):
    self._ur3_arm = ur3_arm
    self._camera = ImageCapture()

    self._rng = np.random.RandomState(seed)
    
    self._reset_next_step = True
    self.is_last_step = False

  def reset(self) -> dm_env.TimeStep:
    """Returns the first `TimeStep` of a new episode."""
    self._reset_next_step = False
    return dm_env.restart(self._observation())

  def step(self, action: list, is_last_step=False) -> dm_env.TimeStep:
    """Updates the environment according to the action."""
    self._ur3_arm.move_robot_to_target(action)

    if is_last_step:
      return dm_env.termination(reward=0, observation=self._observation())
    else:
      return dm_env.transition(reward=0., observation=self._observation())

  def observation_spec(self) -> specs.BoundedArray:
    """Returns the observation spec."""
    return specs.BoundedArray(
        shape=(224, 224, 3),
        dtype=np.uint8,
        name="image",
        minimum=0,
        maximum=255,
    )

  def action_spec(self) -> specs.BoundedArray:
    """Returns the action spec."""
    return specs.BoundedArray(
        shape=(7,),
        dtype=np.float32,
        name="action",
        minimum=-1.0,
        maximum=1.0,
    )

  def _observation(self) -> np.ndarray:
    return self._camera.take_photo()
  
