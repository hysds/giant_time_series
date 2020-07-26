import os
import logging
import matplotlib as mpl
import matplotlib.pyplot as plt


mpl.use('Agg')


log_format = "[%(asctime)s: %(levelname)s/%(name)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)
logger = logging.getLogger(os.path.splitext(os.path.basename(__file__))[0])


def plot_stack(ifg_dates, plt_file):
    "Plot stack."""

    fig1, axis = plt.subplots()
    mains = []
    subordinates = []
    for index, ifg in enumerate(ifg_dates):
        main_dt, subordinate_dt = ifg
        axis.plot([main_dt, subordinate_dt], [index, index])
        mains.append(main_dt)
        subordinates.append(subordinate_dt)
    axis.scatter(mains, range(0, len(mains)), marker="o", label="Main")
    axis.scatter(subordinates, range(0, len(subordinates)), marker="+", label="Subordinate")
    plt.title("Network Pair Coverage By Time")
    axis.set_xlabel('Time')
    axis.set_ylabel('Pairings Sorted By Start Time')
    plt.legend()
    fig1.savefig(plt_file)
