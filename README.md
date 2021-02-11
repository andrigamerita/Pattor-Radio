# Pattor Radio
## Goodies-packed pirate radio station on Linux

Pattor Radio is a combination of scripts, services, and apps, oriented to setting up and mantaining an advanced pirate radio station on Linux systems.
For now, this is tested only on the Raspberry Pi 3 with Raspberry Pi OS Buster 32-bit.

### What's there
- Support for .mp3, .oga, .ogg, .opus, .wav, .flac audio files
- Reading of info from an audio file such as artist, album, duration, and title
- Saving of program configurations on JSON-style files
- Playback modes and options
  - Shuffling a folder of songs (including subfolders) in random order
  - Possibility of customizing the replay chance percentage for shuffle (the chance for any song that has already been played to be played again)
- PiFM support for transmitting over FM radio frequencies
  - Changing of some of the default PiFM configuration options
  - Setting Radio Text based on song title

### What still needs to be done
- Play, pause, stop, skip, and custom playlists
- Streaming over HTTP (and Bluetooth?)
- WebUI for managing everything via HTTP
- Android and PC apps for managing simpler things and not necessarily via HTTP
- Support for multiple separate music folders
- Saving and loading of played songs list on file (used by the shuffle playing mode)
- (Down)loading of songs from YouTube
- Customization for all PiFM options
- Reloading of configurations at every cycle without program restart
- Probably much more

#### Optional and required third-party libraries and programs
- [PiFM (by mundeeplamport)](https://github.com/mundeeplamport/PiFM.git), to support transmission over FM
- [Python](https://www.python.org/), for the execution of all the main scripts
- [SoX - Sound eXchange](http://sox.sourceforge.net/), to support playback of many audio formats
- [libsox-fmt-mp3](https://packages.debian.org/search?keywords=libsox-fmt-mp3), to provide SoX with MP3 support
- [tinytag (by devsnd)](https://github.com/devsnd/tinytag), to get informations from audio files
