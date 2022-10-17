import numpy as np
import xarray as xr
import warnings
import multiprocessing

from functools import reduce
from itertools import repeat


def get_time_window(ds, day, win_size):
    '''For a given `day` obtain a window of `win_size` around that day.'''
    plusminus = win_size // 2
    valid_days = (np.arange(day - plusminus - 1, day + plusminus) % 366) + 1
    window = ds.time.dt.dayofyear.isin(valid_days)
    return window


def get_quantiles(ds, day, win_size, q, q_period):
    '''Calculate quantiles for a given dataset `ds`.

    Quantiles are compute using the quantile thresholds `q` and the window
    size `win_size` of additional days around a given `day`.
    `q_period` defines the time slice which serves as a base to calculate the
    quantiles.
    '''
    window = get_time_window(ds.sel(time=q_period), day, win_size)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', r'All-NaN slice encountered')
        return ds.where(window, drop=True).quantile(q, dim='time', skipna=False)


def decluster(data, is_above_threshold, n_days=3):
    '''Remove individual extreme events which are shorter than ``n_days``.'''

    convolution = np.convolve(
        is_above_threshold,
        np.ones(n_days, dtype=float),
        'valid'
    ) >= n_days
    indices = np.flatnonzero(convolution)
    indices = [indices + i for i in range(n_days)]
    idx_heatwave = reduce(np.union1d, (indices))
    idx_all = np.arange(len(data))
    return np.where(np.isin(idx_all, idx_heatwave), data, np.nan)


def get_heatwaves(da, threshold, n_days=3):
    ''' Remove individual extreme events which are shorter than ``n_days``.

    This is an wrapper for ``xr.DataArray``.
    '''

    is_hot = da.groupby('time.dayofyear') > threshold
    hot_days_only = da.where(is_hot)
    return xr.apply_ufunc(
        decluster,
        hot_days_only,
        is_hot,
        kwargs={'n_days': n_days},
        input_core_dims=[['time'], ['time']],
        output_core_dims=[['time']],
        vectorize=True
    )


def Md(da, quantile=0.90, win_size=31, n_days=3, ref_period=slice('1981', '2010')):
    '''Calculate the daily magnitudes :math:`M_d`.

    Russo et al. (2015) [1] define the daily magnitudes as:

    .. math::
      M_d(T_d) = \\begin{cases}
        \\frac{T_d - T_{ref, 25p}}{T_{ref, 75p} - T_{ref, 25p}}, \\qquad \\text{ if } T_d > T_{ref, 25p} \\
        0 \\qquad \\text{ if } T_d \\leq T_{ref, 25p},
      \end{cases} 
    
    with :math:`T_d` being the maximum daily temperature on day :math:`d` of the heatwave,
    :math:`T_{ref, 25p}` and :math:`T_{ref, 75p}` are the 25th and 75th percentile values, respectively, of the
    annual temperature maxima over a reference period (e.g. 30 years from 1981-2010).

    Parameters
    ----------

    da : xr.DataArray
        DataArray containing (daily) maximum temperature.
    quantile : float
        Quantile to define heatwave threshold (default is 0.90).
    win_size : int
        Window size around a given date to define quantiles (default is 31).
    n_days : int
        Minimum number of consecutive days to be considered a heatwave
        (default is 3).
    ref_period : slice
        Reference period which serves as a baseline for the HWMId calculation.
        (the default is slice('1981', '2010')).

    References
    ----------
    [1]: Simone Russo et al 2015 Environ. Res. Lett. 10 124003
    [2]: Simone Russo et al 2014 J. Geophys. Res. 119 D022098

    '''
    T30 = da.sel(time=ref_period).groupby('time.year').max()
    T30y = T30.quantile([0.25, 0.75], dim='year')
    T30y75p = T30y.sel(quantile=0.75)
    T30y25p = T30y.sel(quantile=0.25)

    # For better performance, use parallel computing
    pool = multiprocessing.Pool()
    result = pool.starmap(
        get_quantiles,
        zip(
            repeat(da),
            range(1, 367),
            repeat(win_size),
            repeat(quantile),
            repeat(ref_period)
        )
    )
    threshold = xr.concat(result, dim='dayofyear')
    threshold = threshold.assign_coords({'dayofyear' : range(1, 367)})

    Td = get_heatwaves(da, threshold=threshold, n_days=n_days)

    Md = (Td - T30y25p) / (T30y75p - T30y25p)
    return Md.where(Td > T30y25p, 0)
