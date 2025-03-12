import os
import yt_dlp

class EasyUrlLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"default": "youtube.com/watch?v=your_video_url", "label": "Video URL"}),
                "download_full_video": ("BOOLEAN", {"default": True, "label": "Download Full Video"}),
                "download_audio": ("BOOLEAN", {"default": False, "label": "Keep Separate Audio"}),
                "download_video": ("BOOLEAN", {"default": False, "label": "Keep Separate Video"}),
                "full_output_dir": ("STRING", {"default": "", "label": "Full Video Output Directory (optional)"}),
                "audio_output_dir": ("STRING", {"default": "", "label": "Audio Output Directory (optional)"}),
                "video_output_dir": ("STRING", {"default": "", "label": "Video Output Directory (optional)"})
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("full_video_path", "audio_path", "video_path")
    FUNCTION = "download_video"
    CATEGORY = "Custom Nodes"

    def download_video(self, url, download_full_video=True, download_audio=False, download_video=False, 
                       full_output_dir="", audio_output_dir="", video_output_dir=""):
        try:
            # Set default base path
            default_base = './custom_nodes/comfyui-easyurlloader/downloads'

            # Determine output paths with fallbacks
            full_path = full_output_dir if (full_output_dir and os.path.isdir(full_output_dir)) else os.path.join(default_base, "full")
            audio_path = audio_output_dir if (audio_output_dir and os.path.isdir(audio_output_dir)) else os.path.join(default_base, "audio")
            video_path = video_output_dir if (video_output_dir and os.path.isdir(video_output_dir)) else os.path.join(default_base, "video")

            # Create directories if they don’t exist
            os.makedirs(full_path, exist_ok=True)
            os.makedirs(audio_path, exist_ok=True)
            os.makedirs(video_path, exist_ok=True)

            # Define download options
            full_opts = {
                'format': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]/best[height<=2160]',
                'outtmpl': f'{full_path}/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'noplaylist': True,
            }
            audio_opts = {
                'format': 'bestaudio',
                'outtmpl': f'{audio_path}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'noplaylist': True,
            }
            video_opts = {
                'format': 'bestvideo[height<=2160]',
                'outtmpl': f'{video_path}/%(title)s.%(ext)s',
                'noplaylist': True,
            }

            # Get video title
            with yt_dlp.YoutubeDL(full_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            title = info['title']

            # Initialize paths
            full_video_path = ""
            audio_file_path = ""
            video_file_path = ""

            # Download full video if requested
            if download_full_video:
                full_video_path = os.path.join(full_path, f"{title}.mp4")
                if not os.path.exists(full_video_path):
                    with yt_dlp.YoutubeDL(full_opts) as ydl:
                        ydl.download([url])
                else:
                    print(f"Full video already exists at: {full_video_path}")
            else:
                print("Full video download skipped.")

            # Download separate audio if requested
            if download_audio:
                audio_file_path = os.path.join(audio_path, f"{title}.mp3")
                if not os.path.exists(audio_file_path):
                    with yt_dlp.YoutubeDL(audio_opts) as ydl:
                        ydl.download([url])
                else:
                    print(f"Audio already exists at: {audio_file_path}")

            # Download separate video if requested
            if download_video:
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    info_video = ydl.extract_info(url, download=False)
                ext = info_video['ext']
                video_file_path = os.path.join(video_path, f"{title}.{ext}")
                if not os.path.exists(video_file_path):
                    with yt_dlp.YoutubeDL(video_opts) as ydl:
                        ydl.download([url])
                else:
                    print(f"Video already exists at: {video_file_path}")

            # Check full video only if it was supposed to be downloaded
            if download_full_video and not os.path.exists(full_video_path):
                raise FileNotFoundError(f'Full video file not found: {full_video_path}')

            return (full_video_path, audio_file_path, video_file_path)

        except Exception as e:
            print(f'Error processing video: {e}')
            return (f"Error: {str(e)}", "", "")

NODE_CLASS_MAPPINGS = {"EasyUrlLoader": EasyUrlLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"EasyUrlLoader": "EasyUrl Loader"}