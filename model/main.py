# coding: utf-8
import sys

sys.path.append(".")

from abmlib.cli import create_cli
from models.sn7 import SN7
from models.valenicina import Valenicina

if __name__ == "__main__":
    create_cli(
        {"valenicina": Valenicina, "spacenet7": SN7},
        default_model="spacenet7",
        default_config="model/config/sn7/L15-0331E-1257N_1327_3160_13/2018-01.toml",
        default_host="127.0.0.1",
        default_port=8884,
    )()
