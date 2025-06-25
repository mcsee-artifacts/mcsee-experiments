import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns   # only for palette
import pandas as pd
from matplotlib.ticker import AutoMinorLocator

# 1 pt = 1/72.27 in (TeX point)
width_pt = 229.5 * 1.05
inches_per_pt = 1.0 / 72.27
fig_width = width_pt * inches_per_pt
fig_height = fig_width * 0.65   # keep your original 10×4 aspect ratio

# LaTeX style
# mpl.rcParams.update({
#     'text.usetex': True,
#     'font.family': 'serif',
#     'font.serif': ['Computer Modern Roman'],
#     'axes.labelsize': 8,
#     'font.size': 8,
#     'xtick.labelsize': 8,
#     'ytick.labelsize': 8,
#     'legend.fontsize': 8,
#    #  'figure.dpi': ,
# })

# Unified LaTeX-style plot settings
plt.rcParams.update({
    "text.usetex": False,
    'figure.figsize': (fig_width, fig_height),
    "font.family": "serif",
    "axes.labelsize": 8,
    "font.size": 8,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "hatch.linewidth": 0.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

# Load the CSV
file_path = "./act2act_distances_per_bank.csv"
nbanks = []
values = []

with open(file_path, "r") as f:
    for line in f:
        items = line.strip().split(",")
        if len(items) < 2:
            continue
        n = int(items[0])
        v = list(map(float, items[1:]))
        nbanks.extend([n] * len(v))
        values.extend(v)

df_violin_full = pd.DataFrame({'nbanks': nbanks, 'value': values})

min_outliers = 10

# 1) build a boolean mask of **all** outliers in your full df
mask = df_violin_full.groupby('nbanks')['value'].transform(
    lambda g: (g < (g.quantile(.25) - 1.5*(g.quantile(.75)-g.quantile(.25)))) |
              (g > (g.quantile(.75) + 1.5*(g.quantile(.75)-g.quantile(.25))))
)

# 2) grab just those rows
raw_out = df_violin_full[mask].copy()

# 3) count how many outliers each bucket has
out_counts = raw_out['nbanks'].value_counts()

# 4) keep only buckets with >= min_outliers
keep_buckets = out_counts[out_counts >= min_outliers].index
df_outliers_full = raw_out[ raw_out['nbanks'].isin(keep_buckets) ]


# start the figure (size now comes from rcParams)
plt.figure()

# Reference line
plt.plot([0, 15], [10, 160],
         color="#555555", linestyle='-', linewidth=1.0, zorder=1)

# palette
n_levels = df_violin_full['nbanks'].nunique()
pal = sns.color_palette("Set2", n_levels)

# group into lists
grouped   = df_violin_full.groupby('nbanks')['value'].apply(list)
positions = grouped.index.tolist()    # these become y-positions now
data      = grouped.values.tolist()

parts = plt.violinplot(
    data,
    positions=positions,
    widths=1.4,
    showmeans=False,
    showmedians=False,
    showextrema=False,
    vert=False,
)

# thin the edges
for body, color in zip(parts['bodies'], pal):
    body.set_facecolor(color)
    body.set_edgecolor('black')
    body.set_linewidth(0.3)    # ← thinner outline (default is ~1.0)
    body.set_alpha(1.0)
    body.set_zorder(2)

if len(df_outliers_full) > 20000:
    df_outliers_full = df_outliers_full.sample(20000, random_state=42)

# scatter your filtered outliers on top (swap x/y)
plt.scatter(
    df_outliers_full['value'],  # x now = distance
    df_outliers_full['nbanks'], # y now = #banks
    color='black',
    s=0.3,
    alpha=1,
    zorder=3
)


# labels
plt.xlabel(r'ACT-to-ACT Distance')
plt.ylabel(r'#Banks hammered')

# grid and limits
plt.grid(True, axis='y', linestyle='--', alpha=0.5)
plt.xlim(left=0)
plt.ylim(0, 17)
# plt.xlim(0, 500)
plt.xlim(0, 325)

# major y-ticks at every integer but only label the odd ones
major_yticks = list(range(1, 17))
plt.yticks(major_yticks,
           [str(i) if (i % 2 == 1) else '' for i in major_yticks])

# add minor ticks on x-axis and push them outside
ax = plt.gca()
# 4 intervals ⇒ 3 ticks between each pair of majors
ax.xaxis.set_minor_locator(AutoMinorLocator(4))
ax.tick_params(axis='x', which='minor', length=3, direction='out')

# only odd y‐tick labels
major_yticks = list(range(1,17))
plt.yticks(major_yticks,
           [str(i) if (i%2==1) else '' for i in major_yticks])

# move the y‐label to the top-left corner…
ax.yaxis.set_label_coords(-0.08, 1.02)   # (x,y) in axis fraction

# …make it horizontal and left-aligned
lbl = ax.yaxis.get_label()
lbl.set_rotation(0)       # ← no more 90° rotation
lbl.set_ha('left')        # left-align the text
lbl.set_va('bottom')      # anchor its bottom at y=1.02


plt.tight_layout(pad=0.5)
plt.savefig("../../sledgehammer_act2actdistances.pdf")
# plt.savefig("../../sledgehammer_act2actdistances.pgf")
# plt.tight_layout()
# plt.show()
