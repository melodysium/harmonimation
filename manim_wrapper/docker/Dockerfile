FROM manimcommunity/manim:latest

# install some music latex packages
USER root
RUN tlmgr install musicography musixtex-fonts stackengine newunicodechar
USER ${NB_USER}

CMD [ "/bin/bash" ]
