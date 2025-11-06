"""
Clean and normalize monster data from 5etools.

Eliminates polymorphic fields and ensures consistent data structure.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data/bestiary')
OUTPUT_FILE = Path('cleaned_data/monsters.json')


def normalize_type(type_data: Any) -> Dict[str, Any]:
    """
    Normalize type to always be {"type": str, "tags": [...]}.

    Input: "humanoid" OR {"type": "humanoid", "tags": ["orc"]} OR {"type": {"choose": [...}}}
    Output: {"type": "humanoid", "tags": ["orc"]}
    """
    if isinstance(type_data, str):
        return {"type": type_data, "tags": []}
    elif isinstance(type_data, dict):
        type_val = type_data.get('type', 'unknown')

        # Handle nested dict for type (very rare)
        if isinstance(type_val, dict):
            # Extract first option if it's a choose structure
            if 'choose' in type_val and isinstance(type_val['choose'], list):
                type_val = type_val['choose'][0] if type_val['choose'] else 'unknown'
            else:
                type_val = 'unknown'

        # Normalize tags to always be array of strings
        tags = type_data.get('tags', [])
        normalized_tags = []
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str):
                    normalized_tags.append(tag)
                elif isinstance(tag, dict):
                    # Extract tag name from dict like {"tag": "orc", "prefix": "..."}
                    tag_name = tag.get('tag', '') or tag.get('name', '')
                    if tag_name:
                        normalized_tags.append(tag_name)

        return {
            "type": type_val,
            "tags": normalized_tags
        }
    return {"type": "unknown", "tags": []}


def normalize_ac(ac_data: Any) -> List[Dict[str, Any]]:
    """
    Normalize AC to always be array of dicts.

    Input: 13 OR [13] OR [{"ac": 13, "from": ["hide armor"]}]
    Output: [{"ac": 13, "from": None}]
    """
    if ac_data is None:
        return [{"ac": 10, "from": None}]

    if isinstance(ac_data, int):
        return [{"ac": ac_data, "from": None}]

    if isinstance(ac_data, list):
        result = []
        for item in ac_data:
            if isinstance(item, int):
                result.append({"ac": item, "from": None})
            elif isinstance(item, dict):
                result.append({
                    "ac": item.get('ac', 10),
                    "from": item.get('from', None)
                })
        return result if result else [{"ac": 10, "from": None}]

    return [{"ac": 10, "from": None}]


def normalize_alignment(alignment_data: Any) -> List[str]:
    """
    Normalize alignment to always be array of abbreviation strings.

    Input: ["C", "E"] OR "any alignment" OR {"alignment": ["L", "G"]}
    Output: ["C", "E"]
    """
    if not alignment_data:
        return ["U"]  # Unaligned

    if isinstance(alignment_data, str):
        # Handle special cases
        if "any" in alignment_data.lower():
            return ["A"]
        if "unaligned" in alignment_data.lower():
            return ["U"]
        return [alignment_data]

    if isinstance(alignment_data, list):
        result = []
        for item in alignment_data:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # Handle complex alignment with chance/note
                align = item.get('alignment', [])
                if isinstance(align, list):
                    result.extend(align)
                elif isinstance(align, str):
                    result.append(align)
        return result if result else ["U"]

    return ["U"]


def normalize_speed(speed_data: Any) -> Dict[str, int]:
    """
    Normalize speed to dict with all movement types.

    Input: {"walk": 30, "fly": 60} OR {"walk": 30, "fly": {"number": 60, "condition": "..."}}
    Output: {"walk": 30, "fly": 60, "swim": 0, "climb": 0, "burrow": 0}
    """
    if not speed_data or not isinstance(speed_data, dict):
        return {"walk": 30, "fly": 0, "swim": 0, "climb": 0, "burrow": 0}

    def extract_speed(value):
        """Extract speed number from int or dict."""
        if isinstance(value, int):
            return value
        elif isinstance(value, dict):
            return value.get('number', 0)
        return 0

    return {
        "walk": extract_speed(speed_data.get('walk', 30)),
        "fly": extract_speed(speed_data.get('fly')),
        "swim": extract_speed(speed_data.get('swim')),
        "climb": extract_speed(speed_data.get('climb')),
        "burrow": extract_speed(speed_data.get('burrow'))
    }


def normalize_cr(cr_data: Any) -> float:
    """
    Convert CR from string fraction to decimal.

    Input: "1/2" OR "5" OR 5
    Output: 0.5 OR 5.0
    """
    if cr_data is None:
        return 0.0

    if isinstance(cr_data, (int, float)):
        return float(cr_data)

    if isinstance(cr_data, str):
        if '/' in cr_data:
            parts = cr_data.split('/')
            return float(parts[0]) / float(parts[1])
        try:
            return float(cr_data)
        except ValueError:
            return 0.0

    return 0.0


def normalize_hp(hp_data: Any) -> Dict[str, Any]:
    """
    Parse HP into consistent structure.

    Input: {"average": 15, "formula": "2d8+6"}
    Output: {"average": 15, "formula": "2d8+6"}
    """
    if not hp_data or not isinstance(hp_data, dict):
        return {"average": 1, "formula": "1d1"}

    return {
        "average": hp_data.get('average', 1),
        "formula": hp_data.get('formula', '1d1')
    }


def normalize_size(size_data: Any) -> str:
    """
    Extract size as single character.

    Input: ["M"] OR "M"
    Output: "M"
    """
    if isinstance(size_data, list):
        return size_data[0] if size_data else "M"
    elif isinstance(size_data, str):
        return size_data
    return "M"


def normalize_damage_mods(damage_list: Any) -> List[str]:
    """
    Normalize resist/immune/vulnerable to simple string array.

    Input: ["fire", {"special": "..."}, "cold"]
    Output: ["fire", "cold"]
    """
    if not damage_list:
        return []

    result = []
    for item in damage_list:
        if isinstance(item, str):
            result.append(item)
        # Skip complex objects for now

    return result


def normalize_senses(senses: Any) -> List[str]:
    """
    Normalize senses to always be array of strings.

    Input: ["darkvision 60 ft."] OR None
    Output: ["darkvision 60 ft."] OR []
    """
    if senses is None:
        return []

    if isinstance(senses, list):
        return [str(s) for s in senses if isinstance(s, str)]

    return []


def normalize_passive(passive: Any) -> int:
    """
    Normalize passive perception to always be int.

    Input: 10 OR "10"
    Output: 10
    """
    if passive is None:
        return 10

    if isinstance(passive, int):
        return passive

    if isinstance(passive, str):
        try:
            return int(passive)
        except ValueError:
            return 10

    return 10


def normalize_languages(languages: Any) -> List[str]:
    """
    Normalize languages to always be array of strings.

    Input: ["Common", "Elvish"] OR None
    Output: ["Common", "Elvish"] OR []
    """
    if languages is None:
        return []

    if isinstance(languages, list):
        return [str(lang) for lang in languages if isinstance(lang, str)]

    return []


def normalize_optional_list_field(field: Any) -> List[Dict]:
    """
    Normalize optional fields like trait, action, reaction, legendary, spellcasting.

    Input: [{...}, {...}] OR None
    Output: [{...}, {...}] OR []
    """
    if field is None:
        return []

    if isinstance(field, list):
        return field

    return []


def normalize_group(group: Any) -> List[str]:
    """
    Normalize group to always be array of strings.

    Input: ["Demon"] OR None
    Output: ["Demon"] OR []
    """
    if group is None:
        return []

    if isinstance(group, list):
        return [str(g) for g in group if isinstance(g, str)]

    return []


def normalize_short_name(short_name: Any) -> str:
    """
    Normalize shortName to always be string.

    Input: true OR "Dragon"
    Output: "" OR "Dragon"
    """
    if short_name is None or short_name is False:
        return ""

    if short_name is True:
        return ""

    if isinstance(short_name, str):
        return short_name

    return ""


def normalize_gear(gear: Any) -> List[str]:
    """
    Normalize gear to always be array of strings.

    Input: ["sword", {"item": "shield"}]
    Output: ["sword", "shield"]
    """
    if not gear:
        return []

    result = []
    for item in gear:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            item_name = item.get('item', '')
            if item_name:
                result.append(item_name)

    return result


def clean_monster(monster: Dict) -> Dict:
    """Clean a single monster record."""
    cleaned = monster.copy()

    # Normalize type
    cleaned['type'] = normalize_type(monster.get('type'))

    # Normalize AC
    cleaned['ac'] = normalize_ac(monster.get('ac'))

    # Normalize alignment
    cleaned['alignment'] = normalize_alignment(monster.get('alignment'))

    # Normalize speed
    cleaned['speed'] = normalize_speed(monster.get('speed'))

    # Normalize CR
    cleaned['cr'] = normalize_cr(monster.get('cr'))

    # Normalize HP
    cleaned['hp'] = normalize_hp(monster.get('hp'))

    # Normalize size
    cleaned['size'] = normalize_size(monster.get('size'))

    # Normalize damage modifiers
    if 'resist' in monster:
        cleaned['resist'] = normalize_damage_mods(monster.get('resist'))

    if 'immune' in monster:
        cleaned['immune'] = normalize_damage_mods(monster.get('immune'))

    if 'vulnerable' in monster:
        cleaned['vulnerable'] = normalize_damage_mods(monster.get('vulnerable'))

    # Normalize condition immunities to simple array
    if 'conditionImmune' in monster:
        cond_immune = monster.get('conditionImmune', [])
        if isinstance(cond_immune, list):
            cleaned['conditionImmune'] = [
                c for c in cond_immune if isinstance(c, str)
            ]

    # Normalize senses
    if 'senses' in monster:
        cleaned['senses'] = normalize_senses(monster.get('senses'))

    # Normalize passive perception
    if 'passive' in monster:
        cleaned['passive'] = normalize_passive(monster.get('passive'))

    # Normalize languages
    if 'languages' in monster:
        cleaned['languages'] = normalize_languages(monster.get('languages'))

    # Normalize optional list fields
    if 'trait' in monster:
        cleaned['trait'] = normalize_optional_list_field(monster.get('trait'))

    if 'action' in monster:
        cleaned['action'] = normalize_optional_list_field(monster.get('action'))

    if 'reaction' in monster:
        cleaned['reaction'] = normalize_optional_list_field(monster.get('reaction'))

    if 'legendary' in monster:
        cleaned['legendary'] = normalize_optional_list_field(monster.get('legendary'))

    if 'spellcasting' in monster:
        cleaned['spellcasting'] = normalize_optional_list_field(monster.get('spellcasting'))

    # Normalize group
    if 'group' in monster:
        cleaned['group'] = normalize_group(monster.get('group'))

    # Normalize shortName
    if 'shortName' in monster:
        cleaned['shortName'] = normalize_short_name(monster.get('shortName'))

    # Normalize gear
    if 'gear' in monster:
        cleaned['gear'] = normalize_gear(monster.get('gear'))

    # Remove _copy field entirely - it's metadata we don't need
    if '_copy' in cleaned:
        del cleaned['_copy']

    return cleaned


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools Monster Data Cleaning")
    print("=" * 60)

    all_monsters = []

    if not DATA_DIR.exists():
        print(f"❌ Error: {DATA_DIR} not found!")
        return

    # Process all bestiary files
    json_files = sorted(DATA_DIR.glob('bestiary-*.json'))
    print(f"\n📖 Found {len(json_files)} bestiary files")

    for json_file in json_files:
        print(f"  Processing {json_file.name}...")

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                monsters = data.get('monster', [])

                for monster in monsters:
                    cleaned = clean_monster(monster)
                    cleaned['_source_file'] = json_file.name
                    all_monsters.append(cleaned)

        except Exception as e:
            print(f"    ⚠️  Error processing {json_file.name}: {e}")

    # Save cleaned data
    print(f"\n💾 Saving {len(all_monsters)} cleaned monsters...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_monsters, f, indent=2)

    print(f"✅ Cleaned monsters saved to: {OUTPUT_FILE}")
    print(f"📊 Total monsters: {len(all_monsters)}")

    # Show sample
    print("\n📋 Sample cleaned monster:")
    if all_monsters:
        sample = all_monsters[0]
        print(f"  Name: {sample.get('name')}")
        print(f"  Type: {sample.get('type')}")
        print(f"  Size: {sample.get('size')}")
        print(f"  AC: {sample.get('ac')}")
        print(f"  CR: {sample.get('cr')}")
        print(f"  Speed: {sample.get('speed')}")


if __name__ == '__main__':
    main()
