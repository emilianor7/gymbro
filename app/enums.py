from enum import Enum


class MuscleGroup(str, Enum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    FOREARMS = "forearms"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    ABDOMINALS = "abdominals"
    OBLIQUES = "obliques"
    LOWER_BACK = "lower_back"
    TRAPS = "traps"
    LATS = "lats"
    NECK = "neck"
    FULL_BODY = "full_body"
    CARDIO = "cardio"
    OTHER = "other"


class Equipment(str, Enum):
    BARBELL = "barbell"
    DUMBBELL = "dumbbell"
    MACHINE = "machine"
    CABLE = "cable"
    SMITH = "smith"
    BODYWEIGHT = "bodyweight"
    KETTLEBELL = "kettlebell"
    BAND = "band"
    PLATE = "plate"
    EZ_BAR = "ez_bar"
    TRX = "trx"
    OTHER = "other"


class SetType(str, Enum):
    NORMAL = "normal"
    WARMUP = "warmup"
    DROPSET = "dropset"
    FAILURE = "failure"
    REST_PAUSE = "rest_pause"


class WeightUnit(str, Enum):
    KG = "kg"
    LB = "lb"
