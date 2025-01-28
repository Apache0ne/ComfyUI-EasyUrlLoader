# EasyUrlLoader
A simple YT downloader node for ComfyUI using video Urls. \
![image](https://github.com/user-attachments/assets/30501d79-6073-4653-8eaf-452ebc7fd719)\
Needed a faster way to download YT videos when using comfyUI and testing new tech. \
Will get the best resolution for the video so works great when running a video through a CN for a vid2vid pass.
## CONS & PROS
Cons\
User needs to go to downloads inside the custom node and see the FPS of downloaded videos\
User needs to do math when only wanting small parts of a YT video\
Only works for YT URLs for now\
Pros\
Faster than using other 3rd party downloaders and needing to trasnfer files around\
Will try to get 4k video compared to most other 3rd party downloaders only doing 1080.\
After download user can move YT video to other video editing APPS for cliping etc.\
For users will no ad block this makes getting YT videos easier
## Dependencies
'yt_dlp' py lib
'FFmpeg' non-py lib 
## Installation
ComfyUI-Manager (rec)\
Can be downloaded from ComfyUI-manager\
IF using Windows Port version\
ComfyUI Folder\
```pip install yt_dlp```\
Inside Custom_nodes Folder\
```git clone https://github.com/Apache0ne/ComfyUI-EasyUrlLoader.git ```\
IF using Matrix \
Inside venv\Scripts\
```activate```\
```pip install yt_dlp```\
Inside Custom_nodes Folder\
```git clone https://github.com/Apache0ne/ComfyUI-EasyUrlLoader.git ```\
##FFmpeg Installation\
Download pre-built package here based on OS(bottom middle left):
```https://ffmpeg.org/download.html#build-windows```\
Use ```7-Zip``` or another archive tool to extract the .7z file\
Locate the ```bin``` folder inside the extracted directory.\
Add it to your system's PATH\
In System Variables, find Path > Click Edit.\
Add the path to the bin folder, e.g., C:\ffmpeg\bin\
Test PATH in console : ```ffmpeg -version```\

