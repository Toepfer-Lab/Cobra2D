![Generic badge](<https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue>)
![Tests](https://github.com/Toepfer-Lab/model_duplication/actions/workflows/test.yml/badge.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/Toepfer-Lab/model_duplication)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Toepfer-Lab/model_duplication)

Cobra2D is a Python package that extends COBRApy to automatically reconstruct time-resolved and/or multi-subsystem metabolic models. It generates context-specific submodels, adds linker and/or transfer reactions to connect them, and scales reactions to account for the lengths of the respective time intervals and the sizes of the subsystems. Cobra2D also provides a time interval- and subsystem size-aware weighted pFBA function.

### General process:

* Define time intervals (phases) and subsystems (e.g. cell types, tissues or organs)
* Contextualizing sub-models
  * Adjusting compartment sizes
  * Adjusting time intervals
  * Defining linker reactions (auxiliary reactions that connect phases and allow storage metabolites to be transferred across consecutive phases)
  * Defining transfer reactions (auxiliary reactions that connect subsystems and allow exchange metabolites to be transferred across subsystems)
  * Adding context-specific constraints to submodels
* Construction of a new model containing all context-specific submodels and  their respective constraints

For this process, this package provides functionalities to not only simplify this process, but also to easily save and
share the defined settings with other people.

### Use cases for this package

There are two ways to use this package: functions implemented in Python can be used to define phases and constraints directly, or an XML file can be created and read in to generate a new model.

### Examples

Examples of package usage can be found in the examples folder, including scripts that demonstrate the core functions and a sample XML file showing how parameters are stored. 

### Visualization

The package also provides the possibility to obtain an overview of the created settings via an animated or static graphic.

<object data="../../assets/media/ConInteractive.gif" type="image/gif">
      <object data="https://github.com/Toepfer-Lab/model_duplication/blob/c42dfdac52524a93323e78e1f3d996aef5e01714/assets/media/ConInteractive.gif" type="image/gif">
        <img src="./assets/media/ConInteractive.gif" alt="ConInteractive.gif">
      </object>
</object>

### Installation

After cloning the repository, the package can be installed in the current Python environment using pip. In a terminal, this can be done with the following commands: 

```
git clone https://github.com/Toepfer-Lab/model_duplication

cd model_duplication

pip install .
```

The static GraphViz visualization (`Constraints.create_graph`) additionally requires the Graphviz system package. It is separate from the `graphviz` Python package and cannot be installed via pip, please refer to the [documentation of graphviz](https://graphviz.readthedocs.io/en/stable/manual.html).

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

* `tox -e format` only reports diffs, it does not rewrite files. Run `black src/cobra2d/ tests/ --line-length=79` to actually apply the formatting.
* `py310-req` is the reproducibility check. It installs the pinned `requirements.txt` rather than resolving dependencies fresh, which is why it is tied to Python 3.10 — the pins were generated with `pip-compile` under that version. The remaining environments install from `setup.cfg` and therefore test against current releases of cobra and its dependencies.
* Without tox-uv, tox falls back to `virtualenv` and expects to find `python3.9`, `python3.10`, … on your `PATH`; environments for versions it cannot find will fail. Add `--skip-missing-interpreters=true` if you deliberately want to run only the subset you have installed.
