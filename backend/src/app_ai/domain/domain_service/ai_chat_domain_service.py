from typing import List, Generator, Tuple
from app_ai.domain.aggregate.ai_conversation import AiConversation
from app_ai.domain.entity.ai_message import AiMessage
from app_ai.domain.value_objects.retrieved_document import RetrievedDocument
from app_ai.domain.value_objects.attachment import MessageAttachment, AttachmentType
from app_ai.domain.demand_interface.i_llm_client import ILlmClient
from app_ai.domain.demand_interface.i_retriever import IRetriever

class AiChatDomainService:
    """
    Core Domain Service for AI Chat.
    Orchestrates the RAG flow: Retrieve -> Augment -> Generate.
    """
    def __init__(self, llm_client: ILlmClient, retriever: IRetriever):
        self.llm_client = llm_client
        self.retriever = retriever

    def generate_system_prompt(self, documents: List[RetrievedDocument]) -> str:
        base_prompt = """You are TraeTravel Bot, a professional and friendly travel assistant.
        Please answer the user's question based on the following [Reference Information].
        
        Guidelines:
        1. Use Markdown format (bold for emphasis, lists for points).
        2. If the reference information is insufficient, use your general knowledge but mention it.
        3. Be concise and helpful.
        """
        
        if not documents:
            return base_prompt + "\n\n[Reference Information]: None found."
            
        docs_text = "\n".join([f"{i+1}. {str(doc)}" for i, doc in enumerate(documents)])
        return f"{base_prompt}\n\n[Reference Information]:\n{docs_text}"

    def identify_attachments(self, documents: List[RetrievedDocument], llm_response_text: str) -> List[MessageAttachment]:
        """
        Heuristic Strategy (B): 
        If the document is highly relevant (Top-3) OR explicitly mentioned in the response,
        attach it as a card.
        For now, we simply attach the top 3 retrieved documents if they exist.
        """
        attachments = []
        seen_ids = set()
        
        # Take top 3 unique documents
        for doc in documents[:3]:
            if doc.reference_id in seen_ids:
                continue
            
            att_type = AttachmentType.POST if doc.source_type == 'post' else AttachmentType.ACTIVITY
            # Note: image_url is not in RetrievedDocument yet, we might need to fetch it or include it in retrieval
            # For this version, we leave image_url empty
            
            attachments.append(MessageAttachment(
                type=att_type,
                reference_id=doc.reference_id,
                title=doc.title,
                image_url=None 
            ))
            seen_ids.add(doc.reference_id)
            
        return attachments

    def stream_response(self, conversation: AiConversation, query: str) -> Generator[dict, None, None]:
        """
        Generator that yields SSE events.
        """
        # 1. Retrieve
        documents = self.retriever.search(query)
        
        # 2. Build Prompt
        system_prompt = self.generate_system_prompt(documents)
        history = conversation.get_history_for_llm()
        
        # 3. Call LLM & Stream Text
        full_response_text = ""
        for chunk in self.llm_client.stream_chat(history, system_prompt):
            full_response_text += chunk
            yield {
                "event": "text_chunk",
                "data": {"delta": chunk, "finish": False}
            }
            
        yield {
            "event": "message_end",
            "data": {"full_text": full_response_text}
        }
        
        # 5. Identify Attachments
        attachments = self.identify_attachments(documents, full_response_text)
        for att in attachments:
            yield {
                "event": "attachment",
                "data": att.to_dict()
            }
            
        # 6. Return final full message structure (for App Service to save)
        # We yield a special internal event for the App Service to capture
        yield {
            "event": "internal_complete",
            "data": {
                "full_text": full_response_text,
                "attachments": [att.to_dict() for att in attachments]
            }
        }
