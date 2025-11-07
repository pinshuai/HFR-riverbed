#!/usr/bin/env python

import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta
import seaborn as sns
from sklearn.metrics import mean_squared_error


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

def closest_node(node, nodes):
    nodes = np.asarray(nodes)
    dist_2 = np.sum((nodes - node)**2, axis=1)
    return np.argmin(dist_2)

def printname(name):
    print(name)

def batch_time_to_delta(origin, x, time_format):
    y = []
    for ix in x:
        temp_y = abs(datetime.strptime(
            ix, time_format) - origin).total_seconds()
        y.append(temp_y)
    y = np.asarray(y)
    return(y)

def batch_delta_to_time(origin, x, time_format, delta_format):
    """
    convert from 
    """
    y = []
    for ix in x:
        if delta_format == "hours":
            temp_y = origin + timedelta(hours=ix)
        elif delta_format == "days":
            temp_y = origin + timedelta(days=ix)
        elif delta_format == "minutes":
            temp_y = origin + timedelta(minutes=ix)
        elif delta_format == "weeks":
            temp_y = origin + timedelta(weeks=ix)
        elif delta_format == "seconds":
            temp_y = origin + timedelta(seconds=ix)
        elif delta_format == "microseconds":
            temp_y = origin + timedelta(microseconds=ix)
        elif delta_format == "milliseconds":
            temp_y = origin + timedelta(milliseconds=ix)
        else:
            print("Sorry, this naive program only solve single time unit")
        y.append(temp_y.strftime(time_format))
    y = np.asarray(y)
    return(y)
    
def print_structure(name, obj):
    '''
    view the tree structure of hdf5 file
    
    example: input_h5.visititems(print_structure)
    '''
    print(name)
    
def lin_regression(x, y):
    ''' add linear regression line
        calculate R^2 (coefficient of determination)
    '''
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r_sq = r_value**2
    y_fit = intercept + slope * x
    
    return r_sq, y_fit

def regplot_R2(varX, varY, df):
    """
    plot regression plot with R2 on it.
    
    Auguments: 
    varX: colname in df for x variable
    varY: colname in df for y variable
    """
    
    ax = sns.regplot(x = df[varX], y = df[varY])
    
    r_sq, y_fit = lin_regression(df[varX].values, df[varY].values)

    ax.text(0.05, 0.95, 'R\u00b2 = {0:.2f}'.format(r_sq), fontweight= 'bold',
         fontsize = 12, color = 'k', transform = ax.transAxes)
    
    return ax

def regplot_r(varX, varY, df):
    """
    plot regression plot with Pearson's r on it.
    
    Auguments: 
    varX: colname in df for x variable
    varY: colname in df for y variable
    """
    
    ax = sns.regplot(x = df[varX], y = df[varY])
    pr, _ = stats.pearsonr(df[varX].values, df[varY].values)

    ax.text(0.05, 0.95, 'r = {0:.2f}'.format(pr), fontweight= 'bold',
         fontsize = 12, color = 'k', transform = ax.transAxes)
    
    return ax

def forward_selected(data, response):
    """Linear model designed by forward selection.

    Parameters:
    -----------
    data : pandas DataFrame with all possible predictors and response

    response: string, name of response column in data

    Returns:
    --------
    model: an "optimal" fitted statsmodels linear model
           with an intercept
           selected by forward selection
           evaluated by adjusted R-squared
    """
    remaining = set(data.columns)
    remaining.remove(response)
    selected = []
    current_score, best_new_score = 0.0, 0.0
    while remaining and current_score == best_new_score:
        scores_with_candidates = []
        for candidate in remaining:
            formula = "{} ~ {} + 1".format(response,
                                           ' + '.join(selected + [candidate]))
            score = smf.ols(formula, data).fit().rsquared_adj
            scores_with_candidates.append((score, candidate))
        scores_with_candidates.sort()
        best_new_score, best_candidate = scores_with_candidates.pop()
        if current_score < best_new_score:
            print(best_candidate, '%.2f'%best_new_score, '%.3f'% (best_new_score-current_score))
            remaining.remove(best_candidate)
            selected.append(best_candidate)
            current_score = best_new_score
    formula = "{} ~ {} + 1".format(response,
                                   ' + '.join(selected))
    model = smf.ols(formula, data).fit()
    return model
    
