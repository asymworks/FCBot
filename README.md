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

## Configuration

FCBot is configured using YAML files. An example YAML file with all available options is shown below.

```yaml
fcbot:
    version: 1          # This is optional but must be set to 1 if provided
    log_level: "INFO"   # This accepts Python logging level strings (DEBUG, INFO, WARNING, ERROR, and CRITICAL)
    output_dir: "."     # All generated files are saved relative to this directory

outputs:
  - name: STEP Output               # The `name` key is optional and is used in all log messages to identify the step
    type: step                      # Currently `step`, `stl`, and `pdf` are supported output formats
    filename: part.step             # The output file name
    objects:                        # Specify which FreeCAD objects to include in the output
      - Part                        # This can be a list of object labels, as in this example

  - name: STL Output
    comment: Output a STL Mesh      # Comments can be provided and are output to the console before the step is run
    type: stl
    filename: part.stl
    objects:
      shapes: all                   # `objects` can also contain a mapping of `shapes: all` to export all solid bodies
                                    # Note that for STL outputs, only one object can be output at a time, but this can
                                    # still be useful for when the project only contains one solid body

  - name: PDF Drawing
    type: pdf
    filename: part.pdf
    objects:
      pages: all                    # Similar to `shapes: all`, `pages: all` will export all TechDraw Pages into a single
                                    # merged PDF file.

```