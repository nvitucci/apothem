### Create the environment

The project requires Python 3.

- Initialize virtual environment.

    :::bash
    python3 -m venv venv3
    source venv3/bin/activate
    pip install -r requirements.txt

- Run `pelican` in listen mode and autoreload.

    :::bash
    pelican -r -l

- (Optional) Redownload and install `alchemy` theme. 

    :::bash
    mkdir -p themes && cd themes
    git clone https://github.com/nairobilug/pelican-alchemy
    mv pelican-alchemy/alchemy/ .
    rm -rf pelican-alchemy/
    pelican-themes -i themes/alchemy/

