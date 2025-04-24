import util
from agents.dummy_agent import DummyAgent
from rtde_client import RtdeClient
from ur3_env import Ur3
import numpy as np

rtde_client = RtdeClient(util.ROBOT_HOST)
ur3 = Ur3(rtde_client)
agent = DummyAgent(f"robot_data/episode{util.EPISODE}.csv")

ln_instructions = [
    "Pick up red cub and place it on top of the blue plate.",
    "Pick up blue tumbler and place it inside the green cup.",
    "Pick up blue tumbler and put it inside the yellow tumbler.",
    "Remove the lid from the red cup and place it on the blue tumbler. Place the red cup upside down on the table.",
    "Move the yellow tumbler to the center of the table.",
    "pickup green cup by handle and place it on the yellow plate.",
    "Stack the red cup on top of the green cup.",
    "Remove the blue tumbler from the green cup and place it on the green plate.",
    "Pickup yellow tumbler and blue tumbler and stack them inside the green cup.",
    "Lift the green cup from the yellow plate and stack it on the blue tumbler.",
    
]
rtde_client.send_robot_pose(agent.get_first())
rtde_client.pause()
episodes = []
obs = ur3.reset()

rtde_client.start()
while True:
    action = agent.next()
    episodes.append({"observation": obs, "action": action, "reward": 0, 
                     "discount": 1, "language_instruction": ln_instructions[util.EPISODE-1]})
    ur3.is_last_step = agent.is_last()
    obs = ur3.step(action, agent.is_last())
    
    if agent.is_last():
        break

np.save(f"episodes/episode{util.EPISODE}.npy", np.array(episodes))
rtde_client.close()