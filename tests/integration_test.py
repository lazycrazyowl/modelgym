import pytest

from modelgym.models import XGBClassifier, RFClassifier, LGBMClassifier, CtBClassifier, \
                            XGBRegressor, LGBMRegressor, CtBRegressor
from modelgym.trainers import TpeTrainer, RandomTrainer, RFTrainer, GPTrainer
from modelgym.metrics import RocAuc, Accuracy, Mse
from modelgym.utils import XYCDataset, ModelSpace
from modelgym.trackers import LocalTracker

import os
import shutil
from hyperopt import hp

from sklearn.datasets import make_classification, make_regression

TRAINER_CLASS = [TpeTrainer, RandomTrainer, GPTrainer, RFTrainer]
TRACKABLE_TRAINER_CLASS = [TpeTrainer, RandomTrainer]


@pytest.mark.parametrize("trainer_class", TRAINER_CLASS)
def test_basic_pipeline_biclass(trainer_class):
    X, y = make_classification(n_samples=200, n_features=20,
                               n_informative=10, n_classes=2)

    ctb_model_space = ModelSpace(CtBClassifier, {
                'learning_rate': hp.loguniform('learning_rate', -5, -1),
                'iterations': 10
            })

    trainer = trainer_class([XGBClassifier, LGBMClassifier, RFClassifier, ctb_model_space])
    dataset = XYCDataset(X, y)
    trainer.crossval_optimize_params(Accuracy(), dataset, opt_evals=3)
    trainer.get_best_results()


@pytest.mark.parametrize("trainer_class", TRAINER_CLASS)
def test_basic_pipeline_regression(trainer_class):
    X, y = make_regression(n_samples=200, n_features=20,
                           n_informative=10, n_targets=1)
    xgb_model_space = ModelSpace(XGBRegressor, {'n_estimators': 15}, name='XGB')
    ctb_model_space = ModelSpace(CtBRegressor, {
                'learning_rate': hp.loguniform('learning_rate', -5, -1),
                'iterations': 10
            })
    trainer = trainer_class([LGBMRegressor, xgb_model_space, ctb_model_space])
    dataset = XYCDataset(X, y)
    trainer.crossval_optimize_params(Mse(), dataset, opt_evals=3)
    results = trainer.get_best_results()
    assert results['XGB']['result']['params']['n_estimators'] == 15


@pytest.mark.parametrize("trainer_class", TRACKABLE_TRAINER_CLASS)
def test_advanced_pipeline_biclass(trainer_class):
    try:
        X, y = make_classification(n_samples=200, n_features=20,
                                   n_informative=10, n_classes=2)
        DIR = '/tmp/local_dir'
        tracker = LocalTracker(DIR)

        ctb_model_space = ModelSpace(CtBClassifier, {
                    'learning_rate': hp.loguniform('learning_rate', -5, -1),
                    'iterations': 10
                })

        trainer = trainer_class([XGBClassifier, LGBMClassifier, RFClassifier, ctb_model_space],
                                tracker=tracker)
        dataset = XYCDataset(X, y)
        trainer.crossval_optimize_params(Accuracy(), dataset, opt_evals=3,
                                         metrics=[RocAuc()])
        trainer.get_best_results()

        assert os.listdir(DIR)
    except Exception as e:
        try:
            shutil.rmtree(DIR)
        except Exception as _:
            pass
        raise e
