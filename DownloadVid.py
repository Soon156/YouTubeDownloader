import os
import re
from datetime import datetime

from PyQt6.QtCore import QThread, pyqtSignal
from pydub import AudioSegment
from pytube import YouTube, Playlist

desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Output')
resolution_list = ['', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']


class DownloadThread(QThread):
    msg = pyqtSignal(str)
    progress = pyqtSignal(int)
    finish = pyqtSignal(int)

    def __init__(self, url, output, mp3, index):
        super().__init__()
        self.url = url
        self.output = output
        self.music = mp3
        self.resolution = resolution_list[index]
        self.type = None
        self.video_stream = None
        self.music_stream = None
        self.total_videos = 0
        self.playlist_file_size = 0
        self.downloaded_size = 0
        self.remaining_size = 0

    def run(self):
        try:
            if self.url and len(self.url) >= 1:
                if len(self.url) == 1:
                    self.msg.emit("Video URL: " + self.url[0])
                if not self.output:
                    self.msg.emit("Warning: No output folder is insert, output to Desktop/Output folder")
                    self.output = desktop_path
                if self.resolution:
                    self.msg.emit("Resolution: " + self.resolution)
                self.msg.emit("Output Folder: " + self.output)
                self.process_input()
                self.finish.emit(1)
            else:
                self.msg.emit("Please insert the video url...")
        except Exception as e:
            self.finish.emit(1)
            self.msg.emit("Error: " + str(e))

    def process_input(self):
        self.finish.emit(0)
        self.msg.emit("Retrieving info from YouTube...\n")

        if "playlist?list" in self.url[0] or len(self.url) > 1:
            playlist_title = str(datetime.now().strftime("%Y-%m-%d %H-%M-%S"))
            playlist = None
            if "playlist?list" in self.url[0]:
                self.type = "playlist"
                # Create a Playlist object
                playlist = Playlist(self.url[0])

                # Print playlist details
                playlist_title = re.sub(r'[^a-zA-Z0-9\s]', '', playlist.title)
                self.total_videos = len(playlist.video_urls)

                self.msg.emit("\nPlaylist Title: " + playlist_title)
                self.msg.emit("Number of Videos/Music in Playlist: " + str(self.total_videos))

            if len(self.url) > 1:
                self.type = "playlist"
                self.total_videos = len(self.url)
                self.msg.emit("Number of Videos/Music in Playlist: " + str(self.total_videos))

            # check is it mp3
            if self.music:
                # Create output directory
                output_path = os.path.join(self.output, playlist_title + ' MP3')
                os.makedirs(output_path, exist_ok=True)

                # Download each video in the playlist
                self.msg.emit("Getting playlist size...")

                if len(self.url) > 1:
                    for video_url in self.url:
                        self.get_file_size(video_url)
                    self.msg.emit("Downloading music list...")
                    for idx, video_url in enumerate(self.url):
                        self.msg.emit("\nMusic " + str(idx + 1) + ", " + str(self.total_videos - idx - 1) + " file left")
                        self.download_music(video_url, output_path)
                else:
                    for video_url in playlist.video_urls:
                        self.get_file_size(video_url)
                    self.msg.emit("Downloading music list...")
                    for idx, video_url in enumerate(playlist.video_urls):
                        self.msg.emit("\nMusic " + str(idx + 1) + ", " + str(self.total_videos - idx - 1) + " file left")
                        self.download_music(video_url, output_path)

            else:
                # Create output directory
                output_path = os.path.join(self.output, playlist_title)
                os.makedirs(output_path, exist_ok=True)

                self.msg.emit("Getting playlist size...")

                if len(self.url) > 1:
                    for video_url in self.url:
                        self.get_file_size(video_url)
                    self.msg.emit("Downloading video list...")
                    for idx, video_url in enumerate(self.url):
                        self.msg.emit("\nVideo " + str(idx + 1) + ", " + str(self.total_videos - idx - 1) + " file left")
                        self.download_video(video_url, output_path)
                else:
                    for video_url in playlist.video_urls:
                        self.get_file_size(video_url)
                    self.msg.emit("Downloading video list...")
                    for idx, video_url in enumerate(playlist.video_urls):
                        self.msg.emit("\nVideo " + str(idx + 1) + ", " + str(self.total_videos - idx - 1) + " file left")
                        self.download_video(video_url, output_path)

            self.msg.emit("\nAll download progress is complete")

        else:
            if self.music:
                self.download_music(self.url[0], self.output)
            else:
                self.download_video(self.url[0], self.output)
            self.msg.emit("\nDownload completed.")

    def playlist_callback(self, stream, chunk, remaining):
        if self.music:
            downloaded = self.music_stream.filesize - remaining
        else:
            downloaded = self.video_stream.filesize - remaining
        self.remaining_size = self.playlist_file_size - self.downloaded_size - downloaded
        progress_percentage = (1 - self.remaining_size / self.playlist_file_size) * 100
        self.progress.emit(int(progress_percentage))

    def progress_callback(self, stream, chunk, remaining):
        progress = (1 - remaining / self.video_stream.filesize) * 100
        self.progress.emit(int(progress))

    def music_callback(self, stream, chunk, remaining):
        progress = (1 - remaining / self.music_stream.filesize) * 100
        self.progress.emit(int(progress))

    def get_file_size(self, video_url):
        yt = YouTube(video_url)
        if self.music:
            audio_stream = yt.streams.filter(only_audio=True).first()
            self.playlist_file_size += audio_stream.filesize
        else:
            video_stream = self.check_resolution(yt, True)
            self.playlist_file_size += video_stream.filesize

    def check_resolution(self, yt, precheck=False):
        if self.resolution:
            video_stream = yt.streams.get_by_resolution(self.resolution)
            if video_stream:
                if not precheck:
                    self.msg.emit("Resolution: " + video_stream.resolution)
            else:
                video_stream = yt.streams.get_highest_resolution()
                if not precheck:
                    self.msg.emit(
                        "Target resolution to high, try to get the highest available resolution: " + video_stream.resolution)
        else:
            video_stream = yt.streams.get_highest_resolution()
        return video_stream

    def download_video(self, video_url, output_path):
        # Create a YouTube object
        if self.type == "playlist":
            yt = YouTube(video_url, on_progress_callback=self.playlist_callback)

        else:
            yt = YouTube(video_url, on_progress_callback=self.progress_callback)

        video_stream = self.check_resolution(yt)
        self.video_stream = video_stream

        # Get the highest resolution stream
        self.msg.emit("Downloading: " + yt.title)
        self.msg.emit("File Size: " + str(round(video_stream.filesize / (1024 * 1024), 2)) + "MB")

        # Download the video
        os.makedirs(output_path, exist_ok=True)
        video_stream.download(output_path)
        self.msg.emit("Video saved: " + output_path)
        self.downloaded_size += video_stream.filesize

    def download_music(self, video_url, output_path):
        # Create a YouTube object
        if self.type == "playlist":
            yt = YouTube(video_url, on_progress_callback=self.playlist_callback)
        else:
            yt = YouTube(video_url, on_progress_callback=self.music_callback)

        # Get the highest resolution audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        self.music_stream = audio_stream

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
        self.msg.emit("MP3 saved: " + mp3_file)

        self.downloaded_size += audio_stream.filesize