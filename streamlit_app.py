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

def get_available_transcript(video_id):
    try:
        # First try to get all available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            # If no English, get the first available transcript and translate it
            try:
                transcript = transcript_list.find_manually_created_transcript()
            except:
                transcript = transcript_list.find_generated_transcript()
            
            if transcript.language_code != 'en':
                transcript = transcript.translate('en')
        
        return transcript.fetch()
        
    except Exception as e:
        st.error(f"Error getting transcript: {str(e)}")
        st.info("This might be because:\n" +
                "1. The video doesn't have captions enabled\n" +
                "2. The captions are embedded in the video and not available as text\n" +
                "3. The video might be age-restricted or private")
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
                    transcript = get_available_transcript(video_id)
                    if transcript:
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
                st.info("If the error persists, try another video or check if the video has captions enabled.")
    else:
        st.warning("Please enter a YouTube URL")

st.markdown("---")
st.markdown("### Tips:")
st.markdown("- Make sure the video has closed captions enabled")
st.markdown("- If a video has auto-generated captions, those will work too")
st.markdown("- Works with non-English videos (will auto-translate to English)")