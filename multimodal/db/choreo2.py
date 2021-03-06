# encoding: utf-8


"""Choerography dataset v2.

    More information can be found at:
    http://flowers.inria.fr/choreo2/
"""


import os

import numpy as np

from ..local import CONFIG
from ..lib.net import check_destination_path, urlretrieve
from .models.kinect_motion import MotionDatabase
from .models.loader import Loader
from ..features.angle_histograms import db_to_VQ_hist_matrix


DEFAULT_NB_BINS = 15  # Used to build features
SRC = 'http://olivier.mangin.com/data/choreo2/'
DEFAULT_META_FILE_NAME = 'choreo2.json'
DEFAULT_FEATURES_FILE_NAME = 'choreo2_angle_hist.npz'


def default_db_file():
    return os.path.join(CONFIG['db-dir'], 'choreo2', DEFAULT_META_FILE_NAME)


def get_default_feature_file():
    return os.path.join(CONFIG['feat-dir'], DEFAULT_FEATURES_FILE_NAME)


# Load motion DB and features

def load(db_file=None, verbose=False):
    if db_file is None:
        db_file = default_db_file()
    return MotionDatabase.load_from_npz(db_file, verbose=verbose)

load.__doc__ = MotionDatabase.load_from_npz.__doc__


class Choreo2Loader(Loader):

    dataset_name = 'choreo2'

    def get_data(self):
        X = load_features()
        self.check_n_samples(X.shape[0])
        return X

    def get_labels(self):
        db = load(verbose=False)
        motion_names = db.label_descriptions
        self.check_n_samples(len(db.records))
        return [motion_names[r[1][0]] for r in db.records]


# Deprecated
def load_features_and_labels(db_file=None, feat_file=None):
    db = load(db_file=db_file)
    X = load_features(feat_file=feat_file)
    labels = [r[1] for r in db.records]
    assert(X.shape[0] == len(labels))
    return X, labels, db.label_descriptions


def load_features(feat_file=None):
    if feat_file is None:
        feat_file = get_default_feature_file()
    return np.load(feat_file)['Xmotion']


def build_features(db_file=None, feat_file=None, force=False,
                   nb_bins=DEFAULT_NB_BINS, verbose=False):
    """Build histograms of angle and velocities features.
       May take a few minutes.
    """
    if feat_file is None:
        feat_file = get_default_feature_file()
    if os.path.exists(feat_file) and not force:
        raise ValueError("Feature file exists at {}.".format(feat_file))
    db = load(db_file=db_file)
    # Generate features
    if verbose:
        print('Computing histograms (may take a few minutes)...')
    X = db_to_VQ_hist_matrix(db, vel_delay=10, nb_bins=nb_bins)
    np.savez(feat_file, Xmotion=X)
    if verbose:
        print("Motion features generated and saved to: %s." % feat_file)


def __get_dest(dest, extension=True):
    if dest is None:
        file_ = default_db_file()
        dest = os.path.dirname(file_)
        name = os.path.basename(file_)
    else:
        name = DEFAULT_META_FILE_NAME
    if not extension:
        name, _ = os.path.splitext(name)
    return dest, name


def download_meta(dest=None, overwrite=False):
    """Downloads description and features of the dataset."""
    dest, name = __get_dest(dest, extension=True)
    file_ = check_destination_path(dest, name, overwrite=overwrite)
    urlretrieve(SRC + name, file_)


def download(dest=None, overwrite=False):
    """Downloads description and features of the dataset."""
    dest, name = __get_dest(dest, extension=False)
    urlretrieve(SRC + name + '.json',
                check_destination_path(dest, name + '.json',
                                       overwrite=overwrite))
    urlretrieve(SRC + name + '.npz',
                check_destination_path(dest, name + '.npz',
                                       overwrite=overwrite))


def download_with_features(meta_dest=None, features_dest=None,
                           overwrite=False):
    """Downloads description and features of the dataset."""
    download(dest=meta_dest, overwrite=overwrite)
    if features_dest is None:
        features_dest = CONFIG['feat-dir']
    features_name = DEFAULT_FEATURES_FILE_NAME
    features_file = check_destination_path(features_dest, features_name,
                                           overwrite=overwrite)
    urlretrieve(SRC + features_name, features_file)
