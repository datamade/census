import math
import warnings

# Aggregate Functions
def moe_of_sum(values, moes):
    warnings.warn('The calculation of the margin of error of a sum of variables assumes no covariance between variables. The Census does not provide data on covariance and suggests this method as an approximation. https://www.census.gov/content/d`am/Census/programs-surveys/acs/guidance/training-presentations/20170419_MOE.pdf')
    
    moe_sq = sum(moe**2 for value, moe in zip(values, moes) if value != 0)

    try:
        # If there are multiple zero values, Census advises to use
        # only the largest associated MOE,
        # https://www.census.gov/content/dam/Census/programs-surveys/acs/guidance/training-presentations/20170419_MOE.pdf, page 51
        moe_sq += max(moe for value, moe in zip(values, moes) if value == 0)**2
    except ValueError:
        pass

    return math.sqrt(moe_sq)
