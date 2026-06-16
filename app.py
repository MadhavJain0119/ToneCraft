from __future__ import annotations

import logging

import streamlit as st

from tonecraft import __version__
from tonecraft.config import settings
from tonecraft.exceptions import ToneCraftError
from tonecraft.generator import PostGenerator

logging.basicConfig(level=logging.INFO)


@st.cache_resource(show_spinner=False)
def get_generator() -> PostGenerator:
    return PostGenerator(cfg=settings)


def render() -> None:
    st.set_page_config(page_title="ToneCraft", page_icon="🪶", layout="centered")
    st.title("🪶 ToneCraft")
    st.caption("Draft posts that sound like *you* — powered by your own past writing.")

    try:
        generator = get_generator()
        topics = generator.library.topics()
    except ToneCraftError as exc:
        st.error(str(exc))
        st.stop()

    col_topic, col_length, col_language = st.columns(3)
    with col_topic:
        topic = st.selectbox("Topic", options=topics)
    with col_length:
        length = st.selectbox("Length", options=settings.length_buckets)
    with col_language:
        language = st.selectbox("Language", options=settings.supported_languages)

    if st.button("✨ Generate post", type="primary", use_container_width=True):
        with st.spinner("Crafting your post…"):
            try:
                post = generator.generate(topic=topic, length=length, language=language)
            except ToneCraftError as exc:
                st.error(str(exc))
            else:
                st.markdown("#### Generated post")
                st.write(post)
                st.download_button("Download as .txt", post, file_name="tonecraft_post.txt")

    st.caption(f"ToneCraft v{__version__} · {generator.library.size} posts in your style library")


if __name__ == "__main__":
    render()
