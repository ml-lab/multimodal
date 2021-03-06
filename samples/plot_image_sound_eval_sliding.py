import os

import numpy as np
import matplotlib as plt

from multimodal.lib.metrics import mutual_information
from multimodal.lib.logger import Logger
from multimodal.lib.window import (BasicTimeWindow, ConcatTimeWindow,
                                   concat_from_list_of_wavs,
                                   slider)
from multimodal.lib.plot import TEN_COLORS
from multimodal.db.acorns import Year1Loader as AcornsLoader
from multimodal.plots import InteractivePlot, plot_one_sentence


WIDTH = .5
SHIFT = .1

WORKDIR = os.path.expanduser('~/work/data/results/quick/')
COLORS = TEN_COLORS

sound_loader = AcornsLoader(1)

logger = Logger.load(os.path.join(WORKDIR, 'sliding'))

# Build windows to access time and metadata
sound_modality = logger.get_value('modalities').index('sound')
assoc_idx = logger.get_value('sample_pairing')
test_idx = [assoc_idx[i][sound_modality]
            for i in logger.get_last_value('test')]
test_records = set([sound_loader.records[i] for i in test_idx])
all_wavs = [sound_loader.records[i[sound_modality]].get_audio_path()
            for i in assoc_idx]
all_sound_labels = sound_loader.get_labels()
sound_labels = logger.get_value('label_pairing')[sound_modality]
n_labels = len(sound_labels)
test_labels = [sound_labels.index(all_sound_labels[i]) for i in test_idx]
print('Building time windows from wav files...')
sound_wins = concat_from_list_of_wavs(all_wavs)
# Also build index windows
record_wins = ConcatTimeWindow([
    BasicTimeWindow(w.absolute_start, w.absolute_end,
                    obj=sound_loader.records[i[sound_modality]])
    for i, w in zip(assoc_idx, sound_wins.windows)
    ])
# Sliding windows
sliding_wins = [sound_wins.get_subwindow(ts, te)
                for ts, te in slider(sound_wins.absolute_start,
                                     sound_wins.absolute_end,
                                     WIDTH, SHIFT)
                ]


similarities = -logger.get_last_value('sliding_distances')


def word_histo_by_label(records, labels):
    assert(len(records) == len(labels))
    labels = [w.lower() for w in labels]
    all_labels = list(set(labels))
    words_by_record = [r.trans.strip('.?!').lower().split() for r in records]
    all_words = set(sum(words_by_record, []))
    # Re-order with all labels first
    all_words = all_labels + sorted(list(all_words.difference(all_labels)))
    word_idx = [[all_words.index(w) for w in set(t)] for t in words_by_record]
    word_counts = [np.bincount(t, minlength=len(all_words)) for t in word_idx]
    counts_by_labels = [[] for _ in all_labels]
    for l, h in zip(labels, word_counts):
        counts_by_labels[all_labels.index(l)].append(h)
    h = np.vstack([np.sum(1. * np.vstack(l), axis=0)
                   for l in counts_by_labels]).T
    h /= len(records)
    p_labels = 1. * np.array([len(l) for l in counts_by_labels]) / len(records)
    return h, p_labels, all_labels, all_words


h, p_labels, all_labels, all_words = word_histo_by_label(
    sound_loader.records, sound_loader.get_labels())
word_label_info = np.zeros(h.shape)
for i in range(len(all_words)):
    for j in range(len(all_labels)):
        hist = [[h[i, j],
                 sum(h[i, :j]) + sum(h[i, (j + 1):])],
                [p_labels[j] - h[i, j],
                 sum(p_labels - h[i, :]) - p_labels[j] + h[i, j]],
                ]
        word_label_info[i, j] = mutual_information(np.array(hist))

plt.interactive(True)
plt.style.use('ggplot')
example_labels = [sound_labels[i] for i in logger.get_last_value('label_ex')]
myplot = InteractivePlot(record_wins, sliding_wins, similarities,
                         example_labels, is_test=lambda r: r in test_records,
                         plot_rc={'colors': COLORS})

