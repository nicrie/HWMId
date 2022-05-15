import xarray as xr
import matplotlib.pyplot as plt

from hwmid import HWMId

# Load temperature data for London
t2m_max = xr.open_dataarray('data/london_t2m_max.nc')

# Calculate heatwave magnitude index daily
hwmid = HWMId(
    t2m_max,
    quantile=.9,
    n_days=3,
    win_size=31,
    ref_period=slice('1950', '1979')
)

magnitude = hwmid.groupby('time.year').sum()
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
hwmid.plot(ax=ax, marker='x', ls='', color='darkred')
ax.set_xlabel('Year')
ax.set_ylabel('HWMId')
ax.set_title('Heatwave magnitude index @London, UK', loc='left', weight='bold')
ax.set_title('', loc='center')
plt.tight_layout()
plt.savefig('figs/daily-hwmid.png', dpi=120)

#%%


fig = plt.figure(figsize=(12, 4))
ax = fig.add_subplot(111)
ax.bar(magnitude.year, magnitude.values, color='darkred')
ax.set_xlabel('Year')
ax.set_ylabel('HWMId')
ax.set_title('Yearly heatwave magnitude index @London, UK', loc='left', weight='bold')
ax.set_title('', loc='center')
plt.tight_layout()
plt.savefig('figs/yearly-hwmid.png', dpi=120)
