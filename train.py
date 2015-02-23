import ipdb
import logging
import os
import theano
import time

from itertools import izip
from layer import *
from monitor import Monitor
from opt import *
from util import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Training(object):
    """
    WRITEME

    Parameters
    ----------
    .. todo::
    """
    def __init__(self,
                 data,
                 model,
                 optimizer,
                 outputs,
                 extension=None):
        self.data = data
        self.model = model
        self.optimizer = optimizer
        self.extension = extension
        
        self.inputs = model.get_inputs()
        outputs = tolist(outputs)
        self.outputs = outputs

        self.cost_fn = self.build_training_graph()
        self.trainlog = TrainLog()

        self.endloop = 0
       
    def build_training_graph(self):
        cost = self.model.nodes['cost'].out
        self.grads = OrderedDict(izip(self.model.params,
                                      T.grad(cost, self.model.params)))
        self.run_extension('ext_opt')
        updates = self.optimizer.get_updates(self.grads)
        return self.get_theano_graph(updates)

    def get_theano_graph(self, updates=[]):
        return theano.function(inputs=self.inputs,
                               outputs=self.outputs,
                               updates=updates,
                               on_unused_input='ignore',
                               allow_input_downcast=True)

    def run(self):
        logger.info("Starting main loop")    
        while self.run_epoch():
            pass
                 
    def run_epoch(self):
        while self.run_batch():
            pass
        self.trainlog._epoch_seen += 1
        self.run_extension('ext_term')
        if self.end_training():
            return False
        return True

    def run_batch(self):
        try:
            batch = self.data.next()
        except:
            return False
        batch_t0 = time.time()
        this_cost = self.cost_fn(*batch)
        self.trainlog._times.append(time.time() - batch_t0)
        self.trainlog._batches.append(this_cost)
        self.trainlog._batch_seen += 1
        self.run_extension('ext_monitor')
        return True

    def find_extension(self, name):
        try:
            exts = [extension for extension in self.extension
                    if extension.name==name]
            if len(exts) > 0:
                return_val = 1
            else:
                return_val = 0
            return return_val, exts
        except:
            return (0, None)

    def run_extension(self, name):
        tok, exts = self.find_extension(name)
        if tok:
            for ext in exts:
                ext.exe(self)

    def end_training(self):
        return self.endloop


class TrainingEnd(Exception):
    pass


class TrainLog(object):
    """
    Training log class

    Parameters
    ----------
    .. todo::
    """
    def __init__(self):
        self._batches = []
        self._times = []
        self._ddmonitors = [] 
        self._epoch_seen = 0 
        self._batch_seen = 0 
