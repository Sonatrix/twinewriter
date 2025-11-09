"""
Streamlit UI for TwineWriter - AI Twitter Content Agent
"""

import streamlit as st
import os
import time
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the core functionality from package modules
from twinewriter.models import AgentState, TweetItem

# Page config
st.set_page_config(
    page_title="TwineWriter - AI Twitter Agent",
    page_icon="🐦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    /* Beautiful header bar */
    .header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 12px 20px;
        border-radius: 10px;
        background: linear-gradient(90deg, #0ea5e9 0%, #60a5fa 50%, #7dd3fc 100%);
        color: #fff;
        box-shadow: 0 8px 30px rgba(14,165,233,0.18);
        margin-bottom: 1rem;
    }
    .header-left { display: flex; align-items: center; gap: 12px; }
    .logo-badge { width: 48px; height: 48px; border-radius: 10px; background: rgba(255,255,255,0.12); display:flex; align-items:center; justify-content:center; font-size:1.4rem; }
    .header-title { font-size: 1.3rem; font-weight: 800; margin: 0; }
    .header-sub { font-size: 0.85rem; opacity: 0.95; margin: 0; }
    .header-actions { display:flex; gap:8px; align-items:center; }
    .header-btn { background: rgba(255,255,255,0.12); color: #fff; border: 0; padding: 8px 12px; border-radius: 8px; cursor: pointer; font-weight:600; }
    .header-btn:hover { background: rgba(255,255,255,0.18); }
    .header-desc { text-align: center; color: #475569; font-size: 0.95rem; margin: 8px 0 18px 0; }
    .tweet-box {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #1DA1F2;
    }
    .tweet-number {
        color: #1DA1F2;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .char-count {
        color: #666;
        font-size: 0.85rem;
        text-align: right;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "generated_tweets" not in st.session_state:
    st.session_state.generated_tweets = []
if "final_json" not in st.session_state:
    st.session_state.final_json = None
if "generation_count" not in st.session_state:
    st.session_state.generation_count = 0
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "is_generating" not in st.session_state:
    st.session_state.is_generating = False
if "show_examples" not in st.session_state:
    st.session_state.show_examples = False
if "topic" not in st.session_state:
    st.session_state.topic = ""

# Header bar (beautiful)
import base64
import webbrowser

# Example topics for inspiration
example_topics = [
    "5 tips for effective time management in remote work",
    "The future of AI in healthcare: opportunities and challenges",
    "How to build a morning routine that sets you up for success",
    "Understanding blockchain technology: a beginner's guide",
    "Sustainable living: small changes with big environmental impact",
]

# Build logo data URI if a logo file exists in public/images/logo.png; fallback to emoji badge
logo_img_html = '<div class="logo-badge">🐦</div>'
try:
    logo_path = os.path.join(os.path.dirname(__file__), "public", "images", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        logo_img_html = f'<img src="data:image/png;base64,{encoded}" style="width:48px;height:48px;border-radius:10px;object-fit:cover;" />'
except Exception:
    # leave fallback badge
    pass

header_html = f"""
<div class="header-bar">
    <div class="header-left">
        {logo_img_html}
        <div>
            <div class="header-title">TwineWriter</div>
            <div class="header-sub">AI Twitter Content Agent • Auto-threading • Edit & Export</div>
        </div>
    </div>
</div>
"""

st.markdown(header_html, unsafe_allow_html=True)
st.markdown(
    '<div class="header-desc">Create concise, engaging tweets and threaded conversations using AI — enter a topic, pick a tone, and generate content you can edit and export.</div>',
    unsafe_allow_html=True,
)

# Main layout: left = inputs + info, right = results
col1, col2 = st.columns([1, 2])

with col1:
    # Input section
    st.header("📝 Content Settings")

    # LLM Configuration Section
    with st.expander("🤖 LLM Configuration", expanded=False):
        config_source = st.radio(
            "Configuration Source",
            options=["Use Environment Variables", "Configure via UI"],
            help="Choose whether to use .env file settings or configure directly in the UI"
        )
        
        if config_source == "Configure via UI":
            llm_provider = st.selectbox(
                "Select LLM Provider",
                options=["OpenAI", "Anthropic", "Ollama"],
                help="Choose which LLM provider to use for content generation"
            )
            
            if llm_provider == "OpenAI":
                openai_key = st.text_input(
                    "OpenAI API Key",
                    type="password",
                    help="Enter your OpenAI API key",
                    placeholder="sk-..."
                )
                if openai_key:
                    os.environ["OPENAI_API_KEY"] = openai_key
                    os.environ["ANTHROPIC_API_KEY"] = ""
                    os.environ["USE_OLLAMA"] = "false"
                    st.success("✅ OpenAI configured")
                else:
                    st.info("👆 Enter your OpenAI API key above")
                
            elif llm_provider == "Anthropic":
                anthropic_key = st.text_input(
                    "Anthropic API Key",
                    type="password",
                    help="Enter your Anthropic API key",
                    placeholder="sk-ant-..."
                )
                if anthropic_key:
                    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                    os.environ["OPENAI_API_KEY"] = ""
                    os.environ["USE_OLLAMA"] = "false"
                    st.success("✅ Anthropic configured")
                else:
                    st.info("👆 Enter your Anthropic API key above")
                    
            elif llm_provider == "Ollama":
                ollama_model = st.text_input(
                    "Ollama Model",
                    value="llama3.2",
                    help="Enter the Ollama model name (e.g., llama3.2, mistral)",
                    placeholder="llama3.2"
                )
                ollama_base_url = st.text_input(
                    "Ollama Base URL",
                    value="http://localhost:11434",
                    help="Ollama server URL",
                    placeholder="http://localhost:11434"
                )
                if ollama_model:
                    os.environ["USE_OLLAMA"] = "true"
                    os.environ["OLLAMA_MODEL"] = ollama_model
                    os.environ["OLLAMA_BASE_URL"] = ollama_base_url
                    os.environ["OPENAI_API_KEY"] = ""
                    os.environ["ANTHROPIC_API_KEY"] = ""
                    st.success(f"✅ Ollama configured with model: {ollama_model}")
        else:
            # Using environment variables
            st.info("📁 Using configuration from .env file")
            has_openai_env = os.getenv("OPENAI_API_KEY", "").lower() == "true"
            has_anthropic_env = os.getenv("ANTHROPIC_API_KEY", "").lower() == "true"
            use_ollama_env = os.getenv("USE_OLLAMA", "").lower() == "true"
            
            if has_openai_env:
                st.success("✅ OpenAI configured via environment")
            elif has_anthropic_env:
                st.success("✅ Anthropic configured via environment")
            elif use_ollama_env:
                model = os.getenv("OLLAMA_MODEL", "llama3.2")
                st.success(f"✅ Ollama configured via environment (model: {model})")
            else:
                st.warning("⚠️ No LLM configured in .env file")

    # Check LLM configuration status
    has_openai = os.getenv("OPENAI_API_KEY", "") != ""
    has_anthropic = os.getenv("ANTHROPIC_API_KEY", "") != ""
    use_ollama = os.getenv("USE_OLLAMA", "").lower() == "true"

    if not (has_openai or has_anthropic or use_ollama):
        st.warning("⚠️ Please configure an LLM provider above to generate content")

    st.divider()

    # Define callback for topic suggestion clicks
    def set_topic(suggestion):
        st.session_state.topic_input = suggestion

    # Input form
    topic = st.text_area(
        "Topic",
        placeholder="What do you want to tweet about?",
        help="Enter the main topic or subject for your tweet/thread",
        height=100,
        key="topic_input",
    )

    # Topic suggestions in a collapsible section
    with st.expander("💡 Need inspiration? Try these topics", expanded=False):
        suggestion_cols = st.columns(2)
        for i, topic_suggestion in enumerate(example_topics):
            with suggestion_cols[i % 2]:
                if st.button(
                    f"• {topic_suggestion}",
                    key=f"topic_{i}",
                    use_container_width=True,
                    on_click=set_topic,
                    args=(topic_suggestion,),
                ):
                    pass  # Button will update text via callback

    tone = st.selectbox(
        "Tone",
        options=[
            "professional",
            "educational",
            "witty",
            "marketing",
            "storytelling",
            "casual",
        ],
        help="Select the tone/style for your content",
    )

    base_content = st.text_area(
        "Base Content (Optional)",
        placeholder="Add any pre-written content to expand on...",
        help="Optional: Provide existing content that you want to enhance or expand",
        height=100,
    )

    max_tweet_length = st.slider(
        "Max Tweet Length",
        min_value=100,
        max_value=500,
        value=280,
        help="Maximum character count per tweet (Twitter limit is 280 for unverified accounts)",
    )

    st.divider()

    # Generate button with dynamic label and disabled state
    button_label = (
        "✨ Generating..." if st.session_state.is_generating else "✨ Generate Content"
    )
    generate_button = st.button(
        button_label,
        type="primary",
        disabled=st.session_state.is_generating,
        use_container_width=True,
    )

    # Show a subtle message when button is disabled
    if not topic:
        st.caption("👆 Enter a topic above to enable generation")
    elif st.session_state.is_generating:
        st.caption("⏳ Generation in progress...")

    st.divider()

    # Stats section
    st.markdown("### 📊 Stats")
    if st.session_state.generated_tweets:
        st.metric("Total Tweets", len(st.session_state.generated_tweets))
        st.metric("Generations", st.session_state.generation_count)

    st.divider()

    # Help section
    st.header("ℹ️ About")

    with st.expander("🎯 Features", expanded=True):
        st.markdown(
            """
        - **AI-Powered Generation**: Uses GPT-4 or Claude
        - **Smart Thread Splitting**: Auto-splits long content
        - **Multiple Tones**: Choose from 6 different styles
        - **Real-time Editing**: Edit any tweet before posting
        - **Character Counter**: Visual feedback for tweet length
        - **JSON Export**: Download for API integration
        """
        )

    with st.expander("📚 How to Use"):
        st.markdown(
            """
        1. **Enter Topic**: Describe what you want to tweet about
        2. **Select Tone**: Choose the style (professional, witty, etc.)
        3. **Generate**: Click "Generate Content"
        4. **Review**: Check the generated tweets
        5. **Edit**: Toggle edit mode to modify tweets
        6. **Approve**: Finalize or regenerate
        7. **Export**: Download as JSON for posting
        """
        )

    with st.expander("🎨 Tone Styles"):
        st.markdown(
            """
        - **Professional**: Formal, business-appropriate
        - **Educational**: Informative, teaching-focused
        - **Witty**: Clever, humorous, playful
        - **Marketing**: Promotional, persuasive
        - **Storytelling**: Narrative-driven
        - **Casual**: Conversational, friendly
        """
        )

with col2:
    # Results area header
    st.header("📱 Generated Content")

    # Process generation if button clicked
    if generate_button and topic:
        # Clear previous generated content
        st.session_state.generated_tweets = []
        st.session_state.final_json = None
        
        # mark generation as running to prevent duplicate clicks
        if not st.session_state.is_generating:
            st.session_state.is_generating = True

        # Add progress bar and status
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Show progress steps
            status_text.text("� Analyzing topic and tone...")
            progress_bar.progress(20)

            # Create initial state
            initial_state = {
                "topic": topic,
                "tone": tone,
                "base_content": base_content,
                "max_tweet_length": max_tweet_length,
                "raw_content": "",
                "tweets": [],
                "human_feedback": "",
                "needs_revision": False,
                "approved": False,
                "final_json": {},
                "error": "",
            }

            # Verify LLM is configured
            if not (
                os.getenv("OPENAI_API_KEY", "").lower() == "true"
                or os.getenv("ANTHROPIC_API_KEY", "").lower() == "true"
                or os.getenv("USE_OLLAMA", "").lower() == "true"
            ):
                st.error("⚠️ No LLM configured! Check your .env file")
                st.stop()

            # Create graph without human review node for Streamlit
            status_text.text("🎯 Creating generation pipeline...")
            progress_bar.progress(40)

            from langgraph.graph import StateGraph, END
            from twinewriter.nodes import (
                input_node,
                content_generation_node,
                length_checker_node,
                thread_splitter_node,
                finalizer_node,
            )

            workflow = StateGraph(AgentState)

            # Add nodes (excluding human review for automated flow)
            status_text.text("⚡ Setting up AI processing nodes...")
            progress_bar.progress(50)

            workflow.add_node("input", input_node)
            workflow.add_node("generate", content_generation_node)
            workflow.add_node("check_length", length_checker_node)
            workflow.add_node("split_thread", thread_splitter_node)
            workflow.add_node("finalize", finalizer_node)

            # Define edges
            workflow.set_entry_point("input")
            workflow.add_edge("input", "generate")
            workflow.add_edge("generate", "check_length")

            # Conditional edge for thread splitting
            def should_split(state):
                return "split_thread" if not state["tweets"] else "finalize"

            workflow.add_conditional_edges("check_length", should_split)
            workflow.add_edge("split_thread", "finalize")
            workflow.add_edge("finalize", END)

            # Compile and run
            status_text.text("🔨 Compiling workflow...")
            progress_bar.progress(70)

            from langgraph.checkpoint.memory import MemorySaver

            graph = workflow.compile(checkpointer=MemorySaver())

            status_text.text("🤖 Generating content with AI...")
            progress_bar.progress(80)

            config = {
                "configurable": {"thread_id": f"streamlit-{datetime.now().timestamp()}"}
            }

            # Create placeholder for streaming output
            stream_placeholder = st.empty()
            
            final_state = None
            current_node = ""
            
            # Stream the graph execution with live updates
            for state in graph.stream(initial_state, config):
                final_state = state
                node_name = list(state.keys())[0]
                node_state = state[node_name]
                
                # Update status based on current node
                if node_name != current_node:
                    current_node = node_name
                    if node_name == "input":
                        status_text.text("📥 Processing input...")
                    elif node_name == "generate":
                        status_text.text("✍️ Generating content...")
                    elif node_name == "check_length":
                        status_text.text("📏 Checking content length...")
                    elif node_name == "split_thread":
                        status_text.text("✂️ Splitting into thread...")
                    elif node_name == "finalize":
                        status_text.text("✨ Finalizing...")
                
                # Display intermediate content if available
                if node_state.get("raw_content"):
                    with stream_placeholder.container():
                        st.markdown("### 🔄 Live Preview")
                        st.info(f"**Raw Content:**\n\n{node_state['raw_content'][:500]}...")
                        
                if node_state.get("tweets"):
                    with stream_placeholder.container():
                        st.markdown("### 🔄 Generated Tweets")
                        for tweet in node_state["tweets"]:
                            st.markdown(f"**Tweet {tweet.index}:** {tweet.content}")
                            st.caption(f"Characters: {tweet.char_count}/280")

            status_text.text("✨ Finalizing output...")
            progress_bar.progress(90)

            # Extract final state
            if final_state:
                last_node = list(final_state.keys())[-1]
                final_state = final_state[last_node]

            if (
                final_state
                and final_state.get("tweets")
                and not final_state.get("error")
            ):
                st.session_state.generated_tweets = final_state["tweets"]
                st.session_state.generation_count += 1
                st.session_state.edit_mode = False
                progress_bar.progress(100)
                status_text.text("✅ Content generated successfully!")
                
                # Clear streaming placeholder and show success
                stream_placeholder.empty()
                st.success("✅ Content generated successfully!")
            else:
                error_msg = (
                    final_state.get("error", "Unknown error")
                    if final_state
                    else "No output generated"
                )
                progress_bar.progress(100)
                status_text.text("❌ Generation failed")
                stream_placeholder.empty()
                st.error(f"❌ Error: {error_msg}")

        except Exception as e:
            progress_bar.progress(100)
            status_text.text("❌ Error occurred")
            stream_placeholder.empty()
            st.error(f"❌ Error generating content: {str(e)}")
        finally:
            # clear the generating flag so button becomes active again
            st.session_state.is_generating = False
            # Clear progress indicators after a short delay
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

    # Display generated tweets
    if st.session_state.generated_tweets:
        # Edit mode toggle
        edit_col1, edit_col2 = st.columns([1, 4])
        with edit_col1:
            if st.button(
                "✏️ Edit Mode" if not st.session_state.edit_mode else "👁️ View Mode"
            ):
                st.session_state.edit_mode = not st.session_state.edit_mode

        st.divider()

        # Display tweets
        for idx, tweet in enumerate(st.session_state.generated_tweets):
            with st.container():
                st.markdown(f'<div class="tweet-box">', unsafe_allow_html=True)

                col_a, col_b = st.columns([4, 1])

                with col_a:
                    st.markdown(
                        f'<span class="tweet-number">Tweet {tweet.index}/{len(st.session_state.generated_tweets)}</span>',
                        unsafe_allow_html=True,
                    )

                with col_b:
                    char_color = "red" if tweet.char_count > 280 else "green"
                    st.markdown(
                        f'<div class="char-count" style="color: {char_color};">{tweet.char_count}/280</div>',
                        unsafe_allow_html=True,
                    )

                if st.session_state.edit_mode:
                    # Editable text area
                    edited_content = st.text_area(
                        f"Edit Tweet {tweet.index}",
                        value=tweet.content,
                        key=f"edit_{idx}",
                        height=100,
                        label_visibility="collapsed",
                    )

                    # Update button
                    if st.button(f"Update Tweet {tweet.index}", key=f"update_{idx}"):
                        st.session_state.generated_tweets[idx] = TweetItem(
                            index=tweet.index,
                            content=edited_content,
                            char_count=len(edited_content),
                        )
                        st.rerun()
                else:
                    # Display mode
                    st.markdown(f"<p>{tweet.content}</p>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

        st.divider()

        # Action buttons
        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button("🔄 Regenerate", type="secondary"):
                st.session_state.generated_tweets = []
                st.session_state.final_json = None
                st.rerun()

        with action_col2:
            if st.button("✅ Approve & Finalize", type="primary"):
                # Create final JSON
                st.session_state.final_json = {
                    "status": "approved",
                    "timestamp": datetime.now().isoformat(),
                    "topic": topic if "topic" in locals() else "N/A",
                    "tone": tone if "tone" in locals() else "N/A",
                    "thread": [
                        {
                            "index": tweet.index,
                            "content": tweet.content,
                            "char_count": tweet.char_count,
                        }
                        for tweet in st.session_state.generated_tweets
                    ],
                    "total_tweets": len(st.session_state.generated_tweets),
                    "is_thread": len(st.session_state.generated_tweets) > 1,
                }
                st.success("✅ Content approved and finalized!")
                st.balloons()

        with action_col3:
            # Download as JSON
            if st.session_state.generated_tweets:
                json_data = {
                    "timestamp": datetime.now().isoformat(),
                    "topic": topic if "topic" in locals() else "N/A",
                    "tone": tone if "tone" in locals() else "N/A",
                    "thread": [
                        {
                            "index": t.index,
                            "content": t.content,
                            "char_count": t.char_count,
                        }
                        for t in st.session_state.generated_tweets
                    ],
                }

                st.download_button(
                    label="💾 Download JSON",
                    data=json.dumps(json_data, indent=2),
                    file_name=f"twinewriter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

        # Display final JSON if available
        if st.session_state.final_json:
            st.header("📄 Final Output")
            st.json(st.session_state.final_json)

            st.download_button(
                label="💾 Download Final JSON",
                data=json.dumps(st.session_state.final_json, indent=2),
                file_name=f"twinewriter_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                type="primary",
            )

# Footer
st.divider()
st.markdown(
    """
<div style="text-align: center; color: #666; padding: 20px;">
    Built with ❤️ using <a href="https://langchain-ai.github.io/langgraph/" target="_blank">LangGraph</a>, 
    <a href="https://github.com/astral-sh/uv" target="_blank">uv</a>, and 
    <a href="https://streamlit.io" target="_blank">Streamlit</a>
</div>
""",
    unsafe_allow_html=True,
)
