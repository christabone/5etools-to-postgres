#!/usr/bin/env python3
import json

# Load files
cond = json.load(open('extraction_data/conditions_extracted.json'))
dmg = json.load(open('extraction_data/damage_extracted.json'))
xref = json.load(open('extraction_data/cross_refs_extracted.json'))

print('Conditions by entity:')
print(f'  Items: {len(cond["items"])}')
print(f'  Monsters: {len(cond["monsters"])}')
print(f'  Spells: {len(cond["spells"])}')
print(f'  Total: {len(cond["items"]) + len(cond["monsters"]) + len(cond["spells"])}')
print()

print('Damage by entity:')
print(f'  Items: {len(dmg["items"])}')
print(f'  Monster Attacks: {len(dmg["monster_attacks"])}')
print(f'  Spells: {len(dmg["spells"])}')
print(f'  Total: {len(dmg["items"]) + len(dmg["monster_attacks"]) + len(dmg["spells"])}')
print()

print('Cross-refs by type:')
for k, v in xref.items():
    print(f'  {k}: {len(v)}')

total_xref = sum(len(v) for v in xref.values())
print(f'  Total: {total_xref}')
print()

total_all = (len(cond["items"]) + len(cond["monsters"]) + len(cond["spells"]) +
             len(dmg["items"]) + len(dmg["monster_attacks"]) + len(dmg["spells"]) +
             total_xref)
print(f'GRAND TOTAL: {total_all} relationships')
