from pathlib import Path
import re

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "chroma_db"
DATA_DIR = BASE_DIR / "data"

DB_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CHROMA DATABASE
# ============================================================

client = chromadb.PersistentClient(
    path=str(DB_DIR)
)

collection = client.get_or_create_collection(
    name="college_knowledge",
    metadata={"hnsw:space": "cosine"},
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

_model = None


def model():

    global _model

    if _model is None:
        print("Loading AI embedding model...")
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )
        print("AI embedding model loaded.")

    return _model


# ============================================================
# SECTION PARSER
# ============================================================

def parse_sections(text):

    lines = text.splitlines()

    sections = []

    current_title = None
    current_content = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Detect section headings
        if (
            line.isupper()
            and len(line) < 80
            and not line.startswith(("-", "\u2022", "*", "\u2013"))
            and not line.startswith("1.")
            and not line.startswith("2.")
            and not line.startswith("3.")
            and not line.startswith("4.")
            and not line.startswith("5.")
            and not line.startswith("6.")
            and not line.startswith("7.")
            and not line.startswith("8.")
            and not line.startswith("9.")
        ):

            if current_title and current_content:

                sections.append(
                    (
                        current_title,
                        " ".join(current_content)
                    )
                )

            current_title = line
            current_content = []

        else:

            current_content.append(line)

    # Add final section

    if current_title and current_content:

        sections.append(
            (
                current_title,
                " ".join(current_content)
            )
        )

    return sections


# ============================================================
# LOAD COLLEGE KNOWLEDGE
# ============================================================

def load_college_knowledge():

    knowledge_file = (
        DATA_DIR / "college_knowledge.txt"
    )

    if not knowledge_file.exists():

        print(
            "ERROR: college_knowledge.txt not found."
        )

        return

    text = knowledge_file.read_text(
        encoding="utf-8"
    )

    sections = parse_sections(text)

    if not sections:

        print(
            "ERROR: No knowledge sections found."
        )

        return

    # Clear old collection data
    # so changes in the text file are reflected.
    existing = collection.get()

    if existing.get("ids"):

        collection.delete(
            ids=existing["ids"]
        )

    print(
        f"Indexing {len(sections)} college sections..."
    )

    for index, (title, content) in enumerate(
        sections
    ):

        # Put title together with content.
        # This improves semantic retrieval.
        searchable_text = (
            f"{title}: {content}"
        )

        embedding = model().encode(
            searchable_text
        ).tolist()

        collection.upsert(

            ids=[
                f"college-section-{index}"
            ],

            documents=[
                searchable_text
            ],

            embeddings=[
                embedding
            ],

            metadatas=[
                {
                    "source":
                        "college_knowledge.txt",

                    "section":
                        title
                }
            ]
        )

    print(
        "College knowledge base indexed successfully."
    )


# ============================================================
# DATABASE COUNT
# ============================================================

def collection_count():

    return collection.count()


# ============================================================
# PDF INGESTION
# ============================================================

def chunk_text(
    text,
    size=700,
    overlap=100
):

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    chunks = []

    start = 0

    while start < len(text):

        end = min(
            start + size,
            len(text)
        )

        chunk = text[
            start:end
        ].strip()

        if chunk:

            chunks.append(
                chunk
            )

        if end == len(text):

            break

        start = max(
            0,
            end - overlap
        )

    return chunks


def ingest_pdf(path):

    reader = PdfReader(
        str(path)
    )

    total = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        chunks = chunk_text(text)

        for index, chunk in enumerate(
            chunks
        ):

            document_id = (
                f"{path.stem}-"
                f"{page_number}-"
                f"{index}"
            )

            embedding = model().encode(
                chunk
            ).tolist()

            collection.upsert(

                ids=[
                    document_id
                ],

                documents=[
                    chunk
                ],

                embeddings=[
                    embedding
                ],

                metadatas=[
                    {
                        "source":
                            path.name,

                        "page":
                            page_number,

                        "type":
                            "pdf"
                    }
                ]
            )

            total += 1

    return total


# ============================================================
# ANSWER QUESTION
# ============================================================

