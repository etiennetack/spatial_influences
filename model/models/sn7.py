from math import pi
from abmlib import Model
from abmlib.influences import SlopeInfluence, DistanceInfluenceGPD
from abmlib.influences.functions import make_attraction_repulsion, make_open_distance
from agents.dwelling import Dwelling
from agents.landowner import LandOwner
from agents.road import Road

__all__ = ["SN7"]


class SN7(Model):
    AGENT_CLASSES = (LandOwner, Dwelling, Road)

    def post_init(self):
        self.change_influences(
            # Neighbours
            [10, 15, 20, 0.25]
            # Roads
            + [10, 15, 20, 0.25]
            # Slope
            + [0, pi / 4, 0.5]
        )

    def change_influences(self, P):
        self.set_influence(
            "HouseBuilding",
            [
                # Neighbours
                DistanceInfluenceGPD(
                    model=self,
                    target={"agent_class": Dwelling},
                    function=make_attraction_repulsion(P[0], P[1], P[2]),
                    weight=P[3],
                ),
                # Road influence
                DistanceInfluenceGPD(
                    model=self,
                    target={"agent_class": Road},
                    function=make_attraction_repulsion(P[4], P[5], P[6]),
                    weight=P[7],
                ),
                # Slope
                SlopeInfluence(
                    model=self,
                    function=make_open_distance(P[8], P[9]),
                    weight=P[10],
                    raster="topography",
                ),
            ],
        )
