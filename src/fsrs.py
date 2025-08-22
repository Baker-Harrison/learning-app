import math

class FSRS:
    def __init__(self, w):
        self.w = w

    def initial_stability(self, g):
        return self.w[g - 1]

    def initial_difficulty(self, g):
        return self.w[4] - (g - 3) * self.w[5]

    def new_difficulty(self, d, g):
        d0_3 = self.initial_difficulty(3)
        return self.w[7] * d0_3 + (1 - self.w[7]) * (d - self.w[6] * (g - 3))

    def retrievability(self, t, s):
        return (1 + t / (9 * s)) ** -1

    def new_stability(self, d, s, r, g):
        if g == 1: # Again
            return self.w[11] * d ** -self.w[12] * ((s + 1) ** self.w[13] - 1) * math.exp(self.w[14] * (1 - r))
        else: # Hard, Good, Easy
            hard_penalty = self.w[15] if g == 2 else 1
            easy_bonus = self.w[16] if g == 4 else 1
            return s * (1 + math.exp(self.w[8]) *
                               (11 - d) *
                               s ** -self.w[9] *
                               (math.exp((1 - r) * self.w[10]) - 1) *
                               hard_penalty *
                               easy_bonus)

# Default parameters for FSRS-4.5
# Using FSRS-4.5 as it is a more recent version with better performance
# https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
default_params = [0.4872, 1.4003, 3.7145, 13.8206, 5.1618, 1.2298, 0.8975, 0.031, 1.6474, 0.1367, 1.0461, 2.1072, 0.0793, 0.3246, 1.587, 0.2272, 2.8755]
