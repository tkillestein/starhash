# StarHash

Generate unique, memorable, and deterministic names for astronomical objects.

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![ty](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ty/main/assets/badge/v0.json)](https://github.com/astral-sh/ty)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HEALPix](https://img.shields.io/badge/HEALPix-powered-blue)](https://healpix.jpl.nasa.gov/)

## Why?

Because modern astronomy is hard enough, without mixing up sequentially-generated object
names. Assigning memorable names to objects not only minimises the chance of triggering
precious telescope time on the wrong thing, but reduces cognitive load.

Every 3 arcsecond patch of sky now has a unique 3-word combination associated with it.

### Example

* Instead of `SN2024cld` or `ra=237.589792 dec=+18.93895`
* You get: `armrest-fraying-bullion`

## Installation

To avoid issues with dependencies, we recommend setting up a virtual environment using
your favourite package manager. Then:

```bash
pip install starhash
```

or with `uv`

```bash
uv add starhash
```

## Quickstart

StarHash ships a basic CLI for quick queries by default

```shell
starhash get-name-from-coord --ra=321.4214 --dec=-54.21231
```

```shell
starhash get-coord-from-name gathering-equinox-approach
```

## Development and contributing

```shell
git clone https://github.com/tkillestein/starhash.git
```

Then create the dev environment:

```shell
uv sync --all-groups --python>=3.11
```

Install the pre-commit hooks

```shell
pre-commit install
```

And you're ready to go!

Before committing any changes, run `pytest` to confirm that the hashing code still
satisfies the round-trip property.

## Citation

If you include StarHash in your favourite pipeline/broker/API, please cite:

```bibtex
@software{starhash,
  author = {Tom Killestein},
  title = {StarHash: Human-readable identifiers for astronomical coordinates},
  year = {2026},
  url = {https://github.com/tkillestein/starhash}
}
```