import os
import cv2
import yt_dlp
import numpy as np

class FancyLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"default": "https://www.Fancy.com/watch?v=your_video_url", "label": "Video URL"})
            }
        }

    RETURN_TYPES = ("STRING",)  # Return type changed to STRING for video file path
    FUNCTION = "download_video"
    CATEGORY = "Custom Nodes"

    def download_video(self, url):
        try:
            output_path = './custom_nodes/ComfyUI-FancyLoader/downloads'
            os.makedirs(output_path, exist_ok=True)
            ydl_opts = {
                'format': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]/best[height<=2160]',
                'outtmpl': f'{output_path}/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
                'noplaylist': True,
            }

            video_path = None
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=True)
                    video_path = ydl.prepare_filename(info)
                except yt_dlp.DownloadError as e:
                    raise RuntimeError(f"Error downloading video: {e}")
                except Exception as e:
                    raise RuntimeError(f"Unexpected error: {e}")

            if not video_path or not os.path.exists(video_path):
                raise FileNotFoundError(f'Video file not found: {video_path}')

            batch_size = 100  
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            processed_frames = 0

            while processed_frames < frame_count:
                frames = []
                for _ in range(batch_size):
                    success, frame = cap.read()
                    if not success:
                        break
                    frames.append(frame)

                if frames:
                   
                	processed_frames += len(frames)

            cap.release()

            
            return (video_path,)

        except Exception as e:
            print(f'Error processing video: {e}')
            
            return ("Error: Unable to download video",)


NODE_CLASS_MAPPINGS = {"FancyLoader": FancyLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"FancyLoader": "Fancy Loader"}
