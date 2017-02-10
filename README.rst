How to install
==============

Install system packsages::

  sudo apt-get install git python3-dev libhunspell-dev antiword pandoc
  sudo apt-get build-dep python3-lxml

Create directory where all databot dependencies will be stored::

  mkdir databot && cd databot

Clone all dependencies (since databot is under development, it is not yet
packaged)::

  git clone https://github.com/sirex/gramtool.git
  git clone https://github.com/sirex/databot.git
  git clone https://github.com/sirex/databot-bots.git bots

Install databot and all its dependencies::

  pip install -e ./gramtool -e ./databot -e ./bots

Prepare data directory::

  cd bots && mkdir data
