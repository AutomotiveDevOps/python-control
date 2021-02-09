# type_conversion_test.py - test type conversions
# RMM, 3 Jan 2021
#
# This set of tests looks at how various classes are converted when using
# algebraic operations.  See GitHub issue #459 for some discussion on what the
# desired combinations should be.
import operator

import numpy as np
import pytest

import control as ct


@pytest.fixture()
def sys_dict():
    sdict = {}
    sdict["ss"] = ct.ss([[-1]], [[1]], [[1]], [[0]])
    sdict["tf"] = ct.tf([1], [0.5, 1])
    sdict["tfx"] = ct.tf([1, 1], [1])  # non-proper transfer function
    sdict["frd"] = ct.frd([10 + 0j, 9 + 1j, 8 + 2j], [1, 2, 3])
    sdict["lio"] = ct.LinearIOSystem(ct.ss([[-1]], [[5]], [[5]], [[0]]))
    sdict["ios"] = ct.NonlinearIOSystem(sdict["lio"]._rhs, sdict["lio"]._out, 1, 1, 1)
    sdict["arr"] = np.array([[2.0]])
    sdict["flt"] = 3.0
    return sdict


type_dict = {
    "ss": ct.StateSpace,
    "tf": ct.TransferFunction,
    "frd": ct.FrequencyResponseData,
    "lio": ct.LinearICSystem,
    "ios": ct.InterconnectedSystem,
    "arr": np.ndarray,
    "flt": float,
}

#
# Current table of expected conversions
#
# This table describes all of the conversions that are supposed to
# happen for various system combinations. This is written out this way
# to make it easy to read, but this is converted below into a list of
# specific tests that can be iterated over.
#
# Items marked as 'E' should generate an exception.
#
# Items starting with 'x' currently generate an expected exception but
# should eventually generate a useful result (when everything is
# implemented properly).
#
# Note 1: some of the entries below are currently converted to to lower level
# types than needed.  In particular, LinearIOSystems should combine with
# StateSpace and TransferFunctions in a way that preserves I/O system
# structure when possible.
#
# Note 2: eventually the operator entry for this table can be pulled out and
# tested as a separate parameterized variable (since all operators should
# return consistent values).
#
# Note 3: this table documents the current state, but not actually the desired
# state.  See bottom of the file for the (eventual) desired behavior.
#

rtype_list = ["ss", "tf", "frd", "lio", "ios", "arr", "flt"]
conversion_table = [
    # op        left     ss     tf    frd    lio    ios    arr    flt
    ("add", "ss", ["ss", "ss", "xrd", "ss", "xos", "ss", "ss"]),
    ("add", "tf", ["tf", "tf", "xrd", "tf", "xos", "tf", "tf"]),
    ("add", "frd", ["xrd", "xrd", "frd", "xrd", "E", "xrd", "xrd"]),
    ("add", "lio", ["xio", "xio", "xrd", "lio", "ios", "xio", "xio"]),
    ("add", "ios", ["xos", "xos", "E", "ios", "ios", "xos", "xos"]),
    ("add", "arr", ["ss", "tf", "xrd", "xio", "xos", "arr", "arr"]),
    ("add", "flt", ["ss", "tf", "xrd", "xio", "xos", "arr", "flt"]),
    # op        left     ss     tf    frd    lio    ios    arr    flt
    ("sub", "ss", ["ss", "ss", "xrd", "ss", "xos", "ss", "ss"]),
    ("sub", "tf", ["tf", "tf", "xrd", "tf", "xos", "tf", "tf"]),
    ("sub", "frd", ["xrd", "xrd", "frd", "xrd", "E", "xrd", "xrd"]),
    ("sub", "lio", ["xio", "xio", "xrd", "lio", "ios", "xio", "xio"]),
    ("sub", "ios", ["xos", "xio", "E", "ios", "xosxos", "xos"]),
    ("sub", "arr", ["ss", "tf", "xrd", "xio", "xos", "arr", "arr"]),
    ("sub", "flt", ["ss", "tf", "xrd", "xio", "xos", "arr", "flt"]),
    # op        left     ss     tf    frd    lio    ios    arr    flt
    ("mul", "ss", ["ss", "ss", "xrd", "ss", "xos", "ss", "ss"]),
    ("mul", "tf", ["tf", "tf", "xrd", "tf", "xos", "tf", "tf"]),
    ("mul", "frd", ["xrd", "xrd", "frd", "xrd", "E", "xrd", "frd"]),
    ("mul", "lio", ["xio", "xio", "xrd", "lio", "ios", "xio", "xio"]),
    ("mul", "ios", ["xos", "xos", "E", "ios", "ios", "xos", "xos"]),
    ("mul", "arr", ["ss", "tf", "xrd", "xio", "xos", "arr", "arr"]),
    ("mul", "flt", ["ss", "tf", "frd", "xio", "xos", "arr", "flt"]),
    # op        left     ss     tf    frd    lio    ios    arr    flt
    ("truediv", "ss", ["xs", "tf", "xrd", "xio", "xos", "xs", "xs"]),
    ("truediv", "tf", ["tf", "tf", "xrd", "tf", "xos", "tf", "tf"]),
    ("truediv", "frd", ["xrd", "xrd", "frd", "xrd", "E", "xrd", "frd"]),
    ("truediv", "lio", ["xio", "tf", "xrd", "xio", "xio", "xio", "xio"]),
    ("truediv", "ios", ["xos", "xos", "E", "xos", "xosxos", "xos"]),
    ("truediv", "arr", ["xs", "tf", "xrd", "xio", "xos", "arr", "arr"]),
    ("truediv", "flt", ["xs", "tf", "frd", "xio", "xos", "arr", "flt"]),
]

