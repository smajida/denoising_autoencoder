#!/usr/bin/env python
# encoding: utf-8
"""
dae.py

Guillaume Alain.
"""

import sys
import os
import pdb
import numpy as np

from theano import *
import theano.tensor as T

from dae import DAE

class DAE_untied_weights(DAE):
    """
    A DAE with tanh input units and tanh hidden units.
    """
    def __init__(self,
                 n_inputs=None,
                 n_hiddens=None,
                 W,
                 c=None,  b=None,
                 s=None, act_func=['tanh', 'tanh'],
                 want_plus_x = False)
        """
        Initialize a DAE.
        
        Parameters
        ----------
        n_inputs : int
            Number of inputs units
        n_hiddens : int
            Number of hidden units
        W  : array-like, shape (n_inputs, n_hiddens), optional
             Weight matrix, where n_inputs in the number of input
             units and n_hiddens is the number of hidden units.
        c : array-like, shape (n_hiddens,), optional
            Biases of the hidden units
        b : array-like, shape (n_inputs,), optional
            Biases of the input units
        s : real
            Applied after the second tanh at the output.
            Allows us to represent values in a range [-4,4]
            instead of just [-1,1] by using alpha = 4.0.
        """


        # These values are to be treated as READ-ONLY.
        self.n_inputs = n_inputs
        self.n_hiddens = n_hiddens

        # These values are expected to be modified by
        # algorithms that take the DAE instance as parameter.
        # ex : any training function
        self.reset_params()
        if not (W == None):
            self.W = W
        if not (c == None):
            self.c = c
        if not (b == None):
            self.b = b
        if not (s == None):
            self.s = s

        if len(act_func) != 2:
            error("Need to specify two activation functions from : ['tanh', 'sigmoid', 'id'].")
        else:
            for f in act_func:
                if not f in ['tanh', 'sigmoid', 'id']:
                    error("Unrecognized activation function. Should be from : ['tanh', 'sigmoid', 'id'].")
            if act_func[0] == 'id':
                print "It's a bad idea to use the identity as first activation function. \nMaybe you got the ordering mixed up ?"
        self.act_func = act_func

        self.want_plus_x = want_plus_x
        self.tied_weights = True

        # then setup the theano functions once
        self.theano_setup()
    
    def theano_setup(self):
    
        W = T.dmatrix('W')
        b = T.dvector('b')
        c = T.dvector('c')
        s = T.dscalar('s')
        x = T.dmatrix('x')
    
        h_act = T.dot(x, W) + c
        if act_func[0] == 'tanh':
            h = T.tanh(h_act)
        elif act_func[0] == 'sigmoid':
            h = T.nnet.sigmoid(h_act)
        else act_func[0] == 'id':
            # bad idae
            h = h_act

        r_act = T.dot(h, W.T) + b

        if act_func[1] == 'tanh':
            r = s * T.tanh(r_act)
        elif act_func[1] == 'sigmoid':
            r = s * T.nnet.sigmoid(r_act)
        else act_func[1] == 'id':
            r = s * r_act

        if self.want_plus_x:
            r = r + x

        # Another variable to be able to call a function
        # with a noisy x and compare it to a reference x.
        y = T.dmatrix('y')

        loss = ((r - y)**2)
        sum_loss = T.sum(loss)
        
        # theano_encode_decode : vectorial function in argument X.
        # theano_loss : vectorial function in argument X.
        # theano_gradients : returns triplet of gradients, each of
        #                    which involves the all data X summed
        #                    so it's not a "vectorial" function.

        self.theano_encode_decode = function([W,b,c,s,x], r)
        self.theano_loss = function([W,b,c,s,x,y], loss)

        self.theano_gradients = function([W,b,c,s,x,y],
                                         [T.grad(sum_loss, W),
                                          T.grad(sum_loss, b),  T.grad(sum_loss, c),
                                          T.grad(sum_loss, s)])
        # other useful theano functions for the experiments that involve
        # adding noise to the hidden states
        self.theano_encode = function([W,c,x], h)
        self.theano_decode = function([W,b,s,h], r)
        

    def encode(self, X):
        if X.shape[1] != self.n_inputs:
            error("Using wrong shape[1] for the argument X to DAE.encode. It's %d when it should be %d" % (X.shape[1], self.n_inputs))
        return self.theano_encode(self.W, self.c, X)

    def decode(self, H):
        if H.shape[1] != self.n_hiddens:
            error("Using wrong shape[1] for the argument H to DAE.decode. It's %d when it should be %d" % (H.shape[1], self.n_hiddens))
        return self.theano_decode(self.W, self.b, self.s, H)


    def encode_decode(self, X):
        if X.shape[1] != self.n_inputs:
            error("Using wrong shape[1] for the argument X to DAE.encode_decode. It's %d when it should be %d" % (X.shape[1], self.n_inputs))

        return self.theano_encode_decode(self.W, self.b, self.c, self.s, X)


    def model_loss(self, X, noisy_X = None):
        """
        X:       array-like, shape (n_examples, n_inputs)
        noisy_X: array-like, shape (n_examples, n_inputs)

        Returns  loss: array-like, shape (n_examples,)
        """

        return self.theano_loss(self.W, self.b, self.c, self.s, noisy_X, X)


    def reset_params(self):
        self.W = np.random.uniform( low = -1.0, high = 1.0, size=(self.n_inputs, self.n_hiddens) )
        self.b  = np.random.uniform( low = -0.1, high = 0.1, size=(self.n_inputs,) )
        self.c  = np.random.uniform( low = -0.1, high = 0.1, size=(self.n_hiddens,) )
        self.s  = 1.0


def main():
    pass


if __name__ == '__main__':
    main()
