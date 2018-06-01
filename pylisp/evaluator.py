#!/usr/bin/env python3
from .frame import Frame, Stats

from itertools import count
from logging import getLogger
logger = getLogger(__name__)

def evaluate(insts, env=None):
    if env is None:
        env = {}

    stats = Stats()
    frames = [Frame(insts, env=env, stats=stats)]
    stats.num_frames += 1
    stats.max_frame_depth = max(stats.max_frame_depth, len(frames))
    for step in count():
        if not frames:
            break

        try:
            inst = next(frames[-1])
        except StopIteration:
            break
        try:
            f = frames[-1]
            logger.debug('step             = %r', step)
            logger.debug('frame            = %s', hex(id(f)))
            logger.debug('pc               = %r', f.pc)
            logger.debug('inst             = %r', inst)
            logger.debug('#insts           = %r', len(f.insts))
            logger.debug('insts[pc-5:pc+5] = %r', f.insts[f.pc-5:f.pc+5])
            logger.debug('insts            = %r', f.insts)
            logger.debug('env              = %r', f.env)
            logger.debug('stack            = %r', f.stack)
            frames[-1].stats.num_insts += 1
            inst(frames)
        except Exception as e:
            logger.critical('error = %r', e)
            raise
    return stats

__all__ = [
    'evaluate',
]
