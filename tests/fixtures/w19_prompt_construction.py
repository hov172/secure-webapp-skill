SYSTEM = "You are a support agent for ACME. Internal admin key: {admin_key}"


def build_prompt(user_message: str, retrieved_docs: list[str], admin_key: str) -> str:
    system = SYSTEM.format(admin_key=admin_key)
    docs = "\n".join(retrieved_docs)
    return f"{system}\n\nKnowledge base:\n{docs}\n\nUser: {user_message}"


def answer(user_message, admin_key):
    docs = vector_store.search(user_message, k=5)  # not scoped to the caller's tenant
    return llm.generate(build_prompt(user_message, docs, admin_key))
