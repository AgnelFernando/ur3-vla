#!/usr/bin/env python
# Copyright (c) 2016-2022, Universal Robots A/S,
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the Universal Robots A/S nor the names of its
#      contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL UNIVERSAL ROBOTS A/S BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import time
sys.path.append("..")

import rtde.rtde as rtde
import rtde.rtde_config as rtde_config

class RtdeClient:
    def __init__(self, robot_host):
        robot_port = 30004
        conf = rtde_config.ConfigFile("configs/rtde_config.xml")
        state_names, state_types = conf.get_recipe("state")
        setp_names, setp_types = conf.get_recipe("setp")
        watchdog_names, watchdog_types = conf.get_recipe("watchdog")
        self.con = rtde.RTDE(robot_host, robot_port)
        self.con.connect()
        self.current_pose = None
        self.target_pose = None
        
        self.con.get_controller_version()
        print("Connected to robot.")

        self.con.send_output_setup(state_names, state_types)
        self.setp = self.con.send_input_setup(setp_names, setp_types)
        self.watchdog = self.con.send_input_setup(watchdog_names, watchdog_types)

        self.watchdog.input_int_register_0 = 0

        if not self.con.send_start():
            sys.exit()

        # if not self.wait_for_server_ready():
        #     print("Failed to start communication with robot. Exiting.")
        #     sys.exit(1)
        
        self.first_time = True
        

    def update_current_pose(self, pose):
        self.current_pose = pose
        
    def move_robot_to_target(self, delta):
        self.target_pose = [self.current_pose[i] + delta[i] for i in range(0, 6)]
        self.target_pose.append(int(abs(delta[-1])))  
        return self.send_robot_pose(self.target_pose)

    def send_robot_pose(self, pose):
        if self.first_time:
            print("Start the server")
            self.first_time = False
        
        self.update_setp(pose)
        self.con.send(self.setp)
        self.watchdog.input_int_register_0 = 1
        self.con.send(self.watchdog)

        move_completed = False

        while True:
            state = self.con.receive()

            if state is None:
                print("No state received, aborting movement.")
                return False

            if not move_completed and state.output_int_register_0 == 0:
                move_completed = True  
                self.watchdog.input_int_register_0 = 0

            if move_completed and state.output_int_register_0 == 1:
                self.update_current_pose(pose)
                self.watchdog.input_int_register_0 = 1
                self.con.send(self.watchdog)
                return True  

            self.con.send(self.watchdog)


    def update_setp(self, values):
        for i in range(0, 6):
            self.setp.__dict__["input_double_register_%i" % i] = values[i]
        if values[-1] > 0:
            print("Griper value: ", values[-1])
        self.setp.__dict__["input_int_register_6"] = int(values[-1])

    def wait_for_server_ready(self):
        print("Waiting for server response...")
        retries = 10  
        while retries > 0:
            try:
                self.watchdog.input_int_register_0 = 1  
                self.con.send(self.watchdog)

                state = self.con.receive()
                
                if state and state.output_int_register_0 == 1:
                    print("Server is responsive. Robot is ready.")
                    self.watchdog.input_int_register_0 = 0  
                    self.con.send(self.watchdog)
                    return True
                else:
                    print(f"Waiting for server response... Retries left: {retries-1}")
                    retries -= 1
                    time.sleep(1) 

            except Exception as e:
                print(f"Error checking server status: {e}")
                retries -= 1
                time.sleep(1)  

        print("Server did not respond in time. Communication failed.")
        return False

    def pause(self):
        self.con.send_pause()

    def start(self):    
        self.con.send_start()

    def close(self):
        self.pause()
        self.con.disconnect()

        
