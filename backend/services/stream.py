from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

PROMPT = ChatPromptTemplate.from_template("""Answer the question based only on the context below.

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
