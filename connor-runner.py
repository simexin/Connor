#!/usr/bin/env python

"""Convenience wrapper for running connor directly from source tree."""


from connor.connor import main
import sys

if __name__ == '__main__':
#    import cProfile
#    cProfile.run('main()')
    main(sys.argv)
