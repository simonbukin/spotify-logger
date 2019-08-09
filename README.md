# Spotify Logger
A script for tracking Spotify play history. This script uses API polling to get what a user is currently playing and saves it into a Redis database for further processing.

For an explanation of how this project was done, [here](http://www.simonbukin.com/spotify/project/2019/08/03/logging-spotify.html) is a link

### Tools
-   [redis-py](https://github.com/andymccurdy/redis-py) Redis client in Python, used for storing listening history.
-   [requests](https://github.com/psf/requests) for sending requests to the Spotify API.
