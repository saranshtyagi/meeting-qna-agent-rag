from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.core.llm import get_llm
from app.core.vector_store import (
    get_retriever,
    load_vector_store,
)
import gc

class ChatService:

    def ask(
        self,
        meeting_id: str,
        question: str,
    ) -> str:

        vector_store = load_vector_store(meeting_id)

        try:
            retriever = get_retriever(
                vector_store,
                k=4,
            )

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """
                        You are an expert AI Meeting Assistant.

                        Answer ONLY using the meeting transcript context.

                        If the answer cannot be found in the transcript,
                        reply:

                        "I could not find this information in the meeting."

                        Always answer professionally and concisely.

                        Meeting Context:
                        {context}
                        """,
                    ),
                    ("human", "{question}"),
                ]
            )

            chain = (
                {
                    "context": retriever
                    | RunnableLambda(self._format_docs),
                    "question": RunnablePassthrough(),
                }
                | prompt
                | get_llm()
                | StrOutputParser()
            )

            return chain.invoke(question)

        finally:
            del vector_store
            gc.collect()

    @staticmethod
    def _format_docs(docs):

        return "\n\n".join(
            doc.page_content
            for doc in docs
        )