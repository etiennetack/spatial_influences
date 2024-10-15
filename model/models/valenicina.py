from multiants import Model
from multiants.influences import SlopeInfluence, DistanceInfluenceGPD
from multiants.influences.functions import make_attraction_repulsion, make_open_distance
from agents.dwelling import Dwelling
from agents.landowner import LandOwner
from agents.road import Road
from agents.road.parametters import Category as RoadCategory

__all__ = ["Valenicina"]


class Valenicina(Model):
    AGENT_CLASSES = (LandOwner, Dwelling, Road)

    def post_init(self):
        self.change_influences(
            [
                # Neighbours
                3.01467674e-03,
                2.54376982e00,
                7.36811442e00,
                2.48002587e-01,
                # Roads
                3.55418236e00,
                1.61499448e01,
                9.44629347e01,
                3.20056966e-01,
                # Paths
                3.12297177e00,
                2.39842909e01,
                2.94455378e-01,
                # Slopes
                5.21271948e-01,
                7.81326524e-01,
                1.37390528e-01,
            ]
        )

    def change_influences(self, P):
        self.set_influence(
            "HouseBuilding",
            [
                # Household influence
                DistanceInfluenceGPD(
                    model=self,
                    target={"agent_class": Dwelling},
                    function=make_attraction_repulsion(P[0], P[1], P[2]),
                    weight=P[3],
                ),
                # Road influence
                DistanceInfluenceGPD(
                    model=self,
                    target={
                        "agent_class": Road,
                        "filter": (
                            lambda params: params["category"] == RoadCategory.Type.ROAD
                            or params["category"] == RoadCategory.Type.SMALL_ROAD
                        ),
                    },
                    function=make_attraction_repulsion(P[4], P[5], P[6]),
                    weight=P[7],
                ),
                # Stepway influence
                DistanceInfluenceGPD(
                    model=self,
                    target={
                        "agent_class": Road,
                        "filter": (
                            lambda params: params["category"]
                            == RoadCategory.Type.STEPWAY
                            or params["category"] == RoadCategory.Type.PATH
                        ),
                    },
                    function=make_open_distance(P[8], P[9]),
                    weight=P[10],
                ),
                # Slope
                SlopeInfluence(
                    model=self,
                    raster="topography",
                    function=make_open_distance(P[11], P[12]),
                    weight=P[13],
                ),
            ],
        )
