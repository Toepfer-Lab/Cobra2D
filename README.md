![Generic badge](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue)
![Tests](https://github.com/Toepfer-Lab/model_duplication/actions/workflows/test.yml/badge.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/Toepfer-Lab/model_duplication)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Toepfer-Lab/model_duplication)

A Python package that extends the COBRApy package with functions to represent time periods and organs by copying the
original model for every organ time combination, which we refer to as phases. This way, different time ranges and
customizable volumes of organs can be defined. Furthermore, a new model can be created automatically based on the
specified organs and time periods for the simulation.

### General process:
* Define time ranges and organs
* Individualization of single Phases
    * Volume adjustment
    * Time frame adjustments
    * Defining linkers
    * Adding special constraints for individual phases
* Creation of a new model containing all phases with their associated constraints

For this process, this package provides functionalities to not only simplify this process, but also to easily save and
share the defined settings with other people.

### Possible usage of this package

There are two ways to use this package. Either you use the functions implemented in Python to define phases and
constraints or you create an XML file that can be read in and used to create a new model.

### Examples
Examples of the use of this package can be found in the examples folder. There are examples that demonstrate the
functions but also an XML file that shows how the parameters are stored.

### Visualization
The package also provides the possibility to get an overview of the created settings with the help of an animated or unanimated graphic.

<object data="../../assets/media/ConInteractive.gif" type="image/gif">
      <object data="https://github.com/Toepfer-Lab/model_duplication/blob/c42dfdac52524a93323e78e1f3d996aef5e01714/assets/media/ConInteractive.gif" type="image/gif">
        <img src="./assets/media/ConInteractive.gif" alt="ConInteractive.gif">
      </object>
</object>

### Installation
After cloning the repository, the package can be installed in the current Python environment using pip.
So, in a terminal, the package can be installed with the following commands.
```
git clone https://github.com/Toepfer-Lab/model_duplication

cd model_duplication

pip install .
```