# Prepare for plotting sentence results in files
DESTDIR = os.path.join(WORKDIR, 'sliding_win_plots')
if not os.path.exists(DESTDIR):
    os.mkdir(DESTDIR)
    os.mkdir(os.path.join(DESTDIR, 'annotated'))
PLOT_PARAMS = {
    'font.family': 'serif',
    'font.size': 9.0,
    'font.serif': 'Computer Modern Roman',
    'text.usetex': 'True',
    'text.latex.unicode': 'True',
    'axes.titlesize': 'large',
    'axes.labelsize': 'large',
    'legend.fontsize': 'medium',
    'xtick.labelsize': 'small',
    'ytick.labelsize': 'small',
    'path.simplify': 'True',
    'savefig.bbox': 'tight',
    'figure.figsize': (7.5, 4),
}
SENTENCE_PLOT_RC = {
    'window_boundaries_color': 'gray',
    'window_boundaries_line_width': 1,
    'colors': COLORS,
    'markersize': 3,
}
# Plot sentence results to disk
test_record_wins = [w for w in record_wins.windows
                    if w.obj in test_records]
#with plt.rc_context(rc=PLOT_PARAMS):
#    plt.pyplot.interactive(False)
#    for r in test_record_wins:
#        score_plot = plot_one_sentence(r, sliding_wins, similarities,
#                                       example_labels,
#                                       plot_rc=SENTENCE_PLOT_RC)
#        for ext in ['svg', 'pdf']:
#            path = os.path.join(DESTDIR, '{}.{}'.format(
#                r.obj.audio.split('.')[0],
#                ext))
#            score_plot.fig.savefig(path, transparent=True)
#            print('Written: {}.'.format(path))

# Also dump train transcriptions to file
with open(os.path.join(DESTDIR, 'train_trans.txt'), 'w') as f:
    f.write('\n'.join([r.trans for r in sound_loader.records
                       if r not in test_records]))

ANNOTATIONS = [
    (36, [('book', (.8, 1.))]),  # 0648
    (89, [('Daddy', (.72, .96))]),  # 0215
    (16, [('Angus', (.74, 1.01)),
          ('shoe', (1.53, 1.93))]),  # 0595
    (67, [('bottle', (1., 1.28))]),  # 0771
]
with plt.rc_context(rc=PLOT_PARAMS):
    plt.pyplot.interactive(False)
    # Plot sentence results to disk
    test_record_wins = [w for w in record_wins.windows
                        if w.obj in test_records]
    for i, ann in ANNOTATIONS:
        win = test_record_wins[i]
        score_plot = plot_one_sentence(win, sliding_wins, similarities,
                                       example_labels,
                                       plot_rc=SENTENCE_PLOT_RC,
                                       annotate=ann)
        for ext in ['svg', 'pdf', 'eps']:
            path = os.path.join(DESTDIR, 'annotated', '{}.{}'.format(
                win.obj.audio.split('.')[0],
                ext))
            score_plot.fig.savefig(path, transparent=True)
            print('Written: {}.'.format(path))


# Print confusion matrix
found_labels = logger.get_last_value('found_sound2objects_cosine')
confusion = np.zeros((n_labels, n_labels))
assert(len(test_labels) == len(found_labels))
for l, lfound in zip(test_labels, found_labels):
    confusion[l, lfound] += 1.
print(sound_labels)
print(confusion)


#plt.pyplot.figure()
##most_info = np.nonzero(np.max(word_label_info, axis=1) > .04)[0]
##p = pcolormesh(word_label_info[most_info, :],
##               xticklabels=all_labels,
##               yticklabels=[all_words[i] for i in most_info])
#p = pcolormesh(word_label_info, xticklabels=all_labels, yticklabels=all_words)
#plt.pyplot.colorbar(p)
#
##plot_one_sentence(record_wins[0], sliding_wins, sound_labels, similarities)
