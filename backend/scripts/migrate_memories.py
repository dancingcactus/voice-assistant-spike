"""
Migrate existing user preferences to structured memory system.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def generate_memory_id():
    """Generate a unique memory ID."""
    return f"mem_{uuid.uuid4().hex[:12]}"

def migrate_user_memories(user_file_path: Path):
    """Migrate a user's preferences to structured memories."""

    with open(user_file_path, 'r') as f:
        user_data = json.load(f)

    # Initialize memories dict if not present
    if 'memories' not in user_data:
        user_data['memories'] = {'memories': {}}

    memories = {}

    # Migrate dietary restrictions
    for restriction in user_data.get('preferences', {}).get('dietary_restrictions', []):
        mem_id = generate_memory_id()
        memories[mem_id] = {
            'memory_id': mem_id,
            'category': 'dietary_restriction',
            'content': f"Has {restriction} intolerance/restriction",
            'source': 'migration_from_preferences',
            'importance': 9,  # Dietary restrictions are critical
            'verified': True,
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_accessed': None,
            'access_count': 0,
            'metadata': {'original_field': 'dietary_restrictions'}
        }

    # Migrate favorite foods
    for food in user_data.get('preferences', {}).get('favorite_foods', []):
        mem_id = generate_memory_id()
        memories[mem_id] = {
            'memory_id': mem_id,
            'category': 'preference',
            'content': f"Loves {food}",
            'source': 'migration_from_preferences',
            'importance': 6,
            'verified': True,
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_accessed': None,
            'access_count': 0,
            'metadata': {'original_field': 'favorite_foods', 'food_type': 'favorite'}
        }

    # Migrate disliked foods
    for food in user_data.get('preferences', {}).get('disliked_foods', []):
        mem_id = generate_memory_id()
        memories[mem_id] = {
            'memory_id': mem_id,
            'category': 'preference',
            'content': f"Dislikes {food}",
            'source': 'migration_from_preferences',
            'importance': 5,
            'verified': True,
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_accessed': None,
            'access_count': 0,
            'metadata': {'original_field': 'disliked_foods', 'food_type': 'disliked'}
        }

    # Migrate cooking skill level
    skill_level = user_data.get('preferences', {}).get('cooking_skill_level')
    if skill_level:
        mem_id = generate_memory_id()
        memories[mem_id] = {
            'memory_id': mem_id,
            'category': 'fact',
            'content': f"Has {skill_level} cooking skill level",
            'source': 'migration_from_preferences',
            'importance': 7,
            'verified': True,
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_accessed': None,
            'access_count': 0,
            'metadata': {'original_field': 'cooking_skill_level'}
        }

    # Migrate custom preferences
    custom_prefs = user_data.get('preferences', {}).get('custom_preferences', {})

    if custom_prefs.get('children_count'):
        mem_id = generate_memory_id()
        memories[mem_id] = {
            'memory_id': mem_id,
            'category': 'fact',
            'content': f"Has {custom_prefs['children_count']} children",
            'source': 'migration_from_preferences',
            'importance': 8,
            'verified': True,
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_accessed': None,
            'access_count': 0,
            'metadata': {'original_field': 'custom_preferences.children_count'}
        }

    if custom_prefs.get('greenhouse'):
        mem_id = generate_memory_id()
        memories[mem_id] = {
            'memory_id': mem_id,
            'category': 'fact',
            'content': "Has a greenhouse with 200 hanging baskets",
            'source': 'migration_from_preferences',
            'importance': 6,
            'verified': True,
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_accessed': None,
            'access_count': 0,
            'metadata': {'original_field': 'custom_preferences.greenhouse'}
        }

    if custom_prefs.get('smart_home_expert'):
        mem_id = generate_memory_id()
        memories[mem_id] = {
            'memory_id': mem_id,
            'category': 'fact',
            'content': "Is an expert in smart home systems and embedded development",
            'source': 'migration_from_preferences',
            'importance': 5,
            'verified': True,
            'created_at': user_data.get('created_at', datetime.now().isoformat()),
            'last_accessed': None,
            'access_count': 0,
            'metadata': {'original_field': 'custom_preferences.smart_home_expert'}
        }

    # Update the user data
    user_data['memories'] = {'memories': memories}

    # Write back to file
    with open(user_file_path, 'w') as f:
        json.dump(user_data, f, indent=2)

    print(f"✅ Migrated {len(memories)} memories for {user_file_path.stem}")
    print(f"   - {sum(1 for m in memories.values() if m['category'] == 'dietary_restriction')} dietary restrictions")
    print(f"   - {sum(1 for m in memories.values() if m['category'] == 'preference')} preferences")
    print(f"   - {sum(1 for m in memories.values() if m['category'] == 'fact')} facts")

if __name__ == "__main__":
    # Migrate user_justin.json
    data_dir = Path(__file__).parent.parent / "data" / "users"
    user_file = data_dir / "user_justin.json"

    if user_file.exists():
        migrate_user_memories(user_file)
    else:
        print(f"❌ User file not found: {user_file}")
