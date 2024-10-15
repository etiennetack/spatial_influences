# coding: utf-8
import random
from collections import namedtuple
from multiants import Parametter


class AnnualSettlements(Parametter):
    Type = namedtuple("AnnualSettlements", ["number", "max", "newcommer_months"])

    def init(self, agent, model, override=None):
        return self.reset()

    def reset(self):
        """Every year (january) reset the number of annual settlements.
        This must be called one time each month.
        """
        settlement_range = self.options.get("annual_settlements_range")
        # Randomize the number of new settlements per year given a range defined by the expert
        settlement_max = random.randint(*settlement_range)
        # Determine the month when each settlements will be created
        newcommer_months = [random.randint(1, 12) for _ in range(settlement_max)]
        return self.Type(0, settlement_max, newcommer_months)

    def update(self, agent, model, old):
        if model.time.current.month == 1:
            # print(model.time.current.month)
            return self.reset()
        else:
            return old
