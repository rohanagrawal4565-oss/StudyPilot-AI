import re
import requests
import streamlit as st
from collections import Counter
from urllib.parse import quote

# ---------------- PAGE SETTINGS ----------------

st.set_page_config(
    page_title="StudyPilot AI",
    page_icon="🎓",
    layout="wide"
)

# ---------------- BLUE-CYAN THEME ----------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #071426, #102b46);
    color: #f0f9ff;
}
h1, h2, h3 {
    color: #67e8f9 !important;
}
p, label, li {
    color: #e0f2fe;
}
div.stButton > button {
    background: linear-gradient(90deg, #0891b2, #2563eb);
    color: white;
    border: 0;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}
div.stButton > button:hover {
    border: 1px solid #67e8f9;
    color: white;
}
[data-testid="stMetric"] {
    background: #102b46;
    border: 1px solid #155e75;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------

st.title("🎓 StudyPilot AI")
st.subheader("Your Smart Research & Learning Companion")

st.markdown(
    "### One Topic. Multiple Sources. Smarter Learning."
)

st.write(
    "Explore educational topics, understand important ideas, "
    "discover reliable learning resources and test your knowledge."
)

st.divider()

# ---------------- EDUCATIONAL SOURCES ----------------

def get_sources(topic):
    q = quote(topic)
    return [
        {
            "name": "Wikipedia",
            "url": f"https://en.wikipedia.org/wiki/Special:Search?search={q}"
        },
        {
            "name": "Britannica",
            "url": f"https://www.britannica.com/search?query={q}"
        },
        {
            "name": "Khan Academy",
            "url": f"https://www.khanacademy.org/search?page_search_query={q}"
        },
        {
            "name": "NCERT",
            "url": "https://ncert.nic.in/"
        },
        {
            "name": "Google Scholar",
            "url": f"https://scholar.google.com/scholar?q={q}"
        }
    ]


# ---------------- RESEARCH SUMMARY ----------------

def research_topic(topic):
    search_url = (
        "https://en.wikipedia.org/w/api.php"
    )

    headers = {
        "User-Agent": "StudyPilotAI/1.0 EducationalProject"
    }

    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json",
        "srlimit": 1
    }

    response = requests.get(
        search_url,
        params=params,
        headers=headers,
        timeout=15
    )
    response.raise_for_status()

    results = response.json()["query"]["search"]

    if not results:
        return None

    title = results[0]["title"]

    summary_url = (
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + quote(title.replace(" ", "_"), safe="()_,-")
    )

    summary_response = requests.get(
        summary_url,
        headers=headers,
        timeout=15
    )
    summary_response.raise_for_status()

    data = summary_response.json()

    if data.get("type") == "disambiguation":
        return None

    extract = data.get("extract", "")

    if not extract:
        return None

    return {
        "title": data.get("title", title),
        "summary": extract,
        "page_url": data.get(
            "content_urls", {}
        ).get(
            "desktop", {}
        ).get(
            "page",
            "https://en.wikipedia.org/"
        )
    }


# ---------------- KEY TERMS ----------------

def extract_key_terms(text):
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())

    stop_words = {
        "this", "that", "with", "from", "have", "were",
        "their", "there", "which", "when", "where", "what",
        "about", "into", "than", "then", "them", "they",
        "these", "those", "been", "being", "also", "such",
        "some", "more", "most", "other", "only", "very",
        "will", "would", "could", "should", "does", "during",
        "between", "through", "because", "while", "each",
        "many", "much", "over", "under", "after", "before"
    }

    filtered = [
        word for word in words
        if word not in stop_words
    ]

    return Counter(filtered).most_common(8)


# ---------------- LOCAL TEXT SUMMARY ----------------

