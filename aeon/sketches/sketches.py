import datajoint as dj
import numpy as np
import pandas as pd
import plotly.graph_objects as go

dj.config["database.user"] = "vplattner"

dj.conn()
dj.list_schemas()

dj.config["display.limit"] = 15  # limit number of displayed rows
dj.config["display.width"] = 25  # limit number of displayed columns

_use_virtual_module = True

_db_prefix = "aeon_"

if _use_virtual_module:
    acquisition = dj.create_virtual_module("acquisition", _db_prefix + "acquisition")
    analysis = dj.create_virtual_module("analysis", _db_prefix + "analysis")
    lab = dj.create_virtual_module("lab", _db_prefix + "lab")
    subject = dj.create_virtual_module("subject", _db_prefix + "subject")
    tracking = dj.create_virtual_module("tracking", _db_prefix + "tracking")

else:
    dj.config.update(custom={**dj.config.get("custom", {}), "database.prefix": _db_prefix})
    from aeon.dj_pipeline import acquisition, analysis, lab, subject, tracking


def check_fetch_len(key, length=1):
    """
    Check that a key is of a certain length

    :param key: A key must be a list, query, or pandas DF (not a dict)
    :type key: list, QueryExpression, DataFrame
    :param length: Length to use to check key, defaults to 1
    :type length: int, optional
    :raises ValueError: Key is incorrect length
    """
    assert isinstance(key, (list, dj.expression.QueryExpression, pd.DataFrame))
    if not len(key) == length:
        raise ValueError(f"Key must be of length {length}")


def position_concat(session_key, acquisition, tracking, pixel_scale=0.00192):
    """
    Concatenate position data into a single pandas DataFrame

    :param session_key: a key for a single session
    :type session_key: [type]
    :param acquisition: DataJoint module
    :type acquisition: dj.Schema
    :param tracking: DataJoint module
    :type tracking: dj.Schema
    :param pixel_scale: convert pixels to mm, defaults to 0.00192
    :type pixel_scale: float, optional
    :return: A DataFrame representation of the table
    :rtype: pd.DataFrame
    """
    sess_key = (acquisition.Session() & session_key).fetch(as_dict=True)

    check_fetch_len(sess_key, 1)
    sess_key = sess_key[0]

    to_expand = [
        "timestamps",
        "position_x",
        "position_y",
        "position_z",
        "area",
        "speed",
    ]

    pos_arr = (tracking.SubjectPosition() & sess_key).fetch(
        *to_expand, order_by="time_slice_start"
    )

    for idx, field in enumerate(to_expand):
        col_data = pos_arr[idx]
        col_data = np.concatenate(col_data)
        if field != "timestamps":
            col_data *= pixel_scale
        sess_key[field] = col_data

    return pd.DataFrame(sess_key).set_index("timestamps")



acquisition.Session()

from dplython import select, DplyFrame, X, arrange, count, sift, head, summarize, group_by, tail, mutate
import pandas as pd

acquisition.SessionEnd()

frame = pd.DataFrame(acquisition.SessionEnd())
dpl_frame = DplyFrame(frame)
dpl_frame

dpl_frame >> select(X.subject) >> head(10)


tracking.SubjectPosition()

frame = pd.DataFrame(tracking.SubjectPosition())
dpl_frame = DplyFrame(frame)
dpl_frame >> select(X.speed) >> head(10)



analysis.SessionRewardRate & 'subject = "BAA-1099790"'