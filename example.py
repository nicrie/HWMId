import xarray as xr
import matplotlib.pyplot as plt

from hwmid import Md

# Load temperature data for London
t2m_max = xr.open_dataarray('data/london_t2m_max.nc')

# Calculate daily magnitudes Md
daily_magnitudes = Md(
    t2m_max,
    quantile=.9,
    n_days=3,
    win_size=31,
    ref_period=slice('1950', '1979')
)

# Compute heatwave magnitude by computing the sum over consecutive heatwave days
eps = 1e-5  # to represent zero
heatwave_magnitude = daily_magnitudes.groupby((daily_magnitudes < eps).cumsum('time')).cumsum()

# Compute the HWMId as the maximum heatwave magnitude per year
HWMId = heatwave_magnitude.groupby('time.year').max()

#%%
fig = plt.figure(figsize=(12, 4))
ax = fig.add_subplot(111)
t2m_max.plot(ax=ax, color='darkred')
ax.set_xlabel('Year')
ax.set_ylabel('Temperature (ºC)')
ax.set_title('Daily maximal temperature @London, UK', loc='left', weight='bold')
ax.set_title('', loc='center')
plt.tight_layout()
plt.savefig('figs/daily-max-temperature.png', dpi=120)
#%%

fig = plt.figure(figsize=(12, 4))
ax = fig.add_subplot(111)
daily_magnitudes.where(daily_magnitudes>0).plot(ax=ax, marker='x', ls='', color='darkred')
ax.set_xlabel('Year')
ax.set_ylabel('')
ax.set_title('Daily magnitudes Md @London, UK', loc='left', weight='bold')
ax.set_title('', loc='center')
plt.tight_layout()
plt.savefig('figs/daily-magnitudes.png', dpi=120)

#%%
fig = plt.figure(figsize=(12, 4))
ax = fig.add_subplot(111)
ax.plot(heatwave_magnitude.time, heatwave_magnitude.values, color='darkred')
ax.set_xlabel('Year')
ax.set_ylabel('')
ax.set_title('Heatwave magnitudes @London, UK', loc='left', weight='bold')
ax.set_title('', loc='center')
plt.tight_layout()
plt.savefig('figs/heatwave-magnitudes.png', dpi=120)

# %%
fig = plt.figure(figsize=(12, 4))
ax = fig.add_subplot(111)
ax.bar(HWMId.year, HWMId.values, color='darkred')
ax.set_xlabel('Year')
ax.set_ylabel('')
ax.set_title('Maximal yearly heat wave magniutde (HWMId) @London, UK', loc='left', weight='bold')
ax.set_title('', loc='center')
plt.tight_layout()
plt.savefig('figs/yearly-hwmid.png', dpi=120)
# %%
