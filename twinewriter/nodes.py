"""Node implementations for the TwineWriter workflow."""
import os
import re
from datetime import datetime
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from .models import TweetItem, AgentState


def input_node(state: AgentState) -> AgentState:
    """Receives and validates user input"""
    print("📥 INPUT NODE: Processing user request...")

    if not state.get("max_tweet_length"):
        state["max_tweet_length"] = 280

    if not state.get("tone"):
        state["tone"] = "professional"

    state["needs_revision"] = False
    state["approved"] = False
    state["error"] = ""

    print(f"   Topic: {state['topic']}")
    print(f"   Tone: {state['tone']}")
    print(f"   Max length: {state['max_tweet_length']} chars")

    return state


def content_generation_node(state: AgentState) -> AgentState:
    """Generate tweet content using LLM"""
    print("\n✍️  CONTENT GENERATION NODE: Drafting content...")

    # Use centralized LLM client
    try:
        from .llm import get_llm

        llm = get_llm()
        print("   Using configured LLM client")
    except Exception as e:
        state["error"] = f"LLM initialization failed: {str(e)}"
        return state

    # Build prompt
    system_prompt = f"""You are TwineWriter, an expert Twitter content creator.

Your task: Create engaging Twitter content based on the user's topic and desired tone.

GUIDELINES:
- Tone: {state['tone']}
- Write naturally and conversationally
- Use hooks that grab attention
- Include relevant emojis when appropriate
- Make it shareable and engaging
- If the content is complex, write it as a cohesive piece (we'll split it later if needed)

Topic: {state['topic']}

{f"Base content to expand on: {state['base_content']}" if state.get('base_content') else ""}

Generate the tweet content now. Write it as a single cohesive piece - don't worry about length."""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create engaging Twitter content about: {state['topic']}")
        ]

        response = llm.invoke(messages)
        state["raw_content"] = response.content.strip()

        print(f"   Generated {len(state['raw_content'])} characters")
        print(f"   Preview: {state['raw_content'][:100]}...")

    except Exception as e:
        state["error"] = f"Content generation failed: {str(e)}"

    return state


def length_checker_node(state: AgentState) -> AgentState:
    """Check if content fits in a single tweet"""
    print("\n📏 LENGTH CHECKER NODE: Analyzing content length...")

    max_length = state["max_tweet_length"]
    content_length = len(state["raw_content"]) if state.get("raw_content") else 0

    print(f"   Content length: {content_length} chars")
    print(f"   Max tweet length: {max_length} chars")

    if content_length <= max_length:
        # Single tweet
        state["tweets"] = [TweetItem(
            index=1,
            content=state["raw_content"],
            char_count=content_length
        )]
        print("   ✅ Fits in single tweet!")
    else:
        print("   ⚠️  Exceeds limit - will need thread splitting")
        state["tweets"] = []

    return state


def thread_splitter_node(state: AgentState) -> AgentState:
    """Split long content into logical thread"""
    print("\n✂️  THREAD SPLITTER NODE: Creating thread structure...")

    if state.get("tweets"):
        print("   Content already fits in single tweet, skipping.")
        return state

    content = state.get("raw_content", "")
    max_length = state.get("max_tweet_length", 280)

    # Reserve space for thread numbering (e.g., "1/5 ")
    reserve_chars = 6
    effective_max = max_length - reserve_chars

    # Split by sentences or logical breaks
    sentences = re.split(r'(?<=[.!?])\s+', content)

    tweets: List[str] = []
    current_tweet = ""

    for sentence in sentences:
        # If single sentence is too long, split by words
        if len(sentence) > effective_max:
            words = sentence.split()
            for word in words:
                if len(current_tweet) + len(word) + 1 <= effective_max:
                    current_tweet += (word + " ")
                else:
                    if current_tweet:
                        tweets.append(current_tweet.strip())
                    current_tweet = word + " "
        else:
            # Try to add sentence to current tweet
            if len(current_tweet) + len(sentence) + 1 <= effective_max:
                current_tweet += (sentence + " ")
            else:
                # Save current tweet and start new one
                if current_tweet:
                    tweets.append(current_tweet.strip())
                current_tweet = sentence + " "

    # Add remaining content
    if current_tweet.strip():
        tweets.append(current_tweet.strip())

    # Create TweetItems with numbering
    total_tweets = len(tweets)
    state["tweets"] = [
        TweetItem(
            index=i + 1,
            content=f"{i+1}/{total_tweets} {tweet}",
            char_count=len(f"{i+1}/{total_tweets} {tweet}")
        )
        for i, tweet in enumerate(tweets)
    ]

    print(f"   ✅ Split into {total_tweets} tweets")
    for tweet in state["tweets"]:
        print(f"      {tweet}")

    return state


