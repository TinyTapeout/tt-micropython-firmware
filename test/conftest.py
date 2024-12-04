def pytest_addoption(parser):
    parser.addoption("--shuttle", action="store", default="shuttle of interest")
    parser.addoption("--shuttlepath", action="store", default="directory for shuttle files")

