from enum import StrEnum


class Goal(StrEnum):
    PERFORMANCE = "performance"
    MAINTENANCE = "maintenance"
    FAT_LOSS = "fat_loss"


class Intensity(StrEnum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
