from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

PROMPT = ChatPromptTemplate.from_template("""Answer the question using the context below.
If the context doesn't contain enough information, share what you do know from it and state clearly what's missing.

Context:
{context}

Question: {question}""")

llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
chain = PROMPT | llm | StrOutputParser()

async def stream_answer(docs, question: str):
    context = "\n\n".join(d.page_content for d in docs)
    sources = list({d.metadata.get("file_name") for d in docs})

    async for chunk in chain.astream({"context": context, "question": question}):
        yield {"type": "chunk", "content": chunk}

    yield {"type": "sources", "content": sources}
