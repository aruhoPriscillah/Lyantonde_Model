NURSERY_CLASS_NAMES = {"baby", "nursery", "middle", "top"}
LOWER_PRIMARY_CLASS_NAMES = {
    "p1", "p 1", "primary 1", "primary one",
    "p2", "p 2", "primary 2", "primary two",
    "p3", "p 3", "primary 3", "primary three",
}
UPPER_PRIMARY_CLASS_NAMES = {
    "p4", "p 4", "primary 4", "primary four",
    "p5", "p 5", "primary 5", "primary five",
    "p6", "p 6", "primary 6", "primary six",
    "p7", "p 7", "primary 7", "primary seven",
}

NURSERY_SUBJECT_NAMES = (
    "Numbers",
    "English",
    "Reading",
    "Health Habits",
    "Social Development",
    "Drawing",
    "Writing",
)
LOWER_PRIMARY_SUBJECT_NAMES = (
    "Mathematics",
    "English",
    "Literacy I",
    "Literacy II (Reading)",
    "Religious Education",
    "Luganda",
)
UPPER_PRIMARY_SUBJECT_NAMES = ("Mathematics", "English", "SST", "Science")


def normalized_class_name(school_class):
    if not school_class:
        return ""
    normalized = " ".join(school_class.name.lower().replace("-", " ").split())
    if normalized.endswith(" class"):
        normalized = normalized[:-6].strip()
    return normalized


def is_nursery_class(school_class):
    return normalized_class_name(school_class) in NURSERY_CLASS_NAMES


def is_lower_primary_class(school_class):
    return normalized_class_name(school_class) in LOWER_PRIMARY_CLASS_NAMES


def is_upper_primary_class(school_class):
    return normalized_class_name(school_class) in UPPER_PRIMARY_CLASS_NAMES


def subject_names_for_class(school_class):
    if is_nursery_class(school_class):
        return NURSERY_SUBJECT_NAMES
    if is_lower_primary_class(school_class):
        return LOWER_PRIMARY_SUBJECT_NAMES
    if is_upper_primary_class(school_class):
        return UPPER_PRIMARY_SUBJECT_NAMES
    return None
