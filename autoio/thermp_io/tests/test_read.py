""" Test reading files for ThermP
"""

import numpy
import thermp_io
from _util import read_text_file


OUT_STR1 = read_text_file(['data'], 'thermp.out')
OUT_STR2 = ''


def test__hf298k():
    """ test thermp_io.readar.hf298k
    """

    ref_hf298k = (71.96999999999998, 55.00999999999998,
                  49.72498981881871, 50.86540903238716)

    hf298k_1 = thermp_io.reader.hf298k(OUT_STR1)
    assert numpy.allclose(hf298k_1, ref_hf298k)

    hf298k_2 = thermp_io.reader.hf298k(OUT_STR2)
    assert hf298k_2 is None


if __name__ == '__main__':
    test__hf298k()