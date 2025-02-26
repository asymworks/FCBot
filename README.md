# FCBot

FCBot is a Python tool for automated generation of fabrication and documentation files from FreeCAD projects easily, repeatably, and scriptably. It can be used with a companion Docker image containing FreeCAD for CI/CD workflows. FCBot is inspired by the wonderful KiCad tool [KiBot](https://github.com/INTI-CMNB/KiBot).

Currently FCBot supports FreeCAD 1.0 running on Debian Testing using Python 3.13.

## Usage (Docker)

FCBot is available as a GitHub/Gitea Action, or can be used locally with Docker. To use it locally, the easiest method is to set up a helper script with the following contents, for example as `$HOME/fcbot.sh`:

```shell
$ cat ~/fcbot.sh
#!/bin/sh

docker run -ti --rm -v $PWD:/workspace ghcr.io/asymworks/fcbot $@
```

To use, execute the `fcbot.sh` script from the directory with the FreeCAD project and FCBot configuration file:

```shell
$ ~/fcbot.sh -c fcbot.yaml Project.FCStd
```
