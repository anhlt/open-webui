from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class UsageDetails:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: Optional[Dict[str, Any]] = None
    completion_tokens_details: Optional[Dict[str, Any]] = None


@dataclass
class FileMeta:
    name: str
    content_type: str
    size: int
    data: Dict[str, Any]
    collection_name: str


@dataclass
class FileData:
    content: Optional[str] = None  # Adjust type if other file data is expected


@dataclass
class File:
    id: str
    user_id: str
    hash: str
    filename: str
    data: FileData
    meta: FileMeta
    created_at: int
    updated_at: int


@dataclass
class Source:
    source: Dict[str, Any]
    document: Optional[List[str]] = None
    metadata: Optional[List[Dict[str, Any]]] = None
    distances: Optional[List[float]] = None


@dataclass
class ChatMessage:
    id: str
    parentId: Optional[str]
    childrenIds: List[str]
    role: str
    content: str
    timestamp: int
    models: List[str]

    model: Optional[str] = None
    modelName: Optional[str] = None
    modelIdx: Optional[int] = None
    userContext: Optional[Any] = None
    usage: Optional[UsageDetails] = None
    done: Optional[bool] = None
    files: Optional[List[File]] = None
    sources: Optional[List[Source]] = None


@dataclass
class Messages:
    # Dictionary of message ID to ChatMessage
    messages: Dict[str, ChatMessage]


@dataclass
class History:
    messages: Dict[str, ChatMessage]
    currentId: Optional[str] = None


"""
Represents a conversation with associated metadata and message history.

Attributes:
    id (str): Unique identifier for the conversation.
    title (str): Title or name of the conversation.
    models (List[str]): List of model names or identifiers used in the conversation.
    params (Dict[str, Any]): Parameters associated with the conversation.
    history (History): Complete message history, including modified messages.
    messages (List[ChatMessage]): List of chat messages in the conversation.
    tags (List[Any]): Tags or labels associated with the conversation.
    timestamp (int): Unix timestamp indicating when the conversation was created or last updated.
    files (List[Any]): List of files attached to the conversation.
"""
@dataclass
class Conversation:
    id: str
    title: str
    models: List[str]
    params: Dict[str, Any]
    history: History  
    messages: List[ChatMessage]
    tags: List[Any]
    timestamp: int
    files: List[Any]
