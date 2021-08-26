
import sys

import argparse
import numpy as np
import pandas as pd
import datetime
import scipy.interpolate
import time

import flask

import plotly.graph_objects as go
import plotly.subplots
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL, MATCH
import dash.exceptions

sys.path.append("../..")

import aeon.preprocess.api
import aeon.preprocess.utils
import aeon.signalProcessing.utils
import aeon.preprocess.utils
import aeon.plotting.plot_functions

def main(argv):

    parser = argparse.ArgumentParser()
    parser.add_argument("--local", help="run the flask server only locally", action="store_true")
    parser.add_argument("--debug", help="start GUI with debug functionality", action="store_true")
    parser.add_argument("--root", help="Root path for data access", default="/ceph/aeon/test2/experiment0.1")
    parser.add_argument("--patches_coordinates", help="coordinates of patches", default="585,605,814,834;608,628,250,270")
    parser.add_argument("--nest_coordinates", help="coordinates of nest", default="170,260,450,540")
    parser.add_argument("--patchesToPlot", help="Names of patches to plot", default="Patch1,Patch2")
    parser.add_argument("--sample_rate_for_trajectory0", help="Initial value for the sample rate for the trajectory", default=0.5, type=float)
    parser.add_argument("--reward_rate_time_resolution", help="Time resolution to compute the moving average (sec)", default=0.1, type=float)
    parser.add_argument("--reward_rate_ma_win_length", help="Reward rate moving average window length", default="60s")
    parser.add_argument("--pellet_event_name", help="Pellet event name to display", default="TriggerPellet")
    parser.add_argument("--xlabel_trajectory", help="xlabel for trajectory plot", default="x (pixels)")
    parser.add_argument("--ylabel_trajectory", help="ylabel for trajectory plot", default="y (pixels)")
    parser.add_argument("--ylabel_cumTimePerActivity", help="ylabel", default="Proportion of Time")
    parser.add_argument("--xlabel_travelledDistance", help="xlabel for travelledDistance plot", default="Time (sec)")
    parser.add_argument("--ylabel_travelledDistance", help="ylabel for travelledDistance plot", default="Travelled Distance (cm)")
    parser.add_argument("--xlabel_rewardRate", help="xlabel for reward rate", default="Time (sec)")
    parser.add_argument("--ylabel_rewardRate", help="ylabe for reward ratel", default="Reward Rate")
    parser.add_argument("--ylim_cumTimePerActivity", help="ylim cummulative time per activity plot", default="[0,1]")
    parser.add_argument("--travelled_distance_trace_color", help="travelled distance trace color", default="blue")
    parser.add_argument("--reward_rate_trace_color", help="reward rate trace color", default="blue")
    parser.add_argument("--pellet_color", help="pellet line color", default="red")
    parser.add_argument("--pellet_line_style", help="pellet line style", default="solid")
    parser.add_argument("--trajectories_width", help="width of the trajectories plot", type=int, default=1000)
    parser.add_argument("--trajectories_height", help="height of the trajectories plot", type=int, default=1000)
    parser.add_argument("--trajectories_colorscale", help="colorscale for trajectories", default="Rainbow")
    parser.add_argument("--trajectories_opacity", help="opacity for trajectories", default=0.3, type=float)

    args = parser.parse_args()

    local = args.local
    root = args.root
    patches_coordinates_matrix = np.matrix(args.patches_coordinates)
    nest_coordinates_matrix = np.matrix(args.nest_coordinates)
    patches_to_plot = args.patchesToPlot.split(",")
    sample_rate_for_trajectory0 = args.sample_rate_for_trajectory0
    reward_rate_time_resolution = args.reward_rate_time_resolution
    reward_rate_ma_win_length = args.reward_rate_ma_win_length
    pellet_event_name = args.pellet_event_name
    xlabel_trajectory = args.xlabel_trajectory
    ylabel_trajectory = args.ylabel_trajectory
    ylabel_cumTimePerActivity = args.ylabel_cumTimePerActivity
    xlabel_travelledDistance = args.xlabel_travelledDistance
    ylabel_travelledDistance = args.ylabel_travelledDistance
    xlabel_rewardRate = args.xlabel_rewardRate
    ylabel_rewardRate = args.ylabel_rewardRate
    ylim_cumTimePerActivity = [float(str) for str in args.ylim_cumTimePerActivity[1:-1].split(",")]
    travelled_distance_trace_color = args.travelled_distance_trace_color
    reward_rate_trace_color = args.reward_rate_trace_color
    pellet_color = args.pellet_color
    pellet_line_style = args.pellet_line_style
    trajectories_height = args.trajectories_height
    trajectories_width = args.trajectories_width
    trajectories_colorscale = args.trajectories_colorscale
    trajectories_opacity = args.trajectories_opacity

    metadata = aeon.preprocess.api.sessiondata(root)
    metadata = metadata[metadata.id.str.startswith('BAA')]
    metadata = aeon.preprocess.utils.getPairedEvents(metadata=metadata)
    metadata = aeon.preprocess.api.sessionduration(metadata)

    mouse_names = metadata["id"].unique()
    options_mouse_names = [{"label": mouse_name, "value": mouse_name} for mouse_name in mouse_names]
    sessions_start_times = metadata[metadata["id"]==mouse_names[0]].index
    options_sessions_start_times = [{"label": session_start_time, "value": session_start_time} for session_start_time in sessions_start_times]
    def serve_layout():
        aDiv = html.Div(children=[
            html.H1(children="Behavioral Analysis Dashboard"),
            html.Hr(),
            html.H4(children="Mouse Name"),
            dcc.Dropdown(
                id="mouseNameDropDown",
                options=options_mouse_names,
                value=mouse_names[0],
            ),
            html.H4(children="Session Start Time"),
            dcc.Dropdown(
                id="sessionStartTimeDropdown",
                options=options_sessions_start_times,
                value=sessions_start_times[0],
            ),
            html.H4(children="Plotting Time (sec)"),
            dcc.RangeSlider(
                id="plotTimeRangeSlider",
            ),
            html.H4(children="Sample Rate for Trajectory Plot"),
            dcc.Input(
                id="sRateForTrajectoryPlot",
                type="number",
                value=sample_rate_for_trajectory0,
            ),
            html.Label(id="nTrajectoryPointsToPlot"),
            html.Hr(),
            html.Button(children="Plot", id="plotButton", n_clicks=0),
            html.Div(
                id="plotsContainer",
                children=[
                    html.H4(children="Trajectory"),
                    dcc.Graph(
                        id="trajectoryGraph",
                    ),
                    html.H4(children="Activities"),
                    dcc.Graph(
                        id="activitiesGraph",
                    ),
                    html.H4(children="Distance Travelled"),
                    dcc.Graph(
                        id="travelledDistanceGraph",
                    ),
                    html.H4(children="Reward Rate"),
                    dcc.Graph(
                        id="rewardRateGraph",
                    )
                ], hidden=True)
        ])
        return aDiv

    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
    app.layout = serve_layout()

    @app.callback([Output('sessionStartTimeDropdown', 'options'),
                   Output('sessionStartTimeDropdown', 'value'),],
                  Input('mouseNameDropDown', 'value'))
    def get_sessions_start_times(mouseNameDropDown_value):
        sessions_start_times = metadata[metadata["id"]==mouseNameDropDown_value].index
        options_sessions_start_times = [{"label": session_start_time, "value": session_start_time} for session_start_time in sessions_start_times]
        return options_sessions_start_times, sessions_start_times[0]

    @app.callback([Output('nTrajectoryPointsToPlot', 'children'),],
                  Input('sRateForTrajectoryPlot', 'value'),
                  Input('plotTimeRangeSlider', 'value'),
                 )
    def get_num_trajectory_points_to_plot_label(sRateForTrajectoryPlot_value,
                                                plotTimeRangeSlider_value):
        if sRateForTrajectoryPlot_value is None or plotTimeRangeSlider_value is None:
            raise dash.exceptions.PreventUpdate
        num_trajectory_points_to_plot = int((plotTimeRangeSlider_value[1]-plotTimeRangeSlider_value[0])*sRateForTrajectoryPlot_value)
        answer = ["Number of trajectory points to plot: {:d}".format(num_trajectory_points_to_plot)]
        return answer

    @app.callback([Output('plotTimeRangeSlider', 'min'),
                   Output('plotTimeRangeSlider', 'max'),
                   Output('plotTimeRangeSlider', 'marks'),
                   Output('plotTimeRangeSlider', 'value'),
                  ],
                  Input('sessionStartTimeDropdown', 'value'))
    def get_plotTimeRangeSlider_options(sessionStartTimeDropdown_value):
        # print("get_plotTimeRangeSlider_options called")
        # print("type(sessionStartTimeDropdown_value)")
        # print(type(sessionStartTimeDropdown_value))
        # print("sessionStartTimeDropdown_value")
        # print(sessionStartTimeDropdown_value)
        sessions_duration_sec = metadata[metadata.index==pd.to_datetime(sessionStartTimeDropdown_value)].duration.item().total_seconds()
        # print("sessions_duration_sec")
        # print(sessions_duration_sec)
        # print("about to print 1")
        slider_min = 0
        # print("about to print 2")
        slider_max = int(sessions_duration_sec)
        # print("about to print 3")
        slider_marks = dict(zip(range(0, slider_max, 600), [str(aNum) for aNum in range(0, slider_max, 600)]))
        # print("about to print 4")
        slider_value=[0,slider_max]
        # print("about to print 5")
        # print("min={}, max={}, marks={}, value={}".format(slider_min, slider_max, slider_marks, slider_value))
        return slider_min, slider_max, slider_marks, slider_value

    @app.callback([Output('trajectoryGraph', 'figure'),
                   Output('activitiesGraph', 'figure'),
                   Output('travelledDistanceGraph', 'figure'),
                   Output('rewardRateGraph', 'figure'),
                   Output('plotsContainer', 'hidden'),
                   Output('plotButton', 'children'),
                  ],
                  [Input('plotButton', 'n_clicks')],
                  [State('mouseNameDropDown', 'value'),
                   State('sessionStartTimeDropdown', 'value'),
                   State('plotTimeRangeSlider', 'value'),
                   State('sRateForTrajectoryPlot', 'value')],
                  )
    def update_plots(plotButton_nClicks,
                     mouseNameDropDown_value,
                     sessionStartTimeDropdown_value,
                     plotTimeRangeSlider_value,
                     sRateForTrajectoryPlot_value):
        if plotButton_nClicks == 0:
            print("update prevented ({:s})".format(flask.request.remote_addr))
            raise dash.exceptions.PreventUpdate
        print("update_plots called ({:s})".format(flask.request.remote_addr))
        patches_coordinates = pd.DataFrame(data=patches_coordinates_matrix,
                                           columns=["lower_x", "higher_x",
                                                    "lower_y", "higher_y"])
        nest_coordinates = pd.DataFrame(data=nest_coordinates_matrix,
                                        columns=["lower_x", "higher_x",
                                                 "lower_y", "higher_y"])

        t0_relative = plotTimeRangeSlider_value[0]
        tf_relative = plotTimeRangeSlider_value[1]

        session_start = pd.Timestamp(sessionStartTimeDropdown_value)
        t0_absolute = session_start + datetime.timedelta(seconds=t0_relative)
        tf_absolute = session_start + datetime.timedelta(seconds=tf_relative)
        position = aeon.preprocess.api.positiondata(root, start=t0_absolute, end=tf_absolute)

        x = position["x"].to_numpy()
        y = position["y"].to_numpy()
        time_stamps = (position.index-session_start).total_seconds().to_numpy()

        # trajectory figure
        fig_trajectory = go.Figure()
        patches_traces = aeon.plotting.plot_functions.get_patches_traces(patches_coordinates=patches_coordinates)
        for patch_trace in patches_traces:
            fig_trajectory.add_trace(patch_trace)
        nest_trace = aeon.plotting.plot_functions.get_patches_traces(patches_coordinates=nest_coordinates)[0]
        fig_trajectory.add_trace(nest_trace)
        trajectory_trace = aeon.plotting.plot_functions.get_trayectory_trace(x=x, y=y, time_stamps=time_stamps, sample_rate=sRateForTrajectoryPlot_value, colorscale=trajectories_colorscale, opacity=trajectories_opacity)
        fig_trajectory.add_trace(trajectory_trace)
        fig_trajectory.update_layout(xaxis_title=xlabel_trajectory, yaxis_title=ylabel_trajectory, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=trajectories_height, width=trajectories_width)

        # activity figure
        positions_labels = aeon.preprocess.utils.get_positions_labels(
            x=x, y=y,
            patches_coordinates=patches_coordinates,
            nest_coordinates=nest_coordinates)

        fig_cumTimePerActivity = go.Figure()
        cumTimePerActivity_trace = aeon.plotting.plot_functions.get_cumTimePerActivity_barplot_trace(
            positions_labels=positions_labels,
        )
        fig_cumTimePerActivity.add_trace(cumTimePerActivity_trace)
        fig_cumTimePerActivity.update_layout(yaxis_title=ylabel_cumTimePerActivity)
        fig_cumTimePerActivity.update_yaxes(range=ylim_cumTimePerActivity)

        # travelled distance figure
        travelled_distance = {}
        travelled_seconds = {}
        pellets_seconds = {}
        max_travelled_distance = -np.inf
        for patch_to_plot in patches_to_plot:
            wheel_encoder_vals = aeon.preprocess.api.encoderdata(root, patch_to_plot, start=t0_absolute, end=tf_absolute)
            travelled_distance[patch_to_plot] = aeon.preprocess.api.distancetravelled(wheel_encoder_vals.angle)
            if travelled_distance[patch_to_plot][-1]>max_travelled_distance:
                max_travelled_distance = travelled_distance[patch_to_plot][-1]
            travelled_seconds[patch_to_plot] = (travelled_distance[patch_to_plot].index-session_start).total_seconds()
            pellet_vals = aeon.preprocess.api.pelletdata(root, patch_to_plot, start=t0_absolute, end=tf_absolute)
            pellets_times = pellet_vals[pellet_vals.event == "{:s}".format(pellet_event_name)].index
            pellets_seconds[patch_to_plot] = (pellets_times-session_start).total_seconds()

        travelled_distance_sample_rate = 10.0
        fig_travelledDistance = go.Figure()
        fig_travelledDistance = plotly.subplots.make_subplots(rows=1, cols=len(patches_to_plot), subplot_titles=(patches_to_plot))
        for i, patch_to_plot in enumerate(patches_to_plot):
            trace = aeon.plotting.plot_functions.get_travelled_distance_trace(travelled_seconds=travelled_seconds[patch_to_plot], travelled_distance=travelled_distance[patch_to_plot], color=travelled_distance_trace_color, sample_rate=travelled_distance_sample_rate, showlegend=False)
            fig_travelledDistance.add_trace(trace, row=1, col=i+1)
            trace = aeon.plotting.plot_functions.get_pellets_trace(pellets_seconds=pellets_seconds[patch_to_plot], marker_color=pellet_color)
            fig_travelledDistance.add_trace(trace, row=1, col=i+1)
            if i == 0:
                fig_travelledDistance.update_yaxes(title_text=ylabel_travelledDistance, range=(0, max_travelled_distance), row=1, col=i+1)
            else:
                fig_travelledDistance.update_yaxes(range=(-20, max_travelled_distance), row=1, col=i+1)
            fig_travelledDistance.update_xaxes(title_text=xlabel_travelledDistance, row=1, col=i+1)
        print("Done with fig_travelledDistance")

        # reward rate figure
        pellets_seconds = {}
        reward_rate = {}
        max_reward_rate = -np.inf
        for patch_to_plot in patches_to_plot:
            pellet_vals = aeon.preprocess.api.pelletdata(root, patch_to_plot, start=t0_absolute, end=tf_absolute)
            pellets_times = pellet_vals[pellet_vals.event == "{:s}".format(pellet_event_name)].index
            pellets_seconds[patch_to_plot] = (pellets_times-session_start).total_seconds()
            pellets_events = pd.DataFrame(index=pd.TimedeltaIndex(data=pellets_seconds[patch_to_plot], unit="s"), data=np.ones(len(pellets_seconds[patch_to_plot])), columns=['count'])
            boundary_df = pd.DataFrame(index=pd.TimedeltaIndex(data=[t0_relative, tf_relative], unit="s"), data=dict(count=[0.0, 0.0]), columns=['count'])
            pellets_events = pellets_events.append(other=boundary_df)
            pellets_events.sort_index(inplace=True)
            # pellets_seconds[patch_to_plot] = 
            pellets_events_binned = pellets_events.resample("{:f}S".format(reward_rate_time_resolution)).sum()
            pellets_events_ma = pellets_events_binned.rolling(window=reward_rate_ma_win_length, center=True).mean()
            reward_rate[patch_to_plot] = pellets_events_ma
            patch_max_reward_rate = reward_rate[patch_to_plot].max().item()
            if patch_max_reward_rate > max_reward_rate:
                max_reward_rate = patch_max_reward_rate

        fig_rewardRate = go.Figure()
        fig_rewardRate = plotly.subplots.make_subplots(rows=1, cols=len(patches_to_plot),
                                                       subplot_titles=(patches_to_plot))
        for i, patch_to_plot in enumerate(patches_to_plot):
            trace = go.Scatter(x=reward_rate[patch_to_plot].index.total_seconds(), y=reward_rate[patch_to_plot].iloc[:, 0], line=dict(color=reward_rate_trace_color), showlegend=False)
            fig_rewardRate.add_trace(trace, row=1, col=i+1)
            trace = aeon.plotting.plot_functions.get_pellets_trace(pellets_seconds=pellets_seconds[patch_to_plot], marker_color=pellet_color)
            fig_rewardRate.add_trace(trace, row=1, col=i+1)
            if i == 0:
                fig_rewardRate.update_yaxes(title_text=ylabel_rewardRate, range=(0, max_reward_rate), row=1, col=i+1)
            else:
                fig_rewardRate.update_yaxes(range=(0, max_reward_rate), row=1, col=i+1)
            fig_rewardRate.update_xaxes(title_text=xlabel_rewardRate, row=1, col=i+1)

        plotsContainer_hidden = False
        plotButton_children = ["Update"]

        return fig_trajectory, fig_cumTimePerActivity, fig_travelledDistance, fig_rewardRate, plotsContainer_hidden, plotButton_children
#         return fig_trajectory, fig_cumTimePerActivity, fig_travelledDistance, plotsContainer_hidden, plotButton_children
#         return fig_trajectory, fig_cumTimePerActivity, plotsContainer_hidden, plotButton_children

    if(args.local):
        app.run_server(debug=args.debug)
    else:
        app.run_server(debug=args.debug, host="0.0.0.0")

if __name__=="__main__":
    main(sys.argv)
