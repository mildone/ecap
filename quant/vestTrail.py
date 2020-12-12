import QUANTAXIS as QA
try:
    assert QA.__version__ >= '1.1.0'
except AssertionError:
    print('pip install QUANTAXIS >= 1.1.0 请升级QUANTAXIS后再运行此示例')
    import QUANTAXIS as QA
import numpy as np

read_dictionary = np.load('../liutong.npy', allow_pickle=True).item()

import quant.Pivot as pi
import quant.force as force

if __name__ == "__main__":
    code = '600745'
    force.forceANA(code)
    pi.strategyWP(code)

