import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from transformers import pipeline
import re

st.set_page_config(page_title="YouTube Video Summarizer", page_icon="🎥")

st.title("YouTube Video Summarizer")
st.write("Get key points from any YouTube video that has closed captions!")

# URL input
url = st.text_input("Enter YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_summarizer()

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

if st.button("Get Key Points"):
    if url:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL")
        else:
            try:
                # Get transcript
                with st.spinner("Getting video transcript..."):
                    transcript = YouTubeTranscriptApi.get_transcript(video_id)
                    text = ' '.join([entry['text'] for entry in transcript])
                
                # Summarize
                with st.spinner("Analyzing video content..."):
                    # Split into chunks of 1000 characters
                    max_chunk = 1000
                    chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
                    
                    summaries = []
                    for chunk in chunks:
                        summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
                        summaries.append(summary[0]['summary_text'])
                
                st.success("Analysis complete! Here are the key points:")
                for i, summary in enumerate(summaries, 1):
                    st.markdown(f"**{i}.** {summary}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a YouTube URL")