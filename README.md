# harmonimation

A program for visualizing musical harmonic analysis.

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

![note circles render](resources/note_circles.gif)

### Rhythm Circle

![rhythm circle render](resources/rhythm_circle.gif)

## Upcoming

-   Documentation on the shell wrapper script
-   Early prototypes of some of the widgets from the below design

## Early design

![early design](resources/harmonimation-design-early_sketch.png)
