"""
List models for persistent storage.
Tracks user lists and items (shopping lists, todo lists, etc.).
"""

from datetime import datetime
from typing import Dict, List as ListType, Optional
from pydantic import BaseModel, Field
import uuid


class ListItem(BaseModel):
    """A single item in a list."""
    item_id: str = Field(default_factory=lambda: f"item_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(default=None, description="Optional item description")
    quantity: Optional[str] = Field(default=None, description="Optional quantity (e.g., '2', '1 lb', '3 cups')")
    completed: bool = Field(default=False, description="Whether the item has been completed")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = Field(default=None, description="When the item was marked as completed")


class List(BaseModel):
    """A named list containing items."""
    list_id: str = Field(default_factory=lambda: f"list_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="List name (e.g., 'Groceries', 'Costco List', 'Todo List')")
    items: ListType[ListItem] = Field(default_factory=list, description="Items in the list")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserLists(BaseModel):
    """Collection of lists for a user."""
    user_id: str = Field(..., description="User ID this belongs to")
    lists: Dict[str, List] = Field(default_factory=dict, description="Map of list_id to List object")
