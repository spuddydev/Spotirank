# Spotirank
Streamlit applet for creating ranked spotify playlists

## Description
Uses Spotipy to get a spotify playlist and provides a GUI for ranking the songs from best to worsed based on an elo system.

## Getting Started
### Installation
```sh
git clone https://github.com/spuddydev/spotirank.git
cd spotirank
pip install requirements.txt
```
### Setting Up
Your spotify developer keys must be added to your environment variables before usage. First, make a [spotify developer account](https://developers.spotify.com/.) Go to the [dashboard](https://developer.spotify.com/dashboard), create an app and add your new ID and SECRET (ID and SECRET can be found on an app setting) to your environment variables.

### Usage
```sh
streamlit run app.py
```
That's it! This will open the streamlit app locally ([port 8501](http://localhost:8501) by default) 

## Authors
[spuddydev](https://github.com/spuddydev) (Harrison Lisle) 

## License
This project is licensed under the WTFPL License - see the LICENSE.md file for details