from pathlib import Path
import rasterio as rio
import numpy as np


def save_image(name, influences_maps):
    slope, slope_profile = influences_maps["slope"]
    neighbours, _ = influences_maps["neighbours"]
    roads, _ = influences_maps["roads"]
    paths, _ = influences_maps["paths"]
    aggr, _ = influences_maps["aggr"]
    profile = slope_profile
    profile["count"] = 3
    profile["compress"] = "lzw"
    with rio.open(
        name,
        "w",
        **profile,
    ) as dst:
        aggr[aggr > -1] = 1
        dst.write(np.minimum(slope, aggr), 1)
        dst.write(np.minimum(neighbours, aggr), 2)
        dst.write(np.minimum(roads + paths, aggr), 3)


def read_image(path):
    with rio.open(path, "r", driver="GTiff") as dst:
        return dst.read(1), dst.profile


def read_images(data, results_dir):
    for exp in data:
        influences_maps = {k: read_image(v) for k, v in data[exp].items()}
        save_image(results_dir.joinpath(f"{exp}.tiff"), influences_maps)


def parse_influence_result_maps(basedir):
    data = {}
    for elem in basedir.iterdir():
        split = elem.name.split(".")
        if len(split) == 2 and split[1] == "tiff":
            split2 = split[0].split("-")
            if split2[-1] in ("slope", "neighbours", "roads", "paths"):
                code = "-".join(split2[:-1])
                if code not in data.keys():
                    data[code] = {}
                data[code][split2[-1]] = elem
            else:
                code = "-".join(split2)
                if code not in data.keys():
                    data[code] = {}
                data[code]["aggr"] = elem
    return data


if __name__ == "__main__":
    basedir = Path("results/bests/tiff")
    results_dir = Path("results/bests/colours")
    data = parse_influence_result_maps(basedir)
    for e in data:
        print(e, " ".join(data[e].keys()))
    read_images(data, results_dir)
