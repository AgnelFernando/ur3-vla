#!/usr/bin/env python
# Copyright (c) 2020-2022, Universal Robots A/S,
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

import argparse
import logging
import sys
import pandas as pd
import numpy as np

# sys.path.append(".")
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import util

def interpolate_g_transitions(df, steps=10):
    new_rows = []
    for i in range(len(df) - 1):
        row1 = df.iloc[i]
        row2 = df.iloc[i + 1]
        new_rows.append(row1.tolist())

        if row1['g'] != row2['g']:
            g_start = row1['g']
            g_end = row2['g']
            delta = (g_end - g_start) / steps

            for step in range(1, steps):
                interpolated_row = row2.copy()
                interpolated_row['g'] = g_start + delta * step
                new_rows.append(interpolated_row.tolist())

    new_rows.append(df.iloc[-1].tolist())

    return pd.DataFrame(new_rows, columns=df.columns)

conf = rtde_config.ConfigFile("configs/record_configuration.xml")
output_names, output_types = conf.get_recipe("out")

con = rtde.RTDE(util.ROBOT_HOST, 30004)
con.connect()

# get controller version
con.get_controller_version()

# setup recipes
if not con.send_output_setup(output_names, output_types, frequency=200):
    logging.error("Unable to configure output")
    sys.exit()

# start data synchronization
if not con.send_start():
    logging.error("Unable to start synchronization")
    sys.exit()

df = pd.DataFrame(columns=["dx", "dy", "dz", "rx", "ry", "rz", "g", "program_status"], dtype=float)

i = 1
prev_state = None
skip = 0
threshold = 1e-4
keep_running = True
previous_row = None
first = True
TOTAL_EPISODE_STEPS = 250

while keep_running:
    if first:
        print("Srart the robot")
        first = False


    try:
        state = con.receive()
        if state is None:
            continue
        if state.output_int_register_0 == 100:
            skip += 1
        else:
            skip = 0

        if skip > 1000:
            break

        values = state.__dict__['actual_TCP_pose'].copy() + [state.output_int_register_7, state.output_int_register_0]
        current_row = pd.DataFrame([values], columns=df.columns)

        if previous_row is not None:
            change = np.abs(current_row.values - previous_row.values).max()
            if change <= threshold:
                continue  
        
        df = pd.concat([df, current_row], ignore_index=True)
        previous_row = current_row

    except KeyboardInterrupt:
        keep_running = False
    except rtde.RTDEException:
        con.disconnect()
        sys.exit()

con.send_pause()
con.disconnect()

df = df[df.iloc[:, -1] == 1]
df = df.iloc[:, :-1]

# Keep only l rows by removing in-between rows, keeping the first and last rows
def filter1(df):
    if len(df) <= TOTAL_EPISODE_STEPS:
        return df 
    indices = [0] + list(
        np.linspace(1, len(df) - 2, TOTAL_EPISODE_STEPS-1, dtype=int)
    ) + [len(df) - 1]
    return df.iloc[indices].reset_index(drop=True)

df = filter1(df)

df = interpolate_g_transitions(df, steps=10)

# update the absolute position to deltas
df_copy = df.copy()
zero = pd.DataFrame([[0]*len(df.columns)], columns=df.columns)
df_copy = pd.concat([zero, df_copy]).reset_index(drop=True)
df_copy = df_copy.iloc[:-1]
df = df - df_copy


df.to_csv(f"robot_data/episode{util.EPISODE}.csv", index=False)
print("Data recorded successfully")