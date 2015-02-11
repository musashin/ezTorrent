# ezTorrent
## Purpose and Usage 
Provides a command line interface to the torrent site t411: it permits complex searches.
For example
```python
  search avatar | cid 354 | grep S01E[4-5]
```
will search for torrent with the name 'avatar', in category ID 354 (the cat command return a list of categories), and filter the result with the S01E[4-5] regular expression.
Typing 'help' will return a full list of accepted commands!

The tool also acts as a 'bridge' with a transmission rpc client: the download command will automatically add search result to the download queue!

##Installation & Requirements
Python 2.7.X is required, the file 'requirement.txt' can be used to get pip to install required modules... have fun!

