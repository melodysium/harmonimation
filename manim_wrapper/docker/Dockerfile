FROM manimcommunity/manim:latest

# install some music latex packages
USER root
RUN tlmgr install musicography musixtex-fonts stackengine newunicodechar
RUN rm -f /usr/local/bin/python3 && ln -s /usr/bin/python3.11 /usr/local/bin/python3
USER ${NB_USER}

CMD [ "/bin/bash" ]
