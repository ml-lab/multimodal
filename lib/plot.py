"""Usefull plot functions.
Inspired (and somtime copied from http://olgabot.github.io/prettyplotlib/)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
"""


import numpy as np
#import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import colorConverter

#import brewer2mpl


NavyBlue = '#006EB8'
Red = '#ED1B23'


def plot(*args, **kwargs):
    ax = kwargs.pop('ax', plt.gca())
    if 'linewidth' not in kwargs:
        kwargs['linewidth'] = 0.75
    lines = ax.plot(*args, **kwargs)
    remove_chartjunk(ax, ['top', 'right'])
    return lines


def legend(*args, **kwargs):
    facecolor = colorConverter.to_rgba('white', alpha=.9)
    ax = kwargs.pop('ax', plt.gca())
    legend = ax.legend(*args, frameon=True, scatterpoints=1, **kwargs)
    rect = legend.get_frame()
    rect.set_facecolor(facecolor)
    return legend


def plot_var(y, x=None, color=None, var=True, var_style='fill', **kwargs):
        #linestyle='-', label='', marker='',
        #linewidth=1, markersize=6.):
    """
    Plots a set of data: the mean is plotted as a standard curve,
    and an area around the curve of width twice the standard
    deviation is filled with colored background.

    @param y: two dimensional array, samples for the same value are on axis 1.
    @param color: color to use
    @param x: optional abscisse
    @param var_style: 'fill' (default) | 'bar'
    """
    ax = kwargs.pop('ax', plt.gca())
    mean = np.mean(y, axis=1)
    std = np.std(y, axis=1)
    if x is None:
        x = np.arange(y.shape[0])
    plot_fun = plt.plot
    if var and var_style in ('bar', 'both'):
        kwargs['yerr'] = std
        plot_fun = plt.errorbar
    if color is not None:
        kwargs['color'] = color
        kwargs['markeredgecolor'] = color
    lines = plot_fun(x, mean, **kwargs)
    if color is None:
        color = lines[0].get_color()
    x = lines[0].get_xdata()
    if var and var_style in ('fill', 'both'):
        plt.fill_between(x, mean - std, mean + std, alpha=.3, color=color)
    remove_chartjunk(ax, ['top', 'right'])
    return lines


def boxplot(x, ax=None, **kwargs):
    """
    Create a box-and-whisker plot showing the mean, 25th percentile, and 75th
    percentile. The difference from matplotlib is only the left axis line is
    shown, and ticklabels labeling each category of data can be added.

    @param ax:
    @param x:
    @param kwargs:
    @return:
    """
    if ax is None:
        ax = plt.gca()
    # If no ticklabels are specified, don't draw any
    xticklabels = kwargs.pop('xticklabels', None)

    if 'widths' not in kwargs:
        kwargs['widths'] = 0.15
    bp = ax.boxplot(x, **kwargs)
    if xticklabels:
        ax.xaxis.set_ticklabels(xticklabels)

    remove_chartjunk(ax, ['top', 'right', 'bottom'])
    linewidth = 0.75

    plt.setp(bp['boxes'], color=NavyBlue, linewidth=linewidth)
    plt.setp(bp['medians'], color=Red)
    plt.setp(bp['whiskers'], color=NavyBlue, linestyle='solid',
             linewidth=linewidth)
    plt.setp(bp['fliers'], color=NavyBlue)
    plt.setp(bp['caps'], color=NavyBlue, linewidth=linewidth)
    ax.spines['left']._linewidth = 0.5
    return bp


def remove_chartjunk(ax, spines, grid=None, ticklabels=None):
    '''
    Removes "chartjunk", such as extra lines of axes and tick marks.

    If grid="y" or "x", will add a white grid at the "y" or "x" axes,
    respectively

    If ticklabels="y" or "x", or ['x', 'y'] will remove ticklabels from that
    axis
    '''
    all_spines = ['top', 'bottom', 'right', 'left']
    for spine in spines:
        ax.spines[spine].set_visible(False)

    # For the remaining spines, make their line thinner and a slightly
    # off-black dark grey
    for spine in all_spines:
        if spine not in spines:
            ax.spines[spine].set_linewidth(0.5)
            # ax.spines[spine].set_color(almost_black)
            #            ax.spines[spine].set_tick_params(color=almost_black)
            # Check that the axes are not log-scale. If they are, leave the
            # ticks because otherwise people assume a linear scale.
    x_pos = set(['top', 'bottom'])
    y_pos = set(['left', 'right'])
    xy_pos = [x_pos, y_pos]
    xy_ax_names = ['xaxis', 'yaxis']

    for ax_name, pos in zip(xy_ax_names, xy_pos):
        axis = ax.__dict__[ax_name]
        # axis.set_tick_params(color=almost_black)
        if axis.get_scale() == 'log':
            # if this spine is not in the list of spines to remove
            for p in pos.difference(spines):
                axis.set_ticks_position(p)
                #                axis.set_tick_params(which='both', p)
        else:
            axis.set_ticks_position('none')

    if grid is not None:
        for g in grid:
            assert g in ('x', 'y')
            ax.grid(axis=grid, color='white', linestyle='-', linewidth=0.5)

    if ticklabels is not None:
        if type(ticklabels) is str:
            assert ticklabels in set(('x', 'y'))
            if ticklabels == 'x':
                ax.set_xticklabels([])
            if ticklabels == 'y':
                ax.set_yticklabels([])
        else:
            assert set(ticklabels) | set(('x', 'y')) > 0
            if 'x' in ticklabels:
                ax.set_xticklabels([])
            elif 'y' in ticklabels:
                ax.set_yticklabels([])