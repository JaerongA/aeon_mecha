## Local set-up using Anaconda and conda

1) Install [Anaconda](https://www.anaconda.com/products/individual)
	- If prompted with an "Install for", select "Just Me" (instead of "All Users")
	- Ensure installation is in your home directory:
		- On Windows: `C:\Users\<your_username>\anaconda3`
		- On GNU/Linux: `/home/anaconda3`
		- On MacOS: `/Users/<your_name>/anaconda3`
	- Ensure you add anaconda3 as a path environment variable (even if it says this option is not recommended)
	- Ensure you do *not* register anaconda3 as the default version of Python.
	- _Note_: These installation settings can always be changed posthoc.

2) Create conda environment and install the code dependencies from the `env.yml` file:
```
conda update conda
conda init
conda env create --file env.yml
```

3) Using the virtual environment:

`conda activate aeon`: activates the virtual environment; any commands now run within this terminal will take place within the virtual environment.

`conda deactivate aeon`: deactivates the virtual environment.