from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("working-memo")
except PackageNotFoundError:
    __version__ = "unknown"
