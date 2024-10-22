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

## Run genetic algorithms

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

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1204E-1202N_4816_3380_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1204E-1202N_4816_3380_13/all.toml

# Cairo3

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1204E-1204N_4819_3372_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1204E-1204N_4819_3372_13/all.toml

# Kuwait

pixi run learn --nprocess <n_threads> --nmaxgen 300 --psize 50 --output results/CD/L15-1296E-1198N_5184_3399_13/all --measures chamfer_macro,density_mean --model spacenet7 --config model/config/sn7/L15-1296E-1198N_5184_3399_13/all.toml

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