def summarize_text(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= 3:
        return text.strip()

    return " ".join(sentences[:3])


# ---------------- MAIN INPUT ----------------

st.markdown("## 🔎 Explore a Topic")

topic = st.text_input(
    "Enter a topic to research",
    placeholder="e.g. Artificial Intelligence, Photosynthesis..."
)

if st.button("🚀 Research Topic", use_container_width=True):
    if not topic.strip():
        st.warning("Please enter a topic first.")
    else:
        with st.spinner("Searching educational information..."):
            try:
                result = research_topic(topic.strip())

                if result:
                    st.session_state["research_result"] = result
                    st.session_state["research_topic"] = topic.strip()
                else:
                    st.session_state.pop("research_result", None)
                    st.warning(
                        "No suitable article found. Try a more specific topic."
                    )

            except requests.exceptions.Timeout:
                st.error("The request timed out. Please try again.")

            except requests.exceptions.RequestException:
                st.error(
                    "Could not connect to the research source. "
                    "Check your internet connection and try again."
                )

            except (KeyError, ValueError):
                st.error(
                    "The source returned unexpected information. "
                    "Please try again."
                )

# ---------------- DISPLAY RESULTS ----------------

if "research_result" in st.session_state:
    result = st.session_state["research_result"]
    research_text = result["summary"]

    st.divider()
    st.markdown("## 📚 Research Summary")

    st.markdown(f"### {result['title']}")
    st.write(research_text)

    st.caption(
        "Summary retrieved from Wikipedia. "
        "Verify important facts using additional educational sources."
    )

    st.markdown(
        f"**Original article:** [Read the full article]({result['page_url']})"
    )

    # Key terms
    st.markdown("## 🧠 Key Terms")

    terms = extract_key_terms(research_text)

    if terms:
        columns = st.columns(4)

        for index, (word, count) in enumerate(terms):
            with columns[index % 4]:
                st.metric(
                    label=word.title(),
                    value=count
                )
    else:
        st.info("Not enough text to identify key terms.")

    # Educational resources
    st.markdown("## 🌐 Educational Sources")

    current_topic = st.session_state["research_topic"]

    for source in get_sources(current_topic):
        st.markdown(
            f"- [{source['name']}]({source['url']})"
        )

    # Quiz
    st.divider()
    st.markdown("## 📝 Quick Knowledge Quiz")

    st.write(
        "Answer these questions to check your understanding "
        "of the research summary."
    )

    sentences = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", research_text)
        if len(s.split()) >= 7
    ]

    if sentences:
        quiz_sentences = sentences[:3]

        for index, sentence in enumerate(quiz_sentences):
            st.markdown(f"**Question {index + 1}**")
            st.write(sentence)

            options = [
                "True",
                "False"
            ]

            answer = st.radio(
                "Choose your answer:",
                options,
                key=f"quiz_{index}",
                horizontal=True
            )

        st.info(
            "Read the original research summary carefully "
            "and verify the statements against the source."
        )

        if st.button("📖 Review Answers"):
            for index, sentence in enumerate(quiz_sentences):
                st.write(f"**Question {index + 1}:** True")
                st.caption(
                    "This statement is taken directly from the "
                    "displayed research summary."
                )
    else:
        st.info(
            "This article is too short to create a quiz. "
            "Try another topic."
        )

# ---------------- STUDY NOTES ----------------

st.divider()
st.markdown("## ✍️ Personal Study Notes")

notes = st.text_area(
    "Write or paste your study material here",
    placeholder="Paste your notes to create a short revision summary...",
    height=150
)

if st.button("Create Revision Summary"):
    if notes.strip():
        st.markdown("### Your Revision Summary")
        st.write(summarize_text(notes))
        st.markdown("### Key Terms")

        for word, count in extract_key_terms(notes):
            st.write(f"- **{word.title()}** — appears {count} time(s)")
    else:
        st.warning("Please enter some notes first.")

# ---------------- FOOTER ----------------

st.divider()

st.caption(
    "StudyPilot AI | Learn Smarter. Research Better. "
    "Built as a Class 10 AI Hackathon project."
)

st.caption(
    "Educational prototype: always verify information "
    "with reliable textbooks and primary sources."
      )
