# %%
import numpy as np
import pandas as pd
import datetime
import pathlib
import argparse
import plotly.graph_objects as go
import plotly.subplots
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt

import datajoint as dj
import numpy as np
dj.config["database.user"] = "vplattner"
dj.config["database.password"] = "vplattner-aeon"
dj.conn()
from aeon.dj_pipeline import acquisition, analysis

dj.list_schemas()
# %%
subject_keys = acquisition.Experiment.Subject.fetch('KEY')

subj_names, sess_starts, rate_timestamps, rate_diffs = (analysis.SessionRewardRate & subject_keys).fetch(
    'subject',
    'session_start',
    'pellet_rate_timestamps',
    'patch2_patch1_rate_diff')


session_duration = (acquisition.SessionEnd & subject_keys).fetch("session_duration")

# %%

plt.plot(session_duration)
plt.show()

plt.plot(rate_diffs[2])
plt.show()


acquisition.FoodPatchEvent & subject_keys

(acquisition.FoodPatchWheel & subject_keys).fetch("timestamps")


sk = acquisition.FoodPatchWheel.fetch('KEY')

(acquisition.FoodPatchWheel & sk).fetch("timestamps")



acquisition.FoodPatchWheel & sk



acquisition.Experiment & subject_keys

analysis.SessionSummary.head