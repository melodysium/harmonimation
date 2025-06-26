# harmonimation

A program for visualizing music theory of a given song.

Discord: <https://discord.gg/bseuGuKaZg>

Inspiration ([<img src="https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg" alt="YouTube icon" width="60"/>](https://www.youtube.com/watch?v=1lkJTSdGLG8)):

[![John Coltrane - Giant Steps - Circle of Fifths Diagram](https://img.youtube.com/vi/1lkJTSdGLG8/0.jpg)](https://www.youtube.com/watch?v=1lkJTSdGLG8)

## Features

Currently, very few:

-   [Shell wrapper script](https://github.com/PikaBlue107/harmonimation/blob/main/manim_wrapper/manim)
    to simplify using the [manim docker image](https://docs.manim.community/en/stable/installation/docker.html)
    -   [custom Docker image](https://hub.docker.com/repository/docker/pikablue107/manim-music/general)
        extending the primary manim image with more LaTeX packages (for rendering music)
    -   I'm considering sharing this with the
        [Manim Community project](https://github.com/ManimCommunity/manim)
-   Note circles to show note and chord sequences
-   Rhythm circle to visualize beat patterns

## Demos

### Note Circles

![note circles render](<resources/note_circles - bo en.gif>)

[version with audio](https://youtu.be/G2AJBk6h4Jg)

### Rhythm Circle

![rhythm circle render](resources/rhythm_circle.gif)

## Upcoming

-   Documentation on the shell wrapper script
-   Early prototypes of some of the widgets from the below design

## Early design

![early design](resources/harmonimation-design-early_sketch.png)

## Local install

Not reliably proven, many need to fix your own setup issues.

Prerequisites:

1.  `ffmpeg`
    -   on mac, I've used `brew install ffmpeg`
1.  `uv`: <https://github.com/astral-sh/uv>

Installation steps:

1.  Clone this project
1.  Run `uv sync`
1.  Activate the `.venv` and/or select its interpreter in your IDE
1.  Install a LaTeX distro and the following packages on top of manim's guidance:
    `musicography musixtex-fonts stackengine newunicodechar`
    -   see <https://docs.manim.community/en/stable/installation/uv.html#step-2-optional-installing-latex>
    -   I tried to install `TinyTeX` on mac but I ran into issues with `dvisvgm` and missing files, do not recommend

Other issues:

-   On mac, I also needed to `brew install pkgconf` to get `pycairo` to install currectly during `uv sync`.
-   For some reason, I needed to manually make the `media/Tex` folder necessary for manim to create WIP LaTeX images.
