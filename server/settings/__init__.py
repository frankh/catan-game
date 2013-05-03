from .environment.development import *

environment = 'development'

from .global_settings import *

_temp = __import__('environment.'+environment, globals(), locals(), level=1)
_env_settings = getattr(_temp, environment)

for obj in [x for x in dir(_env_settings) if not x.startswith('_')]:
	globals()[obj] = getattr(_env_settings, obj)

del _temp
del _env_settings