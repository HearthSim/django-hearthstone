try:
	from importlib.metadata import version

	__version__ = version("django-hearthstone")
except ImportError:
	import pkg_resources

	__version__ = pkg_resources.require("django-hearthstone")[0].version
