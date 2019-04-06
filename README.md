### Create the environment

The project requires Python 3.

- Initialize virtual environment.

        python3 -m venv venv3
        source venv3/bin/activate
        pip install -r requirements.txt

- Run `pelican` in listen mode and autoreload.

        pelican -r -l

- (Optional) Redownload and install `alchemy` theme. 

        mkdir -p themes && cd themes
        git clone https://github.com/nairobilug/pelican-alchemy
        mv pelican-alchemy/alchemy/ .
        rm -rf pelican-alchemy/
        pelican-themes -i themes/alchemy/

