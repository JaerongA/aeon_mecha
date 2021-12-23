

#%% Setup
import sys
import os
from os.path import expanduser
sys.path.append(expanduser('~/repos/aeon_mecha_de'))

import numpy as np
import pandas as pd
import aeon.analyze.patches as patches
import os 
import aeon.preprocess.api as api
import matplotlib.pyplot as plt
import aeon.util.helpers as helpers
import aeon.util.plotting as plotting

# As long as you have cloned the aeon_mecha_de folder into 
# repos in your home filter

# This path is only true if you are on pop.erlichlab.org
env = os.environ
dataroot = env.get('aeon_dataroot', '/var/www/html/delab/data/arena0.1/socialexperiment0/')
figpath = env.get('aeon_figpath','/var/www/html/delab/figures/')
export_format = env.get('aeon_dataformat','parquet')
fig_format = env.get('aeon_figformat','png')


#%% Load session data.
def loadSessions():
    sessdf = api.sessiondata(dataroot)
    sessdf = api.sessionduration(sessdf)                                     # compute session duration
    sessdf = sessdf[~sessdf.id.str.contains('test')]
    sessdf = sessdf[~sessdf.id.str.contains('jeff')]
    sessdf = sessdf[~sessdf.id.str.contains('OAA')]
    sessdf = sessdf[~sessdf.id.str.contains('rew')]
    sessdf = sessdf[~sessdf.id.str.contains('Animal')]

    sessdf.reset_index(inplace=True, drop=True)

    df = sessdf.copy()
    helpers.merge(df)
    helpers.merge(df,first=[15])
    helpers.merge(df,first=[32,35, 44, 46, 49], merge_id=True)
    helpers.merge(df, first=[42,])

    #%% Fix bad ids.

    df.loc[10,'id'] = 'BAA-1100705'
    df.loc[19,'id'] = 'BAA-1100704;BAA-1100706'
    df.loc[22,'id'] = 'BAA-1100705;BAA-1100706'
    df.loc[25,'id'] = 'BAA-1100704;BAA-1100705'
    df.loc[30,'id'] = 'BAA-1100704;BAA-1100705'



    #%%
    helpers.markSessionEnded(df)
    return df

#%% 
def makeWheelPlots():
    try:
        fileformat = sys.argv[2]
    except IndexError:
        fileformat = 'png'

    print(f'Saving files as {fileformat} in {figpath}')

    session_list = df.itertuples()
    print('Data loaded and merged.')
    #%% save all the patch figures.

    for session in session_list:
        try:
            meta = {'session':session}
            filename = plotting.plotFileName(os.path.join(figpath,'patch_flip_full',fileformat), 'patch', meta, type=fileformat)
            if not os.path.exists(filename):
                data = helpers.getWheelData(dataroot, session.start, session.end)
                data['meta'] = meta
                data['filename'] = filename
                data['change_in_red'] = True
                # data['total_dur'] = 60 # show 70 minutes around change.
                plotting.plotWheelData(**data)

                print(f'{filename} saved.')
            else:
                print(f'{filename} exists. Skipping.')
        except IndexError as e:
            print(f'Failed to save {filename}. {e}')

def exportDataToParquet():
    pass
# %%

if __name__ == "__main__":
    if len(sys.argv) == 0:
        print("""
        This function has become a 
        dataroot = env.get('aeon_dataroot', '/var/www/html/delab/data/arena0.1/socialexperiment0/')
        figpath = env.get('aeon_figpath','/var/www/html/delab/figures/')
        export_format = env.get('aeon_dataformat','parquet')
        fig_format = env.get('aeon_figformat','png')

        """)
    func = sys.argv[0]
    df = loadSession()
    try:
    eval(func)(*args)