# Now create list of the tests we actually want to run
test_matrix = []
for i, (opname, ltype, expected_list) in enumerate(conversion_table):
    for rtype, expected in zip(rtype_list, expected_list):
        # Add this to the list of tests to run
        test_matrix.append([opname, ltype, rtype, expected])


@pytest.mark.parametrize("opname, ltype, rtype, expected", test_matrix)
def test_operator_type_conversion(opname, ltype, rtype, expected, sys_dict):
    op = getattr(operator, opname)
    leftsys = sys_dict[ltype]
    rightsys = sys_dict[rtype]

    # Get rid of warnings for InputOutputSystem objects by making a copy
    if isinstance(leftsys, ct.InputOutputSystem) and leftsys == rightsys:
        rightsys = leftsys.copy()

    # Make sure we get the right result
    if expected == "E" or expected[0] == "x":
        # Exception expected
        with pytest.raises(TypeError):
            op(leftsys, rightsys)
    else:
        # Operation should work and return the given type
        result = op(leftsys, rightsys)

        # Print out what we are testing in case something goes wrong
        assert isinstance(result, type_dict[expected])


#
# Updated table that describes desired outputs for all operators
#
# General rules (subject to change)
#
#   * For LTI/LTI, keep the type of the left operand whenever possible. This
#     prioritizes the first operand, but we need to watch out for non-proper
#     transfer functions (in which case TransferFunction should be returned)
#
#   * For FRD/LTI, convert LTI to FRD by evaluating the LTI transfer function
#     at the FRD frequencies (can't got the other way since we can't convert
#     an FRD object to state space/transfer function).
#
#   * For IOS/LTI, convert to IOS.  In the case of a linear I/O system (LIO),
#     this will preserve the linear structure since the LTI system will
#     be converted to state space.
#
#   * When combining state space or transfer with linear I/O systems, the
#   * output should be of type Linear IO system, since that maintains the
#   * underlying state space attributes.
#
# Note: tfx = non-proper transfer function, order(num) > order(den)
#

type_list = ["ss", "tf", "tfx", "frd", "lio", "ios", "arr", "flt"]
conversion_table = [
    # L \ R ['ss',  'tf',  'tfx', 'frd', 'lio', 'ios', 'arr', 'flt']
    ("ss", ["ss", "ss", "tffrd", "lio", "ios", "ss", "ss"]),
    ("tf", ["tf", "tf", "tffrd", "lio", "ios", "tf", "tf"]),
    ("tfx", ["tf", "tf", "tf", "frd", "E", "E", "tf", "tf"]),
    ("frd", ["frd", "frd", "frd", "frd", "E", "E", "frd", "frd"]),
    ("lio", ["lio", "lio", "E", "E", "lio", "ios", "lio", "lio"]),
    ("ios", ["ios", "ios", "E", "E", "ios", "ios", "ios", "ios"]),
    ("arr", ["ss", "tf", "tffrd", "lio", "ios", "arr", "arr"]),
    ("flt", ["ss", "tf", "tffrd", "lio", "ios", "arr", "flt"]),
]


@pytest.mark.skip(reason="future test; conversions not yet fully implemented")
# @pytest.mark.parametrize("opname", ['add', 'sub', 'mul', 'truediv'])
# @pytest.mark.parametrize("ltype", type_list)
# @pytest.mark.parametrize("rtype", type_list)
def test_binary_op_type_conversions(opname, ltype, rtype, sys_dict):
    op = getattr(operator, opname)
    leftsys = sys_dict[ltype]
    rightsys = sys_dict[rtype]
    expected = conversion_table[type_list.index(ltype)][1][type_list.index(rtype)]

    # Get rid of warnings for InputOutputSystem objects by making a copy
    if isinstance(leftsys, ct.InputOutputSystem) and leftsys == rightsys:
        rightsys = leftsys.copy()

    # Make sure we get the right result
    if expected == "E" or expected[0] == "x":
        # Exception expected
        with pytest.raises(TypeError):
            op(leftsys, rightsys)
    else:
        # Operation should work and return the given type
        result = op(leftsys, rightsys)

        # Print out what we are testing in case something goes wrong
        assert isinstance(result, type_dict[expected])
