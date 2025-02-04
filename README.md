# README

## Environment and Python dependencies

The Python environment is managed with pixi. It's a cross-platform package
management tool that install libraries and applications in a reproducible way
(using conda environments).

Please follow the instruction of pixi's documentation to install it
(https://pixi.sh/latest/).

Once pixi is installed you can initialize the conda environment and install the
dependencies with:

```bash
# cd into the project root directory
pixi install
```

## Run Genetic Algorithms

```bash
❯ pixi run learn --help
Usage: main.py [OPTIONS]

Options:
  --nprocess INTEGER  The number of process for parallelisation
  --nmaxgen INTEGER   The number of generations for the GA
  --psize INTEGER     The size of the populations of each generation
  --output TEXT       Path to the results save file
  --seed INTEGER      Random seed
  --measures TEXT     Names of the measures to fit
  --model TEXT        spacenet7 or valenicina
  --config TEXT       Simulation config file
  --help              Show this message and exit.
```

### Valenicina

```bash
# 1994--2002

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/valenicina/1994_2002 --measures chamfer_macro,density_mean --model valenicina --config model/config/valenicina/1994.toml

# 2002--2009

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/valenicina/2002_2009 --measures chamfer_macro,density_mean --model valenicina --config model/config/valenicina/2002.toml

# 2009--2019

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/valenicina/2009_2019 --measures chamfer_macro,density_mean --model valenicina --config model/config/valenicina/2009.toml

```

### SpaceNet 7 Data

```bash
# Cairo1

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1203E-1203N_4815_3378_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1203E-1203N_4815_3378_13/all.toml

# Cairo2

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1204E-1204N_4819_3372_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1204E-1204N_4819_3372_13/all.toml

# LA

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-0368E-1245N_1474_3210_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-0368E-1245N_1474_3210_13/all.toml

# London

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1025E-1366N_4102_2726_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1025E-1366N_4102_2726_13/all.toml

# NY

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-0577E-1243N_2309_3217_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-0577E-1243N_2309_3217_13/all.toml

# Santiago

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-0632E-0892N_2528_4620_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-0632E-0892N_2528_4620_13/all.toml

# Tripoli

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1138E-1216N_4553_3325_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1138E-1216N_4553_3325_13/all.toml

# Kuwait

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1296E-1198N_5184_3399_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1296E-1198N_5184_3399_13/all.toml
```

### Inputs / Outputs

- All model inputs are described inside the configuration files (`model/config/...`)
- At the end, the program exports the best solutions into `.parquet` files (readable with pandas as `DataFrames`)
- The output files are placed in a subfolder named with the random seed used by the program

Here is a truncated example for `X.parquet`, which contains the values of the learnt parameters:

```
|   | neighbours_l_min | neighbours_l_0 | neighbours_l_max | neighbours_w | ... | area_range_max |
|---|------------------|----------------|------------------|--------------|-----|----------------|
| 0 | 4.971014         | 85.943037      | 122.522782       | 0.040774     | ... | 37.171996      |
| 1 | 1.768529         | 83.524637      | 120.104298       | 0.040537     | ... | 37.171961      |
| 2 | 4.669140         | 85.623982      | 122.203518       | 0.048813     | ... | 32.911690      | 	
```
 	 	
`F.parquet` contains the associated values for each measure (fitness functions):

```
|   | chamfer_macro | density_mean |
|---|---------------|--------------| 	
| 0 | 435134.683511 | 10.285       |
| 1 | 425704.464531 | 10.380       |
| 2 | 433560.923462 | 10.365       |
```

## Compute Influence and Simulation Error

- To compute the influence error concatenate every `X` and `F` horizontally
- Then concatenate all of them into one `DataFrame` and save it

```python
from pathlib import Path
import pandas as pd

def read_results(basepath, measures, period):
    exp_results = []

    for dataset in (basepath / measures).iterdir():
        if dataset.name == "combined.parquet":
            continue
        period_dir = dataset / period
        if period_dir.exists():
            for exp in period_dir.iterdir():
                x = pd.read_parquet(exp / "X.parquet")
                f = pd.read_parquet(exp / "F.parquet")
                xf = pd.concat([x, f], axis=1)  # concat horizontally
                xf["dataset"] = dataset
                xf["exp"] = int(exp.name)
                exp_results.append(xf)

    # concat vertically
    combined_df = pd.concat(exp_results).reset_index(drop=True)

    return combined_df

results_folder = "./results"
results = read_results(results_folder, "CD", "all")
results.to_parquet(results_folder / "combined.parquet")
```
Finally, you can use the `calculate_influence_error` script to compute the influence error:

```bash
pixi run python scripts/calculate_influence_error.py
```
Check and adjust these variables inside the script (at the end):
- RESULTS_PATH: the path to the `combined.parquet` file
- OUTPUT_PATH: a new file retaking the `combined.parquet` file content with a new column indicating the influence error
- N_CPU: number of parallel processes to use

For the simulation error take again the `combined.parquet` file and run this script: `calculate_simulation_error`:

```bash
pixi run python scripts/calculate_simulation_error.py
```

Check again the end of the script and adjust.
