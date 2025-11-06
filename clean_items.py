"""
Clean and normalize item data from 5etools.

Eliminates polymorphic fields and ensures consistent data structure.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


DATA_DIR = Path('/home/ctabone/dnd_bot/5etools-src-2.15.0/data')
OUTPUT_FILE = Path('cleaned_data/items.json')


def normalize_value(value_data: Any) -> int:
    """
    Convert value to copper pieces (int).

    Examples:
        5 → 500 (assume gp if plain int > 100, else cp)
        {"gp": 5} → 500
        {"sp": 10, "cp": 5} → 105
        None → 0
    """
    if value_data is None:
        return 0

    if isinstance(value_data, dict):
        cp = value_data.get('cp', 0)
        sp = value_data.get('sp', 0) * 10
        gp = value_data.get('gp', 0) * 100
        pp = value_data.get('pp', 0) * 1000
        return int(cp + sp + gp + pp)

    if isinstance(value_data, (int, float)):
        # Heuristic: if value > 100, assume it's already in cp
        # Otherwise assume gp and convert
        if value_data > 100:
            return int(value_data)
        else:
            return int(value_data * 100)  # Convert gp to cp

    return 0


def normalize_weight(weight_data: Any) -> float:
    """Convert weight to always be float."""
    if weight_data is None:
        return 0.0
    return float(weight_data)


def normalize_property(property_data: Any) -> tuple[List[str], Dict[str, str]]:
    """
    Flatten property array and extract notes.

    Input: ["F", {"uid": "2H|XPHB", "note": "unless mounted"}]
    Output: (["F", "2H"], {"2H": "unless mounted"})
    """
    if not property_data:
        return [], {}

    properties = []
    notes = {}

    for prop in property_data:
        if isinstance(prop, str):
            # Simple string property
            properties.append(prop)
        elif isinstance(prop, dict):
            # Complex property with notes
            uid = prop.get('uid', '')
            note = prop.get('note')

            # Extract property code from uid (e.g., "2H|XPHB" → "2H")
            prop_code = uid.split('|')[0] if '|' in uid else uid
            properties.append(prop_code)

            if note:
                notes[prop_code] = note

    return properties, notes


def normalize_range(range_data: Any) -> Dict[str, int]:
    """
    Parse range into consistent format.

    Input: "30" or "30/120" or None
    Output: {"normal": 30, "long": None} or {"normal": 30, "long": 120}
    """
    if not range_data:
        return {"normal": None, "long": None}

    if isinstance(range_data, str):
        if '/' in range_data:
            parts = range_data.split('/')
            return {"normal": int(parts[0]), "long": int(parts[1])}
        else:
            try:
                return {"normal": int(range_data), "long": None}
            except ValueError:
                return {"normal": None, "long": None}

    return {"normal": None, "long": None}


def normalize_mastery(mastery_data: Any) -> List[str]:
    """
    Ensure mastery is always array of simple strings.

    Input: ["Sap|XPHB"] or None
    Output: ["Sap"]
    """
    if not mastery_data:
        return []

    if isinstance(mastery_data, list):
        # Extract just the mastery name, removing source suffix
        return [m.split('|')[0] if '|' in m else m for m in mastery_data]

    return []


def normalize_reprinted_as(reprinted: Any) -> List[str]:
    """
    Normalize reprintedAs to always be array of strings.

    Input: ["itemName"] OR [{"name": "itemName", "source": "PHB"}]
    Output: ["itemName"]
    """
    if not reprinted:
        return []

    result = []
    for item in reprinted:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            name = item.get('name', '')
            if name:
                result.append(name)
    return result


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


def normalize_entries(entries: Any) -> List[str]:
    """
    Flatten entries to array of strings only.

    Input: ["text", {"type": "list", "items": ["a", "b"]}]
    Output: ["text", "a", "b"]
    """
    if not entries:
        return []

    result = []
    for entry in entries:
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict):
            # Extract text from dict structures
            if 'items' in entry:
                items = entry['items']
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str):
                            result.append(item)
            elif 'entries' in entry:
                nested = normalize_entries(entry['entries'])
                result.extend(nested)
    return result


def normalize_pack_contents(contents: Any) -> List[Dict[str, Any]]:
    """
    Normalize packContents to always be array of dicts.

    Input: ["item name"] OR [{"item": "item name", "quantity": 2}]
    Output: [{"item": "item name", "quantity": 1}]
    """
    if not contents:
        return []

    result = []
    for item in contents:
        if isinstance(item, str):
            result.append({"item": item, "quantity": 1})
        elif isinstance(item, dict):
            result.append({
                "item": item.get('item', ''),
                "quantity": item.get('quantity', 1)
            })
    return result


def normalize_strength(strength: Any) -> int:
    """
    Normalize strength requirement to always be int.

    Input: "13" OR 13 OR None
    Output: 13 OR 0
    """
    if strength is None:
        return 0
    if isinstance(strength, str):
        try:
            return int(strength)
        except ValueError:
            return 0
    if isinstance(strength, int):
        return strength
    return 0


def normalize_attunement(attune: Any) -> Dict[str, Any]:
    """
    Normalize reqAttune to dict with required and description.

    Input: true OR "by a cleric"
    Output: {"required": true, "description": ""} OR {"required": true, "description": "by a cleric"}
    """
    if attune is None:
        return {"required": False, "description": ""}

    if isinstance(attune, bool):
        return {"required": attune, "description": ""}

    if isinstance(attune, str):
        return {"required": True, "description": attune}

    return {"required": False, "description": ""}


def normalize_focus(focus: Any) -> List[str]:
    """
    Normalize focus to always be array of strings.

    Input: true OR ["Druid"]
    Output: [] OR ["Druid"]
    """
    if focus is None or focus is False:
        return []

    if focus is True:
        return ["any"]

    if isinstance(focus, list):
        return [str(f) for f in focus]

    return []


def normalize_resist(resist: Any) -> List[str]:
    """
    Normalize resist to always be array of strings.

    Input: ["fire", "cold"] OR None
    Output: ["fire", "cold"] OR []
    """
    if resist is None:
        return []

    if isinstance(resist, list):
        return [str(r) for r in resist if isinstance(r, str)]

    return []


def normalize_recharge_amount(recharge: Any) -> int:
    """
    Normalize rechargeAmount to always be int.

    Input: "1d6" OR 3
    Output: 1 OR 3 (for dice strings, extract the die count)
    """
    if recharge is None:
        return 0

    if isinstance(recharge, int):
        return recharge

    if isinstance(recharge, str):
        # Try to extract number from dice notation like "1d6"
        if 'd' in recharge:
            try:
                return int(recharge.split('d')[0])
            except ValueError:
                return 1
        try:
            return int(recharge)
        except ValueError:
            return 1

    return 0


def normalize_charges(charges: Any) -> int:
    """
    Normalize charges to always be int.

    Input: 5 OR "5"
    Output: 5
    """
    if charges is None:
        return 0

    if isinstance(charges, int):
        return charges

    if isinstance(charges, str):
        try:
            return int(charges)
        except ValueError:
            return 0

    return 0


def normalize_attached_spells(spells: Any) -> List[str]:
    """
    Normalize attachedSpells to array of spell names.

    Input: {"spells": ["fireball", "lightning bolt"]} OR ["fireball"]
    Output: ["fireball", "lightning bolt"]
    """
    if spells is None:
        return []

    if isinstance(spells, list):
        return [str(s) for s in spells]

    if isinstance(spells, dict):
        spell_list = spells.get('spells', [])
        if isinstance(spell_list, list):
            return [str(s) for s in spell_list]

    return []


def normalize_float_field(value: Any) -> float:
    """
    Normalize int/float fields to always be float.

    Input: 24 OR 13.5
    Output: 24.0 OR 13.5
    """
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0

    return 0.0


def clean_item(item: Dict) -> Dict:
    """Clean a single item record."""
    cleaned = item.copy()

    # Normalize value
    cleaned['value'] = normalize_value(item.get('value'))

    # Normalize weight
    cleaned['weight'] = normalize_weight(item.get('weight'))

    # Normalize property
    properties, property_notes = normalize_property(item.get('property'))
    cleaned['property'] = properties
    if property_notes:
        cleaned['property_notes'] = property_notes

    # Default missing rarity
    if 'rarity' not in cleaned or not cleaned['rarity']:
        cleaned['rarity'] = 'none'

    # Normalize range
    if 'range' in item:
        range_data = normalize_range(item.get('range'))
        # Ensure both fields always exist and are correct type
        cleaned['range'] = {
            "normal": range_data["normal"],
            "long": range_data["long"] if range_data["long"] is not None else 0
        }

    # Normalize mastery - ensure always array of strings
    if 'mastery' in item:
        mastery_data = normalize_mastery(item.get('mastery'))
        cleaned['mastery'] = [str(m) if not isinstance(m, dict) else str(m.get('name', '')) for m in mastery_data]

    # Ensure type is clean (remove source suffix)
    if 'type' in cleaned and isinstance(cleaned['type'], str) and '|' in cleaned['type']:
        cleaned['type'] = cleaned['type'].split('|')[0]

    # Clean ammoType
    if 'ammoType' in cleaned and isinstance(cleaned['ammoType'], str) and '|' in cleaned['ammoType']:
        cleaned['ammoType'] = cleaned['ammoType'].split('|')[0]

    # Normalize reprintedAs
    if 'reprintedAs' in item:
        cleaned['reprintedAs'] = normalize_reprinted_as(item['reprintedAs'])

    # Normalize SRD fields
    if 'srd' in item:
        cleaned['srd'] = normalize_srd_field(item['srd'])

    if 'srd52' in item:
        cleaned['srd52'] = normalize_srd_field(item['srd52'])

    # Normalize entries
    if 'entries' in item:
        cleaned['entries'] = normalize_entries(item['entries'])

    # Normalize packContents
    if 'packContents' in item:
        cleaned['packContents'] = normalize_pack_contents(item['packContents'])

    # Normalize strength
    if 'strength' in item:
        cleaned['strength'] = normalize_strength(item['strength'])

    # Normalize attunement
    if 'reqAttune' in item:
        cleaned['reqAttune'] = normalize_attunement(item['reqAttune'])

    # Normalize focus
    if 'focus' in item:
        cleaned['focus'] = normalize_focus(item['focus'])

    # Normalize resist
    if 'resist' in item:
        cleaned['resist'] = normalize_resist(item['resist'])

    # Normalize rechargeAmount
    if 'rechargeAmount' in item:
        cleaned['rechargeAmount'] = normalize_recharge_amount(item['rechargeAmount'])

    # Normalize charges
    if 'charges' in item:
        cleaned['charges'] = normalize_charges(item['charges'])

    # Normalize attachedSpells
    if 'attachedSpells' in item:
        cleaned['attachedSpells'] = normalize_attached_spells(item['attachedSpells'])

    # Normalize vehicle speed
    if 'vehSpeed' in item:
        cleaned['vehSpeed'] = normalize_float_field(item['vehSpeed'])

    # Normalize cargo capacity
    if 'capCargo' in item:
        cleaned['capCargo'] = normalize_float_field(item['capCargo'])

    # Normalize additionalEntries
    if 'additionalEntries' in item:
        cleaned['additionalEntries'] = normalize_entries(item['additionalEntries'])

    # Normalize containerCapacity
    if 'containerCapacity' in item:
        capacity = item['containerCapacity']
        if isinstance(capacity, dict):
            if 'weight' in capacity:
                cleaned['containerCapacity']['weight'] = [normalize_float_field(w) for w in capacity['weight']] if isinstance(capacity['weight'], list) else [normalize_float_field(capacity['weight'])]
            if 'volume' in capacity:
                cleaned['containerCapacity']['volume'] = [normalize_float_field(v) for v in capacity['volume']] if isinstance(capacity['volume'], list) else [normalize_float_field(capacity['volume'])]

    # Normalize barDimensions
    if 'barDimensions' in item and isinstance(item['barDimensions'], dict):
        if 'h' in item['barDimensions']:
            cleaned['barDimensions']['h'] = normalize_float_field(item['barDimensions']['h'])

    # Remove _copy field entirely - it's metadata we don't need
    if '_copy' in cleaned:
        del cleaned['_copy']

    return cleaned


def main():
    """Main execution."""
    print("=" * 60)
    print("5etools Item Data Cleaning")
    print("=" * 60)

    all_items = []

    # Load items-base.json
    items_base_file = DATA_DIR / 'items-base.json'
    if items_base_file.exists():
        print(f"\n📦 Loading {items_base_file.name}...")
        with open(items_base_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            base_items = data.get('baseitem', [])
            print(f"  Found {len(base_items)} base items")

            for item in base_items:
                cleaned = clean_item(item)
                cleaned['_source_file'] = 'items-base.json'
                all_items.append(cleaned)

    # Load items.json
    items_file = DATA_DIR / 'items.json'
    if items_file.exists():
        print(f"\n📦 Loading {items_file.name}...")
        with open(items_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            magic_items = data.get('item', [])
            print(f"  Found {len(magic_items)} magic items")

            for item in magic_items:
                cleaned = clean_item(item)
                cleaned['_source_file'] = 'items.json'
                all_items.append(cleaned)

    # Save cleaned data
    print(f"\n💾 Saving {len(all_items)} cleaned items...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_items, f, indent=2)

    print(f"✅ Cleaned items saved to: {OUTPUT_FILE}")
    print(f"📊 Total items: {len(all_items)}")

    # Show sample
    print("\n📋 Sample cleaned item:")
    if all_items:
        sample = all_items[0]
        print(f"  Name: {sample.get('name')}")
        print(f"  Value: {sample.get('value')} cp")
        print(f"  Weight: {sample.get('weight')} lbs")
        print(f"  Rarity: {sample.get('rarity')}")
        print(f"  Properties: {sample.get('property', [])}")


if __name__ == '__main__':
    main()
