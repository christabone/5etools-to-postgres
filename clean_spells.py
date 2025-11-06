"""
Clean and normalize spell data from 5etools.

Eliminates polymorphic fields and ensures consistent data structure.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data/spells')
OUTPUT_FILE = Path('cleaned_data/spells.json')


def normalize_time(time_data: Any) -> Dict[str, Any]:
    """
    Normalize casting time to consistent structure.

    Input: [{"number": 1, "unit": "action"}]
    Output: {"number": 1, "unit": "action"}
    """
    if not time_data or not isinstance(time_data, list) or len(time_data) == 0:
        return {"number": 1, "unit": "action"}

    first = time_data[0]
    if isinstance(first, dict):
        return {
            "number": first.get('number', 1),
            "unit": first.get('unit', 'action')
        }

    return {"number": 1, "unit": "action"}


def normalize_range(range_data: Any) -> Dict[str, Any]:
    """
    Normalize range to consistent structure.

    Input: {"type": "point", "distance": {"type": "feet", "amount": 150}}
    Output: {"type": "point", "value": 150, "unit": "feet"}
    """
    if not range_data or not isinstance(range_data, dict):
        return {"type": "self", "value": 0, "unit": ""}

    range_type = range_data.get('type', 'self')

    # Handle special range types
    if range_type in ['self', 'touch', 'sight', 'unlimited', 'special']:
        return {"type": range_type, "value": 0, "unit": ""}

    # Handle distance-based range
    distance = range_data.get('distance', {})
    if isinstance(distance, dict):
        return {
            "type": range_type,
            "value": distance.get('amount', 0),
            "unit": distance.get('type', 'feet')
        }

    return {"type": range_type, "value": 0, "unit": ""}


def normalize_duration(duration_data: Any) -> Dict[str, Any]:
    """
    Normalize duration to consistent structure.

    Input: [{"type": "timed", "duration": {"type": "minute", "amount": 1}, "concentration": true}]
    Output: {"type": "timed", "value": 1, "unit": "minute", "concentration": true}
    """
    if not duration_data or not isinstance(duration_data, list) or len(duration_data) == 0:
        return {"type": "instant", "value": 0, "unit": "", "concentration": False}

    first = duration_data[0]
    if not isinstance(first, dict):
        return {"type": "instant", "value": 0, "unit": "", "concentration": False}

    duration_type = first.get('type', 'instant')
    concentration = first.get('concentration', False)

    # Handle instant/permanent
    if duration_type in ['instant', 'permanent', 'special']:
        return {
            "type": duration_type,
            "value": 0,
            "unit": "",
            "concentration": concentration
        }

    # Handle timed duration
    duration = first.get('duration', {})
    if isinstance(duration, dict):
        return {
            "type": duration_type,
            "value": duration.get('amount', 0),
            "unit": duration.get('type', ''),
            "concentration": concentration
        }

    return {"type": duration_type, "value": 0, "unit": "", "concentration": concentration}


def normalize_components(components_data: Any) -> Dict[str, Any]:
    """
    Normalize components to flat structure.

    Input: {"v": true, "s": true, "m": "bat guano and sulfur"}
    Output: {"v": true, "s": true, "m": true, "m_text": "bat guano and sulfur"}
    """
    if not components_data or not isinstance(components_data, dict):
        return {"v": False, "s": False, "m": False, "m_text": ""}

    material_data = components_data.get('m')
    has_material = bool(material_data)
    material_text = ""

    if isinstance(material_data, str):
        material_text = material_data
    elif isinstance(material_data, dict):
        material_text = material_data.get('text', '')

    return {
        "v": components_data.get('v', False),
        "s": components_data.get('s', False),
        "m": has_material,
        "m_text": material_text
    }


def flatten_entries(entries: Any) -> List[str]:
    """
    Flatten entries array to array of strings only.

    Handles nested structures for basic text extraction.
    """
    if not entries:
        return []

    if isinstance(entries, str):
        return [entries]

    if isinstance(entries, list):
        text_parts = []
        for entry in entries:
            if isinstance(entry, str):
                text_parts.append(entry)
            elif isinstance(entry, dict):
                # Extract text from nested structures
                if 'entries' in entry:
                    nested_text = flatten_entries(entry['entries'])
                    text_parts.extend(nested_text)
                elif 'items' in entry:
                    nested_text = flatten_entries(entry['items'])
                    text_parts.extend(nested_text)

        return text_parts

    return []


def normalize_scaling_level_dice(scaling: Any) -> List[Dict[str, Any]]:
    """
    Normalize scalingLevelDice to always be array of dicts.

    Input: {"label": "...", "scaling": {...}} OR [{"level": 5, "dice": "2d6"}]
    Output: [{"level": 5, "dice": "2d6"}]
    """
    if not scaling:
        return []

    if isinstance(scaling, list):
        return scaling

    if isinstance(scaling, dict):
        # Convert single dict to array
        return [scaling]

    return []


def normalize_srd_field(srd_value: Any) -> bool:
    """
    Normalize srd/srd52 to always be boolean.

    Input: true OR "SRD 5.1"
    Output: true
    """
    if isinstance(srd_value, bool):
        return srd_value
    if isinstance(srd_value, str):
        return True  # If it has a string value, it's in SRD
    return False


def clean_spell(spell: Dict) -> Dict:
    """Clean a single spell record."""
    cleaned = spell.copy()

    # Normalize casting time
    cleaned['time'] = normalize_time(spell.get('time'))

    # Normalize range
    cleaned['range'] = normalize_range(spell.get('range'))

    # Normalize duration
    cleaned['duration'] = normalize_duration(spell.get('duration'))

    # Normalize components
    cleaned['components'] = normalize_components(spell.get('components'))

    # Flatten description - now returns array of strings
    if 'entries' in spell:
        cleaned['entries'] = flatten_entries(spell.get('entries'))

    # Flatten higher level text
    if 'entriesHigherLevel' in spell:
        higher = spell.get('entriesHigherLevel', [])
        if higher and isinstance(higher, list):
            cleaned['entriesHigherLevel'] = flatten_entries(higher)

    # Ensure damageInflict is array
    if 'damageInflict' in spell:
        damage = spell.get('damageInflict')
        if isinstance(damage, list):
            cleaned['damageInflict'] = damage
        elif isinstance(damage, str):
            cleaned['damageInflict'] = [damage]
        else:
            cleaned['damageInflict'] = []

    # Clean school (remove source suffix)
    if 'school' in cleaned and isinstance(cleaned['school'], str) and '|' in cleaned['school']:
        cleaned['school'] = cleaned['school'].split('|')[0]

    # Normalize scalingLevelDice
    if 'scalingLevelDice' in spell:
        cleaned['scalingLevelDice'] = normalize_scaling_level_dice(spell.get('scalingLevelDice'))

    # Normalize SRD fields
    if 'srd' in spell:
        cleaned['srd'] = normalize_srd_field(spell['srd'])

    if 'srd52' in spell:
        cleaned['srd52'] = normalize_srd_field(spell['srd52'])

    return cleaned


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools Spell Data Cleaning")
    print("=" * 60)

    all_spells = []

    if not DATA_DIR.exists():
        print(f"❌ Error: {DATA_DIR} not found!")
        return

    # Process all spell files
    json_files = sorted(DATA_DIR.glob('spells-*.json'))
    print(f"\n📖 Found {len(json_files)} spell files")

    for json_file in json_files:
        print(f"  Processing {json_file.name}...")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                spells = data.get('spell', [])

                for spell in spells:
                    cleaned = clean_spell(spell)
                    cleaned['_source_file'] = json_file.name
                    all_spells.append(cleaned)

        except Exception as e:
            print(f"    ⚠️  Error processing {json_file.name}: {e}")

    # Save cleaned data
    print(f"\n💾 Saving {len(all_spells)} cleaned spells...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_spells, f, indent=2)

    print(f"✅ Cleaned spells saved to: {OUTPUT_FILE}")
    print(f"📊 Total spells: {len(all_spells)}")

    # Show sample
    print("\n📋 Sample cleaned spell:")
    if all_spells:
        sample = all_spells[0]
        print(f"  Name: {sample.get('name')}")
        print(f"  Level: {sample.get('level')}")
        print(f"  School: {sample.get('school')}")
        print(f"  Time: {sample.get('time')}")
        print(f"  Range: {sample.get('range')}")
        print(f"  Components: {sample.get('components')}")


if __name__ == '__main__':
    main()
