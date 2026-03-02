# Read the Docs setup (PoolParty + StateTracker)

This repo has two documentation builds. Create **two projects** on [Read the Docs](https://readthedocs.org), both pointing to this repository.

## 1. StateTracker docs

- **Project name:** e.g. `statetracker`
- **Repository:** this repo
- **Configuration file:** `statetracker/.readthedocs.yaml`

In the project’s **Admin → Advanced settings**, set **Configuration file** to:

```text
statetracker/.readthedocs.yaml
```

Paths in that config are relative to the **repository root**. If your repo root is the folder that contains `poolparty` and `statetracker`, leave the config as-is. If your repo root is one level up (e.g. `poolparty-statecounter-acordero`), set **Configuration file** to `poolparty-statetracker/statetracker/.readthedocs.yaml` and in `statetracker/.readthedocs.yaml` use:
- `path: poolparty-statetracker/statetracker`
- `sphinx.configuration: poolparty-statetracker/statetracker/docs/conf.py`

## 2. PoolParty docs

- **Project name:** e.g. `poolparty`
- **Repository:** this repo (same as above)
- **Configuration file:** `poolparty/.readthedocs.yaml`

In the project’s **Admin → Advanced settings**, set **Configuration file** to:

```text
poolparty/.readthedocs.yaml
```

If your repo root is one level up, use `poolparty-statetracker/poolparty/.readthedocs.yaml` and in `poolparty/.readthedocs.yaml` set:
- `path: poolparty-statetracker/poolparty`
- `sphinx.configuration: poolparty-statetracker/poolparty/docs/conf.py`

## Repo root = this folder (`poolparty-statetracker`)

If this directory is the repository root (the one that contains `poolparty` and `statetracker`), no path changes are needed. The YAML files are already set up for that layout.
