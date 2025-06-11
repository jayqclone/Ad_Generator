import json
import os
import yt_dlp
from pathlib import Path
import requests
import hashlib

class VideoExtractor:
    def __init__(self):
        self.download_dir = Path("downloaded_videos")
        self.download_dir.mkdir(exist_ok=True)
        self.metadata_file = "extracted_videos.json"
        self.input_file = "scraped_ads.json"
    
    def setup_ytdl_options(self, output_path):
        return {
            'outtmpl': str(output_path / '%(title)s.%(ext)s'),
            'format': 'best[height<=720][ext=mp4]',
            'writeinfojson': False,
            'writedescription': False,
            'writesubtitles': False,
            'ignoreerrors': True,
            'no_warnings': True
        }
    
    def download_video(self, video_url, brand, ad_id):
        print(f"Attempting to download: {video_url}")
        safe_filename = f"{brand}_{ad_id}_{hashlib.md5(video_url.encode()).hexdigest()[:8]}"
        output_path = self.download_dir / safe_filename
        success = False
        local_file = None
        # Method 1: yt-dlp
        try:
            ydl_opts = self.setup_ytdl_options(self.download_dir)
            ydl_opts['outtmpl'] = str(self.download_dir / f"{safe_filename}.%(ext)s")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            for ext in ['mp4', 'mov', 'avi', 'webm']:
                potential_file = self.download_dir / f"{safe_filename}.{ext}"
                if potential_file.exists():
                    local_file = str(potential_file)
                    success = True
                    break
        except Exception as e:
            print(f"yt-dlp failed for {video_url}: {e}")
        # Method 2: Direct download
        if not success:
            try:
                response = requests.get(video_url, stream=True, timeout=30)
                print(f"Direct download HTTP status: {response.status_code}")
                if response.status_code == 200:
                    file_ext = 'mp4'
                    content_type = response.headers.get('content-type', '')
                    if 'video/webm' in content_type:
                        file_ext = 'webm'
                    elif 'video/mov' in content_type:
                        file_ext = 'mov'
                    local_file = str(self.download_dir / f"{safe_filename}.{file_ext}")
                    with open(local_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    success = True
                else:
                    print(f"Direct download failed for {video_url}: HTTP {response.status_code}")
            except Exception as e:
                print(f"Direct download exception for {video_url}: {e}")
        return local_file if success else None
    
    def extract_all_videos(self):
        with open(self.input_file, 'r') as f:
            ads_data = json.load(f)
        extracted_videos = []
        for i, ad in enumerate(ads_data):
            brand = ad.get('pageName') or ad.get('page_name') or 'Unknown'
            ad_id = ad.get('adArchiveId') or ad.get('ad_archive_id') or ad.get('id') or f"ad_{i}"
            video_hd_url = ad.get('videoHdUrl')
            video_sd_url = ad.get('videoSdUrl')
            print(f"Ad {i+1}/{len(ads_data)} | Brand: {brand} | videoHdUrl: {video_hd_url} | videoSdUrl: {video_sd_url}")
            video_url = video_hd_url or video_sd_url
            if not video_url:
                continue
            print(f"Processing video {i+1}/{len(ads_data)}: {brand}")
            local_file = self.download_video(video_url, brand, ad_id)
            if local_file:
                ad['local_file'] = local_file
                ad['file_size'] = os.path.getsize(local_file)
                extracted_videos.append(ad)
                print(f"✓ Downloaded: {local_file}")
            else:
                print(f"✗ Failed: {video_url}")
        with open(self.metadata_file, 'w') as f:
            json.dump(extracted_videos, f, indent=2)
        return extracted_videos

if __name__ == "__main__":
    extractor = VideoExtractor()
    videos = extractor.extract_all_videos()
    print(f"Successfully extracted {len(videos)} videos") 