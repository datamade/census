from census.core import (ALL, CensusException,
                         UnsupportedYearException, __version__)
try:
    import esridump, shapely
except ImportError:
    from census.core import Census
else:
    from census.geo import Census
    
