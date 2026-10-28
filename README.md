# Cobra2D

![Python versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)
![Tests](https://github.com/Toepfer-Lab/Cobra2D/actions/workflows/test.yml/badge.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/Toepfer-Lab/Cobra2D)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Toepfer-Lab/Cobra2D)

Cobra2D is a Python package that extends COBRApy to automatically build time-resolved and/or multi-subsystem metabolic models from an existing model. It creates one context-specific submodel per time interval and subsystem, and connects these submodels with linker and/or transfer reactions. To account for the lengths of the time intervals and the sizes of the subsystems, it scales the stoichiometry of the linker and transfer reactions and the objective coefficients of each submodel. The bounds of all other reactions are not scaled. For details, see [Linker and transfer reactions](https://cobra2d.readthedocs.io/stable/transport.html#scaling). Cobra2D also provides a weighted pFBA function that takes the lengths of the time intervals and the sizes of the subsystems into account.

### General process

* Define time intervals and subsystems (e.g. cell types, tissues or organs). Each combination of a time interval and a subsystem forms a phase.
  * Set the lengths of the time intervals
  * Set the sizes of the subsystems
* Connect the phases
  * Define linker reactions (auxiliary reactions that connect consecutive time intervals and allow storage metabolites to be carried over from one time interval to the next)
  * Define transfer reactions (auxiliary reactions that connect subsystems and allow metabolites to be exchanged between them)
* Add context-specific constraints to individual phases
* Construct a new model that contains all context-specific submodels, their constraints and the reactions connecting them

Cobra2D not only simplifies this process, but also makes it easy to save the defined settings and share them with others.

### Quick start

Define the sub_models (subsystems) and time periods, connect the phases, and apply the resulting constraints to a COBRApy model:

```python
from cobra2d import Constraints
from cobra.io import load_model

model = load_model("textbook")

constraints = Constraints()
constraints.add_sub_models(["leaf", "root"], [2, 1])
constraints.add_time_slots(n_ranges=2, time=12)
constraints.add_linker_series("atp_c")
constraints.add_transfer_series("glc__D_e", ["leaf", "root"])

resolved_model = constraints.apply_to_model(model)
```

Constraints can also be saved as XML and shared:

```python
constraints.save_as_xml("constraints.xml")
restored = Constraints.load_from_xml("constraints.xml")
```

See the [constraints notebook](https://cobra2d.readthedocs.io/stable/examples/Constraints.html) for a complete introduction and [linkage and phases](https://cobra2d.readthedocs.io/stable/examples/LinkageAndPhases.html) for more advanced model construction.

### Examples

The documentation includes notebooks for [constraints](https://cobra2d.readthedocs.io/stable/examples/Constraints.html), [linkage and phases](https://cobra2d.readthedocs.io/stable/examples/LinkageAndPhases.html), and [visualization](https://cobra2d.readthedocs.io/stable/examples/Visualization/cytoscape.html). A sample XML configuration is available at [docs/source/examples/data/conf.xml](https://github.com/Toepfer-Lab/Cobra2D/blob/main/docs/source/examples/data/conf.xml).

### Visualization

The defined settings can also be visualized, either as an interactive graph or as a static image.

![Interactive Cytoscape visualization of Cobra2D constraints](https://raw.githubusercontent.com/Toepfer-Lab/Cobra2D/main/assets/media/ConInteractive.gif)

### Installation

After cloning the repository, the package can be installed into the current Python environment using pip:

```
git clone https://github.com/Toepfer-Lab/Cobra2D.git

cd Cobra2D

pip install .
```

The static GraphViz visualization (`Constraints.create_graph`) additionally requires the Graphviz system package. It is separate from the `graphviz` Python package and cannot be installed via pip; please refer to the [documentation of graphviz](https://graphviz.readthedocs.io/en/stable/manual.html).

### Development

Tests, linting, formatting and type checks all run through [tox](https://tox.wiki). The test matrix covers Python 3.9 to 3.13, but you do **not** need to build those interpreters yourself: we use the [tox-uv](https://github.com/tox-dev/tox-uv) plugin, which builds every environment with [uv](https://docs.astral.sh/uv/) and can supply the required CPython versions.

Setting up the same environment we use takes one command. With [uv installed](https://docs.astral.sh/uv/getting-started/installation/):

```
uv tool install tox --with tox-uv
```

Alternatively, if you prefer to keep tox in an existing environment, `pip install tox tox-uv` works as well.

Depending on how uv was installed, the interpreters may have to be fetched once manually:

```
uv python install 3.9 3.10 3.11 3.12 3.13
```

From the repository root you can then run:

```
tox                  # the full matrix: format, lint, types, and tests on 3.9-3.13
tox -e py312         # tests on a single version
tox -e format,lint   # black (check only) and flake8
tox -e types         # mypy
tox -e py310-req     # tests against the pinned requirements.txt
tox -e py312 -- -k linker    # arguments after -- are passed through to pytest
```

A few notes on the setup:

* `tox -e format` only reports diffs; it does not rewrite files. Run `black src/cobra2d/ tests/ --line-length=79` to actually apply the formatting.
* `py310-req` is the reproducibility check. It installs the pinned `requirements.txt` rather than resolving dependencies afresh. It is tied to Python 3.10 because the pins were generated with `pip-compile` under that version. The remaining environments install from `setup.cfg` and therefore test against current releases of cobra and its dependencies.
* Without tox-uv, tox falls back to `virtualenv` and expects to find `python3.9`, `python3.10`, … on your `PATH`; environments for versions it cannot find will fail. Add `--skip-missing-interpreters=true` if you deliberately want to run only the subset you have installed.
