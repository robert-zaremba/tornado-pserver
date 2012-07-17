# content of conftest.py for pytest
import sys
import pytest


# If you have the xdist plugin installed you will now always perform test runs using a number of subprocesses close to your CPU.
def pytest_cmdline_preparse(args):
    args.append('-q')
    if False and 'xdist' in sys.modules: # pytest-xdist plugin
        import multiprocessing
        num = max(multiprocessing.cpu_count() / 2, 1)
        args[:] = ["-n", str(num)] + args


# --runslow command line option to control skipping of slow marked tests (decorated by @pytest.mark.slow)
# item is an function - test object
# more info at http://pytest.org/latest/funcargs.html
def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
        help="run slow tests")

def pytest_runtest_setup(item):
    if 'slow' in item.keywords and not item.config.getvalue("runslow"):
        pytest.skip("need --runslow option to run")

# Detect if running from within a py.test run, then in code (eg in logger you can check by: hasattr(sys, '_called_from_test'))
def pytest_configure(config):
    import sys
    sys._called_from_test = True

def pytest_unconfigure(config):
    del sys._called_from_test

# others:
#   http://pytest.org/latest/example/simple.html
#   --duration=num option  - prints time of 3 slowest tests
#   -rx == -report-on-xfail   print messages for xfails
#   --runxfail    force the running and reporting of an xfail marked test as if it weren't marked at all.
#   -rxs  # show extra info on skips and xfails
#   --runslow   - run slow tests
#   selecting tests:  http://pytest.org/latest/example/markers.html#using-k-text-to-select-tests
