# Thesis Information Science

This repo stores everything that was used in creating my thesis project for Information Science.

## Install
### Python
You need Python 3.7+ and a valid install of pip.

The required libraries can be installed using: `pip install -r requirements.txt`

You also need to [download](https://spacy.io/usage/models#languages) a large spacy model (because word vectors work best in large models).

### Spotlight
For DBPedia Spotlight, you can locally host it or have an external link to an API endpoint. 
I recommend running it locally since this system hammers the end point with requests and an externally hosted
party might not appreciate that.

1. Download the Spotlight docker image [here](https://github.com/dbpedia-spotlight/spotlight-docker) (note: the language images do not exist anymore, just download the general `dbpedia/dbpedia-spotlight-tid` version)
2. Download a language model [here](https://sourceforge.net/projects/dbpedia-spotlight/files/2016-10/)
4. Create the image using the instructions from the Spotlight docker wiki on Github (point 1).
4. Run the docker container with the provided language model. I used the following commands (change to fit your config):
```
docker run -itd --restart unless-stopped -p 2232:80 dbpedia/spotlight-dutch spotlight.sh
```
4. Check the README in `support` to see if everything is correct there.
5. Run `main.py` with the path to the corpus.

## Validation
The server for the api is hosted at: [https://wpoelman.pythonanywhere.com/validation](https://wpoelman.pythonanywhere.com/validation)

The page for validation is hosted at: [https://wesselpoelman.nl/validation.html](https://wesselpoelman.nl/validation.html)

