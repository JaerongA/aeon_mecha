import numpy as np
import pandas as pd
import datetime
import pathlib
import argparse
import plotly.graph_objects as go
import plotly.subplots
import plotly.express as px
import plotly.io as pio

import datajoint as dj
import numpy as np
dj.config["database.user"] = "vplattner"
dj.config["database.password"] = "vplattner-aeon"
dj.conn()

from aeon.dj_pipeline import acquisition, analysis

# import webbrowser
# urL="http://www.google.com"
# chrome_path=os.path.join( "C:","Program Files (x86)","Google","Chrome","Application","chrome.exe")
# webbrowser.register("chrome", None,webbrowser.BackgroundBrowser(chrome_path))
# webbrowser.get("chrome").open_new_tab(urL)


#pio.renderers.default = "chrome"

def plot_reward_rate_differences(subject_keys, save_figure=True):
    """
    Plotting the reward rate differences between food patches (Patch 2 - Patch 1)
    for all sessions from all subjects specified in "subject_keys"
    Example usage:
    ```
    subject_keys = acquisition.Experiment.Subject.fetch('KEY')

    fig = plot_reward_rate_differences(subject_keys)
    ```
    """

    ### fetching data as separate variables
    subj_names, sess_starts, rate_timestamps, rate_diffs = (analysis.SessionRewardRate & subject_keys).fetch(
        'subject',
        'session_start',
        'pellet_rate_timestamps',
        'patch2_patch1_rate_diff')


    nSessions = len(sess_starts)
    longest_rateDiff = np.max([len(t) for t in rate_timestamps])

    max_session_idx = np.argmax([len(t) for t in rate_timestamps])
    max_session_elapsed_times = rate_timestamps[max_session_idx] - rate_timestamps[max_session_idx][0]
    x_labels = [t.total_seconds() / 60 for t in max_session_elapsed_times]

    y_labels = [f'{subj_name}_{sess_start.strftime("%m/%d/%Y")}' for subj_name, sess_start in
                zip(subj_names, sess_starts)]

    rateDiffs_matrix = np.full((nSessions, longest_rateDiff), np.nan)
    for row_index, rate_diff in enumerate(rate_diffs):
        rateDiffs_matrix[row_index, :len(rate_diff)] = rate_diff

    absZmax = np.nanmax(np.absolute(rateDiffs_matrix))
    fig = px.imshow(img=rateDiffs_matrix, x=x_labels, y=y_labels,
                    zmin=-absZmax, zmax=absZmax, aspect="auto",
                    color_continuous_scale='RdBu_r',
                    labels=dict(color="Reward Rate<br>Patch2-Patch1"))
    fig.update_layout(
        xaxis_title="Time (min)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    if save_figure:
        fig_filename_pattern = 'reward_rate_diffsPatch1MinusPatch2.{:s}'
        fig.write_image(fig_filename_pattern.format("png"))
        fig.write_html(fig_filename_pattern.format("html"))
    fig.show()


### recreating the figs


# # %%
# import matplotlib.pyplot as mplt
# import pandas as pd
#
# # %%
# mplt.plot(rate_diffs[1])
# mplt.show()
#
# # %%
# data = {'Unemployment_Rate': [6.1, 5.8, 5.7, 5.7, 5.8, 5.6, 5.5, 5.3, 5.2, 5.2],
#         'Stock_Index_Price': [1500, 1520, 1525, 1523, 1515, 1540, 1545, 1560, 1555, 1565]
#         }
#
# df = pd.DataFrame(data, columns=['Unemployment_Rate', 'Stock_Index_Price'])

# # %%
# ratediff_df = pd.DataFrame(rateDiffs_matrix)
#
# ratediff_df = ratediff_df.assign(subject = subj_names)
#
# list(ratediff_df)
#
# rateDiffs_matrix.shape
#
# ratediff_df.plot(x = "1", y = "subject", kind = "line")
# mplt.show()
#
# data = pd.DataFrame(subj_names, sess_starts, rate_timestamps, rate_diffs)
#
# len(subj_names)
#
# sess_starts[1].strftime("%A, %d %b %Y")
#
# rate_timestamps[1][2].strftime("'%d/%m/%y %I:%M %S %p'")
#
# for i in sess_starts
#     sess_starts[i].strftime("'%d/%m/%y %I:%M %S %p'")
#
# datetime.datetime.now()