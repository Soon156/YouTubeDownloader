import os
import re

from PyQt6.QtCore import QThread, pyqtSignal
from pydub import AudioSegment
from pytube import YouTube, Playlist

desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Output')
resolution_list = ['', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']


class DownloadThread(QThread):
    msg = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, url, output, mp3, index):
        super().__init__()
        self.url = url
        self.output = output
        self.music = mp3
        self.resolution = resolution_list[index]
        self.type = None
        self.video_stream = None
        self.total_videos = 0
        self.idx = 0

    def run(self):
        try:
            if self.url:
                self.msg.emit("Video URL: " + self.url)
                if not self.output:
                    self.msg.emit("Warning: No output folder is insert, output to Desktop/Output folder")
                    self.output = desktop_path
                if self.resolution:
                    self.msg.emit("Resolution: " + self.resolution)
                self.msg.emit("Output Folder: " + self.output)
                self.process_input()
            else:
                self.msg.emit("Please insert the video url...")
        except Exception as e:
            self.msg.emit("Error: " + str(e))

    def process_input(self):
        self.msg.emit("Retrieving info from YouTube...\n")

        if "playlist?list" in self.url:
            self.type = "playlist"
            # Create a Playlist object
            playlist = Playlist(self.url)

            # Print playlist details
            playlist_title = re.sub(r'[^a-zA-Z0-9\s]', '', playlist.title)
            self.total_videos = len(playlist.video_urls)
            self.msg.emit("\nPlaylist Title: " + playlist_title)
            self.msg.emit("Number of Videos in Playlist: " + str(self.total_videos))

            # Create output directory
            output_path = os.path.join(self.output, playlist_title)
            os.makedirs(output_path, exist_ok=True)

            # check is it mp3
            if self.music:
                # Download each video in the playlist
                for video_url in playlist.video_urls:
                    self.download_music(video_url, output_path)
            else:
                for video_url in playlist.video_urls:
                    self.download_video(video_url, output_path)
                    self.idx += 1

            self.msg.emit("\nAll download progress is complete")

        else:
            if self.music:
                self.download_music(self.url, self.output)
            else:
                self.download_video(self.url, self.output)
                self.idx += 1

    def playlist_callback(self, stream, chunk, remaining):
        # Calculate progress percentage
        progress_percentage = int(self.idx / self.total_videos * 100)
        self.progress.emit(int(progress_percentage))

    def progress_callback(self, stream, chunk, remaining):
        progress = (1 - remaining / self.video_stream.filesize) * 100
        self.progress.emit(int(progress))

    def download_video(self, video_url, output_path):
        # Create a YouTube object
        if self.type == "playlist":
            yt = YouTube(video_url, on_progress_callback=self.playlist_callback)
        else:
            yt = YouTube(video_url, on_progress_callback=self.progress_callback)

        # Get the highest resolution stream
        self.msg.emit("\nDownloading: " + yt.title)

        if self.resolution:
            video_stream = yt.streams.get_by_resolution(self.resolution)
            if video_stream:
                self.msg.emit("Resolution: " + video_stream.resolution)
            else:
                video_stream = yt.streams.get_highest_resolution()
                self.msg.emit("Target resolution to high, try to get the highest available resolution: " + video_stream.resolution)
        else:
            video_stream = yt.streams.get_highest_resolution()
            self.msg.emit("Resolution: " + video_stream.resolution)

        self.msg.emit("File Size: " + str(round(video_stream.filesize / (1024 * 1024), 2)) + "MB")

        # Download the video
        os.makedirs(output_path, exist_ok=True)
        self.video_stream = video_stream
        video_stream.download(output_path)
        self.msg.emit("\nDownload complete! Saved at " + output_path)

    def download_music(self, video_url, output_path):
        # Create a YouTube object
        if self.type == "playlist":
            yt = YouTube(video_url, on_progress_callback=self.playlist_callback)
        else:
            yt = YouTube(video_url, on_progress_callback=self.progress_callback)

        # Get the highest resolution audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()

        # Print video details
        self.msg.emit("\nDownloading audio: " + yt.title)
        self.msg.emit("File Size: " + str(round(audio_stream.filesize / (1024 * 1024), 2)) + "MB")

        # Download the audio
        audio_file = audio_stream.download(output_path)

        # Convert the audio to MP3
        audio = AudioSegment.from_file(audio_file)
        mp3_file = os.path.splitext(audio_file)[0] + ".mp3"
        audio.export(mp3_file, format="mp3")

        # Remove the original audio file
        os.remove(audio_file)
        self.msg.emit("\nDownload complete! MP3 saved as: " + mp3_file)
