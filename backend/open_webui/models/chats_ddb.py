import uuid
import boto3
import time
from typing import Optional, List, Dict, Any
from boto3.dynamodb.conditions import Key
from .data_class.message import ChatMessage
from .chats import ChatForm

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UserConversationsTable')


class DynamoChatManager:
    def __init__(self, table):
        self.table = table

    def _conversation_pk(self, user_id: str, conv_id: str) -> str:
        return f"USER#{user_id}#{conv_id}"
    
    def _message_sk(self, timestamp: int) -> str:
        # Assuming SK is a string representation of the timestamp and random suffix
        return str(timestamp) + str(uuid.uuid4())
    

    def insert_new_conversation(
            self,
            user_id: str,
            form_data: ChatForm):
        
        conv_id = str(uuid.uuid4())


        



    def insert_conversation_metadata(
            self,
            user_id: str,
            conv_id: str,
            title: str = "New Chat",
            pinned: bool = False,
            archived: bool = False,
            meta: Optional[Dict[str, Any]] = None,
            folder_id: Optional[str] = None,
    ) -> bool:
        pk = self._conversation_pk(user_id, conv_id)
        item = {
            'PK': pk,
            'SK': "METADATA",
            'Title': title,
            'CreatedAt': int(time.time()),
            'UpdatedAt': int(time.time()),
            'Pinned': pinned,
            'Archived': archived,
            'Meta': meta or {},
            'FolderID': folder_id or "",
        }
        self.table.put_item(Item=item)
        return True

    def update_conversation_metadata(
            self,
            user_id: str,
            conv_id: str,
            updates: Dict[str, Any]
    ) -> bool:
        pk = self._conversation_pk(user_id, conv_id)
        # Fetch existing metadata
        existing = self.get_conversation_metadata(user_id, conv_id)
        if not existing:
            # Insert if missing
            self.insert_conversation_metadata(user_id, conv_id, **updates)
            return True

        # Merge updates
        item = existing.copy()
        item.update(updates)
        item['UpdatedAt'] = int(time.time())

        item['PK'] = pk
        item['SK'] = "METADATA"
        self.table.put_item(Item=item)
        return True

    def get_conversation_metadata(
            self,
            user_id: str,
            conv_id: str
    ) -> Optional[Dict[str, Any]]:
        pk = self._conversation_pk(user_id, conv_id)
        resp = self.table.get_item(Key={'PK': pk, 'SK': "METADATA"})
        return resp.get('Item')

    def insert_message(
            self,
            user_id: str,
            conv_id: str,
            message_id: str,
            content: str,
            sender: str,
            timestamp: int,
            metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        pk = self._conversation_pk(user_id, conv_id)
        # Sort key as ISO timestamp or number string for ordering
        sk = str(timestamp)
        item = {
            'PK': pk,
            'SK': sk,
            'MessageID': message_id,
            'Content': content,
            'Sender': sender,
            'Timestamp': timestamp,
            'Metadata': metadata or {},
        }
        self.table.put_item(Item=item)
        # Also update conversation's last update timestamp
        self.update_conversation_metadata(user_id, conv_id, {'UpdatedAt': timestamp})
        return True

    def get_messages(
            self,
            user_id: str,
            conv_id: str,
            limit: int = 100,
            start_key: Optional[Dict[str, Any]] = None,
            descending: bool = False
    ) -> Dict[str, Any]:
        pk = self._conversation_pk(user_id, conv_id)

        kwargs = {
            'KeyConditionExpression': Key('PK').eq(pk) & Key('SK').begins_with('2'),  # assuming SK timestamps always start with '2' for years
            'Limit': limit,
            'ScanIndexForward': not descending,
        }
        if start_key:
            kwargs['ExclusiveStartKey'] = start_key

        resp = self.table.query(**kwargs)
        return {
            'Messages': resp.get('Items', []),
            'LastEvaluatedKey': resp.get('LastEvaluatedKey')
        }

    def get_all_items(
            self,
            user_id: str,
            conv_id: str
    ) -> List[Dict[str, Any]]:
        # Fetch all items (metadata + all messages) of a conversation
        pk = self._conversation_pk(user_id, conv_id)
        response = self.table.query(
            KeyConditionExpression=Key('PK').eq(pk)
        )
        return response.get('Items', [])

    def delete_conversation(
            self,
            user_id: str,
            conv_id: str
    ) -> bool:
        # Delete all items belonging to conversation
        pk = self._conversation_pk(user_id, conv_id)

        # Scan to get all items keys
        response = self.table.query(KeyConditionExpression=Key('PK').eq(pk))
        items = response.get('Items', [])

        with self.table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})

        return True

    def pin_conversation(
            self,
            user_id: str,
            conv_id: str,
            pin: bool = True
    ) -> bool:
        return self.update_conversation_metadata(user_id, conv_id, {'Pinned': pin})

    def archive_conversation(
            self,
            user_id: str,
            conv_id: str,
            archive: bool = True
    ) -> bool:
        return self.update_conversation_metadata(user_id, conv_id, {'Archived': archive})

    def add_tag_to_conversation(
            self,
            user_id: str,
            conv_id: str,
            tag: str
    ) -> bool:
        meta = self.get_conversation_metadata(user_id, conv_id)
        if meta is None:
            meta = {}
        tags = meta.get('Meta', {}).get('tags', [])
        if tag not in tags:
            tags.append(tag)
        meta['Meta'] = meta.get('Meta', {})
        meta['Meta']['tags'] = tags
        return self.update_conversation_metadata(user_id, conv_id, {'Meta': meta['Meta']})

    def remove_tag_from_conversation(
            self,
            user_id: str,
            conv_id: str,
            tag: str
    ) -> bool:
        meta = self.get_conversation_metadata(user_id, conv_id)
        if meta is None or 'Meta' not in meta:
            return False
        tags = meta['Meta'].get('tags', [])
        if tag in tags:
            tags.remove(tag)
            meta['Meta']['tags'] = tags
            return self.update_conversation_metadata(user_id, conv_id, {'Meta': meta['Meta']})
        return False

    def search_conversations_by_tag(
            self,
            user_id: str,
            tag: str,
            limit: int = 50
    ) -> List[Dict[str, Any]]:
        # DynamoDB cannot efficiently query JSON tags inside an attribute.
        # This requires a GSI or a separate tags table for efficient tag-based search.
        # Simple solution: scan table with filter (not recommended for production).
        # In production, better to maintain a separate tag index table.

        response = self.table.scan(
            FilterExpression=Key('PK').begins_with(f"USER#{user_id}#") & Key('SK').eq("METADATA"),
            Limit=limit,
        )
        items = response.get('Items', [])

        # Filter locally for tag membership
        tagged_convs = [item for item in items if tag in item.get('Meta', {}).get('tags', [])]

        return tagged_convs


# Create instance
Chats = DynamoChatManager(table)