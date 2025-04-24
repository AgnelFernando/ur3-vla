from rtde_client import RtdeClient

import util
from agents.open_vla_agent import OpenVla
from ur3_env import Ur3
import numpy as np
from dm_env import StepType


rtde_client = RtdeClient(util.ROBOT_HOST)
ur3 = Ur3(rtde_client)

prompt = "In: What action should the robot take to pick up red cub and place it on top of the blue plate.?\nOut:"

rtde_client.send_robot_pose([-0.1684,-0.3692,0.2822,-0.3151,-3.0613,0.3282, 0.0])
rtde_client.pause()
episodes = []
rtde_client.start()
step = ur3.reset()
agent = OpenVla("openvla/openvla-7b", unnorm_key="ur3_vla")

while True:
    action = agent.predict(step.observation, prompt)
    step = ur3.step(action)

    if step.step_type == StepType.LAST:
        break



rtde_client.close()