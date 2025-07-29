# chat_backend.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# 🌐 Flask setup
app = Flask(__name__)
CORS(app)

# 🔐 Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME", "nikhil-resume-index")

# 🔌 Connect to Pinecone and LangChain vectorstore
pc = Pinecone(api_key=PINECONE_API_KEY)
pinecone_index = pc.Index(INDEX_NAME)
embedding = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = PineconeVectorStore.from_existing_index(index_name=INDEX_NAME, embedding=embedding)

# 🔍 Setup retriever
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "lambda_mult": 0.8}
)

# 🧠 Prompt template
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a helpful AI assistant answering questions strictly based on Nikhil Pujari’s resume and background information.

Instructions:
- Always give detailed, specific answers, referring to **what** Nikhil did, **how** he applied skills, and **where** he used them — without stating "as per the context" or referencing document sections.
- If context clearly includes examples (like projects, tools, impact), include that detail in your response.
- Respond with clear, specific, and natural language — like a human colleague would.
- Aim for 2–3 sentences max unless the user asks for more detail.
- Avoid repeating general traits — focus on key accomplishments or skills.
- Do not speculate or answer generally. If the answer is not in the context, simply say: "I do not have this information currently."

Context:
{context}

Question:
{question}
"""
)

# 🤖 QA pipeline
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY, temperature=0, max_tokens=300),
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt_template}
)

# 📡 Flask API endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    response = qa.run(query)
    return jsonify({"response": response})

# 🚀 Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004)
Demo