def human_review_node(state: AgentState) -> AgentState:
    """Human-in-the-loop review and approval"""
    print("\n👤 HUMAN REVIEW NODE: Awaiting human feedback...")
    print("\n" + "=" * 70)
    print("GENERATED CONTENT:")
    print("=" * 70)

    for tweet in state.get("tweets", []):
        print(f"\n{tweet}")

    print("\n" + "=" * 70)
    print("\nOPTIONS:")
    print("  [a] Approve and finalize")
    print("  [e] Edit a specific tweet")
    print("  [r] Request complete revision with feedback")
    print("  [q] Quit without saving")
    print("=" * 70)

    choice = input("\nYour choice: ").strip().lower()

    if choice == 'a':
        state["approved"] = True
        state["needs_revision"] = False
        print("✅ Content approved!")

    elif choice == 'e':
        try:
            tweet_num = int(input("Which tweet # to edit? "))
        except Exception:
            print("Invalid number")
            return state

        if 1 <= tweet_num <= len(state.get("tweets", [])):
            new_content = input(f"Enter new content for tweet {tweet_num}: ").strip()

            # Update the tweet
            tweet_item = state["tweets"][tweet_num - 1]

            # Preserve numbering if it's a thread
            if len(state["tweets"]) > 1:
                prefix = f"{tweet_num}/{len(state['tweets'])} "
                new_content = prefix + new_content

            state["tweets"][tweet_num - 1] = TweetItem(
                index=tweet_num,
                content=new_content,
                char_count=len(new_content)
            )

            print(f"✅ Tweet {tweet_num} updated!")
            # Loop back for another review
            state["needs_revision"] = False
            state["approved"] = False
        else:
            print("Invalid tweet number!")
            state["needs_revision"] = False
            state["approved"] = False

    elif choice == 'r':
        feedback = input("Enter your feedback for revision: ").strip()
        state["human_feedback"] = feedback
        state["needs_revision"] = True
        state["approved"] = False
        print("🔄 Requesting revision...")

    elif choice == 'q':
        state["error"] = "User cancelled"
        print("❌ Cancelled by user")

    else:
        print("Invalid choice, please review again.")
        state["needs_revision"] = False
        state["approved"] = False

    return state


def revision_node(state: AgentState) -> AgentState:
    """Revise content based on human feedback"""
    print("\n🔄 REVISION NODE: Revising content based on feedback...")

    try:
        from .llm import get_llm

        llm = get_llm()
    except Exception as e:
        state["error"] = f"LLM initialization failed: {str(e)}"
        return state

    current_content = "\n\n".join([t.content for t in state.get("tweets", [])])

    system_prompt = f"""You are TwineWriter. The user has reviewed your content and wants revisions.

ORIGINAL CONTENT:
{current_content}

USER FEEDBACK:
{state.get('human_feedback','')}

Please revise the content according to the feedback while maintaining:
- Tone: {state.get('tone')}
- Topic: {state.get('topic')}
- Engaging and shareable style

Generate the REVISED content as a single cohesive piece."""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content="Revise the content based on the feedback.")
        ]

        response = llm.invoke(messages)
        state["raw_content"] = response.content.strip()

        # Reset tweets to force re-processing
        state["tweets"] = []
        state["needs_revision"] = False

        print(f"   ✅ Content revised ({len(state['raw_content'])} chars)")

    except Exception as e:
        state["error"] = f"Revision failed: {str(e)}"

    return state


def finalizer_node(state: AgentState) -> AgentState:
    """Create final JSON output"""
    print("\n🎯 FINALIZER NODE: Preparing final output...")

    state["final_json"] = {
        "status": "approved",
        "timestamp": datetime.now().isoformat(),
        "topic": state.get("topic"),
        "tone": state.get("tone"),
        "thread": [
            {
                "index": tweet.index,
                "content": tweet.content,
                "char_count": tweet.char_count,
            }
            for tweet in state.get("tweets", [])
        ],
        "total_tweets": len(state.get("tweets", [])),
        "is_thread": len(state.get("tweets", [])) > 1,
    }

    print("   ✅ Final JSON ready!")
    print(f"   Total tweets: {len(state.get('tweets', []))}")

    return state
