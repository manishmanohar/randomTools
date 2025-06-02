import os
import csv
import ffmpeg
from datetime import datetime

source_folder = 'input_videos'
output_folder = 'converted_videos'
max_size_mb = 13.0  # Just below 15 to be safe
max_duration = 360  # seconds

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# List of input extensions to process
input_extensions = ['.mov', '.avi', '.mkv', '.flv', '.wmv', '.webm', '.mp4']

# CSV file for output details
csv_path = os.path.join(output_folder, 'converted_videos_info.csv')

def get_video_duration(path):
    try:
        probe = ffmpeg.probe(path)
        return float(probe['format']['duration'])
    except Exception:
        return max_duration

def get_file_size_mb(path):
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except Exception:
        return 0

# Create/open CSV file
with open(csv_path, 'w', newline='') as csvfile:
    csv_writer = csv.writer(csvfile)
    # Write header
    csv_writer.writerow(['Original Name', 'Converted Name', 'Size (MB)', 'Conversion Date'])

    # Process each file
    for filename in os.listdir(source_folder):
        if not any(filename.lower().endswith(ext) for ext in input_extensions):
            continue
            
        input_path = os.path.join(source_folder, filename)
        output_filename = f"{os.path.splitext(filename)[0]}.mp4"
        output_path = os.path.join(output_folder, output_filename)
        
        duration = min(get_video_duration(input_path), max_duration)
        
        # Conservative bitrate for <15MB: bitrate = (size_in_bits / duration)
        target_bitrate = int((max_size_mb * 8 * 1024 * 1024) / duration)
        
        print(f"🔄 Converting {filename} → {output_path}")
        print(f"⏱ Duration: {duration}s | 🎯 Target bitrate: {target_bitrate // 1000} kbps")
        
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    vcodec='h264_videotoolbox',
                    acodec='aac',
                    video_bitrate=target_bitrate,
                    audio_bitrate='50k',
                    vf='scale=360:-2',  # Enforce width of 640px (smaller = smaller size)
                    t=duration,         # Trim to max_duration
                    movflags='faststart'
                )
                .run(overwrite_output=True, quiet=True)
            )
            
            # Get the size of the converted file
            file_size = get_file_size_mb(output_path)
            
            # Write to CSV
            csv_writer.writerow([
                filename, 
                output_filename, 
                f"{file_size:.2f}", 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            
            print(f"✅ Done. Size: {file_size:.2f} MB")
            
        except ffmpeg.Error as e:
            print(f"❌ Failed: {e}")

print(f"📊 CSV report created at {csv_path}")

