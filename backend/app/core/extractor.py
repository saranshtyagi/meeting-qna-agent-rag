from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from app.core.llm import get_llm

def build_chain(system_prompt: str):
    llm = get_llm()

    return(
        RunnablePassthrough() | 
        RunnableLambda(lambda x: {"text": x}) | 
        ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}")
        ]) | llm | StrOutputParser()
    )

def extract_action_items(transcript) -> str:
    print("Starting Action Items...")
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "-Task Description\n"
        "-Owner (who is responsible)\n"
        "-Deadline (if mentioned, else write 'Not Specified)\n\n"
        "Format as a number list. If none found say 'No action items found.'"
    )

    print("Action Items Complete.")

    return chain.invoke(transcript)

def extract_key_decisions(transcript: str) -> str:
    print("Starting Decisions...")
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions made. Format as a numbered list. "
        "If none found say 'No key decisions found.'"
    )

    print("Decisions Complete.")

    return chain.invoke(transcript)

def extract_questions(transcript: str) -> str:
    print("Starting Questions...")
    chain = build_chain(
        "From the meeting transcript, extract all unresolved questions "
        "or topics needing follow-up. Format as a numbered list. "
        "If none found say 'No open questions found.'"
    )

    print("Questions Complete.")

    return chain.invoke(transcript)

