from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

# Define the path to the video
video_path = "uploads/001.mp4"

# Define the output path for the cut video
output_path = "uploads/cut_001.mp4"

# Define the start and end times for the cut
start_time = 2
end_time = 4 

# Use ffmpeg to cut the video
ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=output_path)

print(f"Cut video saved as {output_path}")