def answer_question(question):

    # Load the official college sections.
    load_college_knowledge()
    # ========================================================
    # FOLLOW-UP QUESTION RESOLUTION
    # ========================================================

    q = question.lower()

    if (
        (
            "which one" in q
            or "which course" in q
            or "which one is" in q
        )
        and (
            "ai" in q
            or "artificial intelligence" in q
        )
    ):

        return {
            "answer": (
                "The undergraduate course most directly "
                "related to AI is **B.Sc Artificial Intelligence**. "
                "The college also offers **B.Sc Computer Science** "
                "and **B.Sc Data Science**, which are related fields."
            ),

            "sources": [
                {
                    "document": "college_knowledge.txt",
                    "section": "UG COURSES"
                }
            ],

            "confidence": 1.0,

            "fallback": False
        }
    if collection.count() == 0:

        return {
            "answer":
                "The college knowledge base is empty.",

            "sources": [],

            "confidence": 0.0,

            "fallback": True
        }

    # ========================================================
    # SPECIAL KEYWORD ROUTING
    # ========================================================

    q = question.lower()

    # Contact questions
    contact_words = [
        "contact",
        "phone",
        "telephone",
        "mobile",
        "email",
        "address",
        "reach college",
        "contact number"
    ]

    if any(
        word in q
        for word in contact_words
    ):

        result = collection.get(
            where={
                "section": "CONTACT"
            }
        )

        documents = result.get(
            "documents",
            []
        )

        metadatas = result.get(
            "metadatas",
            []
        )

        if documents:

            return build_response(
                documents[0],
                metadatas[0],
                confidence=0.98
            )

    # Course questions
    course_words = [
        "course",
        "courses",
        "degree",
        "ug",
        "pg",
        "undergraduate",
        "postgraduate"
    ]

    # Compute the embedding once, using OUR model
    # (all-MiniLM-L6-v2), so every query lands in the
    # SAME vector space as the documents that were
    # indexed with model().encode(...). Previously the
    # course_words branch used query_texts=, which asks
    # Chroma to embed the question with its own default
    # embedding function instead -- a different, mismatched
    # vector space that produced meaningless distances and
    # let the old college_knowledge.txt UG COURSES chunk
    # win over the correct PDF content.
    query_embedding = model().encode(
        question
    ).tolist()

    if any(
        word in q
        for word in course_words
    ):

        result = collection.query(

            query_embeddings=[
                query_embedding
            ],

            n_results=5
        )

    else:

        result = collection.query(

            query_embeddings=[
                query_embedding
            ],

            n_results=10
        )

    documents = result.get(
        "documents",
        [[]]
    )[0]

    metadatas = result.get(
        "metadatas",
        [[]]
    )[0]

    distances = result.get(
        "distances",
        [[]]
    )[0]

    if not documents:

        return fallback_response()

    best_distance = (
        distances[0]
        if distances
        else 1.0
    )

    confidence = max(
        0.0,
        min(
            1.0,
            1.0 - float(
                best_distance
            )
        )
    )

    if confidence < 0.35:

        return fallback_response()

    return build_response(
        documents[0],
        metadatas[0],
        confidence
    )


# ============================================================
# BUILD RESPONSE
# ============================================================

def build_response(
    document,
    metadata,
    confidence
):
    """
    Convert retrieved college information into
    a clean, student-friendly response.
    """

    section = metadata.get(
        "section",
        ""
    )

    # Remove the section title from the
    # beginning of the retrieved document.
    if ":" in document:

        answer = document.split(
            ":",
            1
        )[1].strip()

    else:

        answer = document.strip()


    # --------------------------------------------------------
    # CONTACT INFORMATION
    # --------------------------------------------------------

    if section == "CONTACT":

        answer = (
            "You can contact Karan Arts and "
            "Science College using the following "
            "official contact details:\n\n"
            "📞 Telephone: 04175 295295\n"
            "📱 Mobile: +91 9655189091\n"
            "📧 Email: karanarts2017@gmail.com\n\n"
            "📍 Address:\n"
            "Velu Nagar, Su Kilnachipattu,\n"
            "Thenmathur,\n"
            "Tiruvannamalai,\n"
            "Tamil Nadu - 606603"
        )


    # --------------------------------------------------------
    # UG COURSES
    # --------------------------------------------------------

    elif section == "UG COURSES":

        answer = (
            "Karan Arts and Science College "
            "offers the following undergraduate "
            "programs:\n\n"
            "• B.A English\n"
            "• B.A Tamil\n"
            "• B.B.A Business Administration\n"
            "• B.C.A Computer Application\n"
            "• B.Com General\n"
            "• B.Com Computer Application\n"
            "• B.Com Finance & Accounts\n"
            "• B.Sc Artificial Intelligence\n"
            "• B.Sc Chemistry\n"
            "• B.Sc Computer Science\n"
            "• B.Sc Data Science\n"
            "• B.Sc Mathematics\n"
            "• B.Sc Physics"
        )


    # --------------------------------------------------------
    # PG COURSES
    # --------------------------------------------------------

    elif section == "PG COURSES":

        answer = (
            "The college offers the following "
            "postgraduate programs:\n\n"
            "• M.A English\n"
            "• M.Com General\n"
            "• M.Sc Computer Science\n"
            "• M.Sc Mathematics"
        )


    # --------------------------------------------------------
    # FACILITIES
    # --------------------------------------------------------

    elif section == "FACILITIES":

        answer = (
            "The college website lists several "
            "facilities, including:\n\n"
            "• English Lab\n"
            "• Physics Lab\n"
            "• Chemistry Lab\n"
            "• Computer Lab\n"
            "• Internet / Wi-Fi\n"
            "• Transport\n"
            "• Hostel\n"
            "• Auditorium\n"
            "• CCTV\n"
            "• Canteen\n"
            "• Library\n"
            "• Fitness facilities\n"
            "• Medical facilities"
        )


    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    else:

        answer = (
            f"Here is the verified information "
            f"available in the college knowledge base "
            f"under **{section}**:\n\n"
            f"{answer}"
        )


    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    source = {
        "document": metadata.get(
            "source",
            "College Knowledge Base"
        )
    }

    if section:

        source["section"] = section

    if metadata.get("page"):

        source["page"] = metadata[
            "page"
        ]


    return {
        "answer": answer,

        "sources": [
            source
        ],

        "confidence": round(
            confidence,
            2
        ),

        "fallback": False
    }

# ============================================================
# FALLBACK
# ============================================================

def fallback_response():

    return {

        "answer":
            (
                "I couldn't find verified "
                "information about that in "
                "the college knowledge base. "
                "Please contact the appropriate "
                "college office for confirmation."
            ),

        "sources": [],

        "confidence": 0.0,

        "fallback": True
    }