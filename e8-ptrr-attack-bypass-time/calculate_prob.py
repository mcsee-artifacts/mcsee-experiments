import numpy as np
import matplotlib.pyplot as plt
import math

# Configure Matplotlib for LaTeX rendering and specific font
plt.rcParams['text.usetex'] = True
plt.rcParams['font.family'] = 'serif'
# It's good practice to list specific fonts if you want them to be used.
# 'Latin Modern Roman' is usually available if a full TeX Live is installed.
# If you face font issues, ensure LaTeX is correctly set up and fonts are accessible.
# For example: plt.rcParams['font.serif'] = ['Latin Modern Roman'] + plt.rcParams['font.serif']

# Define constants
pth = 0.091 / 100 * 2

# Time durations in seconds
sec_in_a_week = 7 * 24 * 60 * 60
sec_in_a_day = 24 * 60 * 60
sec_in_an_hour = 60 * 60

# Attack attempts
attacks_in_a_week = sec_in_a_week / 0.032
attacks_in_a_day = sec_in_a_day / 0.032
attacks_in_an_hour = sec_in_an_hour / 0.032

# Rowhammer threshold range
# MATLAB's 1000:1000:30000 includes 30000, so np.arange needs stop+step
RTH = np.arange(1000, 30001, 1000)

# Initialize arrays
psuccess_week = np.zeros_like(RTH, dtype=float)
psuccess_day = np.zeros_like(RTH, dtype=float)
psuccess_hour = np.zeros_like(RTH, dtype=float)

# Loop for calculations
for i, NRH in enumerate(RTH):
    nfmax = math.floor((32000000 / 45 - NRH) / 2)
    # MATLAB's 0:nfmax includes nfmax, so np.arange needs stop+1
    nf = np.arange(0, nfmax + 1)

    # Calculate psuccess (sum of a series)
    term1 = (1 - pth/2)**(nf + NRH)
    term2 = (pth/2)**nf
    psuccess = np.sum(term1 * term2)

    psuccess_week[i] = 1 - (1 - psuccess)**attacks_in_a_week
    psuccess_day[i] = 1 - (1 - psuccess)**attacks_in_a_day
    psuccess_hour[i] = 1 - (1 - psuccess)**attacks_in_an_hour

# --- Plotting ---
# Constants for figure size to match MATLAB's export behavior
inches_per_pt = 1 / 72.27
fig_width_pt = 229.5
fig_width_in = fig_width_pt * inches_per_pt
fig_height_in = fig_width_in * 0.2 # Initial aspect ratio from MATLAB

# MATLAB's final figure size adjustment: `([fig_width_in, fig_height_in] + 1) * 100`
# This implies adding 1 inch to width and height to cover margins.
# So, the effective figure size will be (width_in + 1) x (height_in + 1) inches.
final_fig_width_in = fig_width_in + 1.0 # Assuming 0.5in left + 0.5in right margin
final_fig_height_in = fig_height_in + 1.0 # Assuming 0.5in bottom + 0.5in top margin

fig, ax = plt.subplots(figsize=(final_fig_width_in, final_fig_height_in))

# Manually set axes position to mimic MATLAB's specific margin.
# MATLAB's [0.5, 0.5, fig_width_in, fig_height_in] implies 0.5in left/bottom margins
# and the actual plot area being fig_width_in x fig_height_in.
# In Matplotlib's normalized coordinates, this translates to:
left_frac = 0.5 / final_fig_width_in
bottom_frac = 0.5 / final_fig_height_in
width_frac = fig_width_in / final_fig_width_in
height_frac = fig_height_in / final_fig_height_in
ax.set_position([left_frac, bottom_frac, width_frac, height_frac])

# Plot the data
ax.plot(RTH, psuccess_week, '-o', color=[0.1, 0.4, 0.8], linewidth=1.5, markersize=5,
        markerfacecolor=[0.1, 0.4, 0.8], label='1 Week')
ax.plot(RTH, psuccess_day, '-s', color=[0.8, 0.1, 0.4], linewidth=1.5, markersize=5,
        markerfacecolor=[0.8, 0.1, 0.4], label='1 Day')
ax.plot(RTH, psuccess_hour, '-^', color=[0.2, 0.6, 0.2], linewidth=1.5, markersize=5,
        markerfacecolor=[0.2, 0.6, 0.2], label='1 Hour')

# Axis limits
ax.set_xlim([0.5 * 10**4, 3.0 * 10**4])
ax.set_ylim([0, 1])

# LaTeX styling and tick placement
font_size = 9

# Set font size for tick labels and label interpreters
ax.tick_params(axis='both', which='major', labelsize=font_size, direction='out', width=1)
ax.tick_params(axis='x', top=False) # remove top x-ticks

# Axis color and border
# Axis color and border
ax.spines['bottom'].set_color([0.2, 0.2, 0.2])
ax.spines['top'].set_color([0.2, 0.2, 0.2])
ax.spines['left'].set_color([0.2, 0.2, 0.2])
ax.spines['right'].set_color([0.2, 0.2, 0.2])
# ax.set_box_on(True) # plot border - REMOVE OR COMMENT OUT THIS LINE

# X-axis label
ax.set_xlabel(r'Rowhammer Threshold', fontsize=font_size)

# Custom Y-axis label placement
# MATLAB's text positioning is complex. For a horizontal label, setting as ylabel and adjusting position.
ax.set_ylabel(r'Success Probability', fontsize=font_size)
# Adjust label position relative to the axes. (x, y) coordinates where (0,0) is bottom-left of axes.
# This often requires tuning for exact visual match.
ax.yaxis.set_label_coords(-0.08, 0.5) # Example adjustment, tune as needed

# X-axis ticks and labels
x_ticks = np.arange(5000, 30001, 5000)
ax.set_xticks(x_ticks)
xticklabels = [f'{int(x/1000)}K' for x in x_ticks]
ax.set_xticklabels(xticklabels)

# Y-axis ticks and labels
ax.set_yticks([0, 0.5, 1.0])
ax.set_yticklabels(['0', '0.5', '1.0'])

# Grid styling
ax.grid(axis='y', linestyle='--', alpha=0.6, color=[0.5, 0.5, 0.5])
ax.grid(axis='x', visible=False) # 'XGrid', 'off'

# Add legend with light gray border
ax.legend(loc='upper right', fontsize=font_size, frameon=True, edgecolor=[0.7, 0.7, 0.7])

# Export the plot to PDF
plt.savefig('plot_atk_success_rate.pdf', format='pdf') # bbox_inches='tight' can help with margins

# To display the plot (optional, typically commented out when exporting)
# plt.show()
