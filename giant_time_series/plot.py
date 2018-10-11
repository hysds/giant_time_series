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
    masters = []
    slaves = []
    for index, ifg in enumerate(ifg_dates):
        master_dt, slave_dt = ifg
        axis.plot([master_dt, slave_dt], [index, index])
        masters.append(master_dt)
        slaves.append(slave_dt)
    axis.scatter(masters, range(0, len(masters)), marker="o", label="Master")
    axis.scatter(slaves, range(0, len(slaves)), marker="+", label="Slave")
    plt.title("Network Pair Coverage By Time")
    axis.set_xlabel('Time')
    axis.set_ylabel('Pairings Sorted By Start Time')
    plt.legend()
    fig1.savefig(plt_file)
