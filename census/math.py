import math
import warnings

# Aggregate Functions
def moe_of_sum(values, moes):
    """
    Approximates the margin of error of a sum of variables as the sum
    of margin of errors. This approximates neglects any covariance
    between variables
    """
    
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

def linear_percentile(data_list, percentile=0.5):
    """
    This is a python port of a formula by Steve Doig,
    Bob Hoyer and Meghan Hoyer.
    
    It estimates the percentile of grouped/range data, like we get
    from census age and income distributions (n number of
    people are between 5 and 10 years old).
    This function takes a list of data groups. Each item in the
    list should correspond to a range like:
        [
            [count of items in the range, base or lower bound],
        ]
    Here's a full example using age data from the census:
    >>> ages = [
    >>>     [216350, (0, 4)],  # Under 5 years
    >>>     [201692, (5, 9)],  # 5 to 9 years
    >>>     [211151, (10, 14)], # 10 to 14 years
    >>>     [204986, (15, 19)], # 15 to 19 years
    >>>     [200257, (20, 24)], # 20 to 24 years
    >>>     [439047, (25, 34)], # 25 to 34 years
    >>>     [459664, (35, 44)], # 35 to 44 years
    >>>     [424775, (45, 54)], # 45 to 54 years
    >>>     [163492, (55, 59)], # 55 to 59 years
    >>>     [127511, (60, 64)], # 60 to 64 years
    >>>     [169552, (65, 74)], # 65 to 74 years
    >>>     [113693, (75, 84)], # 75 to 84 years
    >>>     [44661, (85, float('inf'))],  # 85 years and over
    >>> ]
    >>> linear_percentile(ages)
    35.3
    And, finally, an explanation from Steve Doig on how this all
    works, using the above sample data:
    "The total population is 2,976,831, so the midpoint of the
    population is 2,976,831/2=1,488,416. That value falls into
    the 35 to 44 years range, which begins with 1,473,483 counted
    in ages 0-34. There are 459,664 people in the 35-44 range.
    The midpoint is 1,488,416-1,473,483 = 14,933 people into the
    range. As a decimal, it is 14,933/459,664 = 0.032 into the range.
    The 35-44 range is 10 years wide. 35+(0.032*10) = 35.3 years"
    """
    i, bin, counts = _bin_select(data_list, percentile)

    lower_bound, upper_bound = bin
    width = upper_bound - lower_bound
    bin_count = counts[i]
    less_than_bin = sum(counts[:i])
    proportion = percentile * sum(counts)
    
    return lower_bound + (proportion - less_than_bin)/bin_count * width

def pareto_percentile(data_list, percentile=0.5):
    """
    Interpolates a percentile value assuming that the data is drawn
    from a Pareto distribution. Good for income and other highly
    skewed distributions.
    """
    i, bin, counts = _bin_select(data_list, percentile)

    lower_bound, upper_bound = bin

    ratio_proportion = (percentile * sum(counts))/sum(counts[i:])
    ratio_overall = sum(counts[(i + 1):])/sum(counts[i:])
    ratio_bounds = upper_bound/lower_bound
        
    return lower_bound * math.exp((math.log(ratio_proportion) /
                                   math.log(ratio_overall)) *
                                  math.log(ratio_bounds))


def _bin_select(data_list, percentile):
    # First make sure our list is in ascending order
    data_list = sorted(data_list, key=lambda lst: lst[1])
    
    # Pull out our elements into separate lists to make
    # things clearer later on. Cast them as floats now 
    # to avoid possible coercion bugs later.
    counts, bins = list(zip(*data_list))

    total = sum(counts)
    # break early if we don't have data
    if not counts or total == 0:
        return 0

    # Find the group that has the percentile in it
    # Which will be the group at which the running sum of the 
    # counts is greater than percentile proportion of the total sum
    proportion = total * percentile
    running_sum = 0
    index = None

    for i, count in enumerate(counts):
        if running_sum + count >= proportion:
            index = i
            break
        running_sum += count
        
    return index, bins[i], counts
