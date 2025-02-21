from flask import Flask, request, render_template, jsonify, send_from_directory, redirect
from flask_cors import CORS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os
import shutil

app = Flask(__name__)
# Configure CORS with specific settings
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept"],
        "supports_credentials": True
    }
})

folder_path = "db"
pdf_folder = "pdf"

# Create necessary directories
os.makedirs(pdf_folder, exist_ok=True)
os.makedirs("static", exist_ok=True)

# Set Google API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyCHJOkMGNtx5TUbKNCOHSSttOWJm9qbwH0"

# Initialize Gemini model with temperature 0
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0  # Set temperature to 0 for deterministic responses
)

# Initialize Google's embedding model
embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Adjust text splitter for better chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,  # Smaller chunks for more precise context
    chunk_overlap=50,
    length_function=len,
    is_separator_regex=False
)

# Create the prompt template
prompt = PromptTemplate.from_template("""You are a helpful assistant answering questions about documents. Answer the question based only on the following context:

Context: {context}
Question: {question}

Keep your answer concise and factual. If you cannot find the specific information in the context, say so clearly. and produce the asswers in precise manner , so this chatbot is made by Genrec-AI 

Answer: """)

@app.route("/")
def index():
    return redirect("/widget")

@app.route("/widget")
def widget():
    return render_template('widget.html')

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/ask", methods=["POST"])
def askPDFPost():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "No question provided"}), 400
        
    question = data["question"]
    print(f"Received question: {question}")

    try:
        # Load the vector store
        if not os.path.exists(folder_path):
            return jsonify({"error": "No documents have been uploaded yet. Please upload a PDF first."}), 400

        vector_store = Chroma(persist_directory=folder_path, embedding_function=embedding)
        
        # Get relevant documents first
        docs = vector_store.similarity_search(
            question,
            k=5,  # Retrieve top 5 most relevant chunks
        )
        
        if not docs:
            return jsonify({"error": "No relevant content found in the documents."}), 404

        print(f"Found {len(docs)} relevant chunks")
        context = "\n\n".join(doc.page_content for doc in docs)
        
        # Generate response using LLM
        response = llm.invoke(
            prompt.format(
                context=context,
                question=question
            )
        )

        return jsonify({
            "answer": response.content,
            "sources": [{"source": doc.metadata["source"], "page_content": doc.page_content} for doc in docs]
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/upload", methods=["POST"])
def pdfPost():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["pdf_file"]
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    try:
        # Clear existing vectorstore
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        os.makedirs(folder_path)
        
        file_name = file.filename
        save_file = os.path.join(pdf_folder, file_name)
        file.save(save_file)
        print(f"Uploaded file: {file_name}")

        # Load and process the PDF
        loader = PDFPlumberLoader(save_file)
        docs = loader.load()
        print(f"Loaded {len(docs)} pages from PDF")

        # Split into chunks
        chunks = text_splitter.split_documents(docs)
        print(f"Created {len(chunks)} chunks")

        # Create new vector store
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embedding,
            persist_directory=folder_path
        )
        
        print("Vector store created successfully")

        return jsonify({
            "status": "Successfully Uploaded",
            "filename": file_name,
            "pages": len(docs),
            "chunks": len(chunks),
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def start_app():
    app.run(host="0.0.0.0", port=8080, debug=True)

if __name__ == "__main__":
    start_app()


