from random import randint

__all__ = [
    "generate_groups",
]


def generate_groups(interval_size, max_value):
    groups = {1: (0, interval_size)}
    i = 2
    while groups[i - 1][1] != max_value:
        groups[i] = groups[i - 1][1], i * interval_size
        i += 1
    groups[i] = groups[i - 1][1], float("inf")
    return groups


def to_age_group(age, groups):
    """For a given age returns the corresponding age group.

    Args:
        age (float): agent's age.
        groups (Dict[int, Tuple[int, int]]): generated groups.
    """
    last = groups[len(groups)]
    interval = last[0] / len(groups)
    if age < last[0]:
        return age // interval + 1
    else:
        return last[0]


def random(age_group, groups, max_generated_age=100):
    """Generates a random age given an age group.

    Args:
        age_group (int): one age group defined in `AGE_GROUPS`.
        groups (Dict[int, Tuple[int, int]]): generated groups.
        max_generated_age (float):
            maximum possible value that can be generated.

    Returns:
        int: random age in range of the given age group.
    """
    age_min, age_max = groups[age_group]
    return randint(
        age_min,
        age_max if age_max != float("inf") else max_generated_age,
    )