def align_yaxis(ax1, v1, ax2, v2):
    """adjust ax2 y-limit so that y2 in ax2 is aligned to y1 in ax1"""
    _, y1 = ax1.transData.transform((0, v1))
    _, y2 = ax2.transData.transform((0, v2))
    inv = ax2.transData.inverted()
    _, dy = inv.transform((0, 0)) - inv.transform((0, y1-y2))
    miny, maxy = ax2.get_ylim()
    ax2.set_ylim(miny+dy, maxy+dy)
    
def decimal_RGB(colors):
    """
    convert RGB from [0,256] to [0,1]
    """

    colors = [j/250 for i in colors for j in i] #convert rgb 0~250 to 0~1; this results in list
    colors = list(zip(*[iter(colors)]*3)) # convert list back to tuples
    
    return colors

def insertNA(df, dt_col):
    '''
    Automatically insert NAs for missing data. 
    Arguments:
      - df. A dataframe contains the missing data.
      - dt_col. Column name in the df which contains time series. 
    '''
    df[dt_col] = pd.to_datetime(df[dt_col])
    ## remove duplicates in the datetime index
#     df = df[~df[dt_col].duplicated()]
    df.drop_duplicates(subset=dt_col, inplace=True)
    df.sort_values(by = dt_col, inplace = True)
    ## create a new index
    start_time = df[dt_col].iloc[0]
    end_time = df[dt_col].iloc[-1]
    ## get the highest frequency in sec
    freq_list = df[dt_col].diff().dt.seconds.value_counts()
    
    # the first freq with the most samples on the list may not be the smallest freq
    if freq_list.index[0] == freq_list.index.min():
        freq = freq_list.index[0]
    else:
        freq = freq_list.index.min()
#     print(freq)
    new_index = pd.date_range(start_time, end_time, freq=pd.DateOffset(seconds = freq), 
                              name = dt_col)
    ## reindex and reset index
    df = df.set_index(dt_col).reindex(new_index).reset_index()
    
    return df
    
def cellID2xyz(icellID, nx, ny):
    '''
    Get cell index from cell ID.
    Arguments:
    - icellID. cell ID
    - nx, ny. the dimension of model
    '''
    
    iz = icellID//(nx*ny)
    iy = (icellID - iz*nx*ny)//nx
    ix = icellID - iz*nx*ny - iy*nx -1 

    ind = np.asarray((ix, iy, iz))
    
    return ind
    
    
def xyz2cellID(iarray, nx, ny):
    '''
    Get cell Id from cell index.
    Arguments:
    - iarray. cell index in an array
    - nx, ny. model dimension
    '''
    
    cellID = iarray[2]*nx*ny + iarray[1]*nx + iarray[0] +1
    return cellID

def mann_whitney_test(data1, data2, alpha=0.05):
    """
    perform a Mann-Whitney test, and return statistics and p-value
    Arguments:
        x: data1
        y: data2
        alpha: significance factor, default 0.05
    """
    stat, p = stats.mannwhitneyu(data1, data2)
    print('Statistics=%.3f, p=%.3f' % (stat, p))
    if p > alpha:
        print('Same distributions (fail to reject H0)')
    else:
        print('Different distributions (reject H0)')
        
    return stat, p

def get_rmse(obs_df, simu_df):
    """
    calculate RMSE from obs and simu data.
    Arguments:
        obs_df: a time series containing observation data
        simu_df: a time series containing simulation data
    """
    if obs_df.index.dtype != 'datetime64[ns]' or simu_df.index.dtype != 'datetime64[ns]':
        print('Make sure datetime index is in the series!')
        return None
    
    df_merge = pd.concat([obs_df, simu_df], axis = 1, join="inner")
    
    if any(df_merge.dtypes == object):
        df_merge = df_merge.apply(pd.to_numeric, errors='coerce')
    
    df_merge.dropna(inplace=True)
    
    if df_merge.shape[0] > 10:
        rmse = mean_squared_error(df_merge.iloc[:, 0], df_merge.iloc[:, 1])**0.5
        return rmse
    else:
        print('Overlapping samples are fewer than 10. No RMSE is calculated!')
        return None 