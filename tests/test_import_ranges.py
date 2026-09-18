"""Audit actual ELF imports, not merely fixup-tool idempotence."""
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]

def imports(path):
    data=path.read_bytes()
    assert data[:6]==b'\x7fELF\x01\x01'
    shoff=struct.unpack_from('<I',data,32)[0]
    entsize,count,names_index=struct.unpack_from('<HHH',data,46)
    sections=[struct.unpack_from('<10I',data,shoff+i*entsize) for i in range(count)]
    names=sections[names_index]
    names_data=data[names[4]:names[4]+names[5]]
    def text(buf,offset): return buf[offset:buf.index(b'\0',offset)].decode('ascii')
    named={text(names_data,s[0]):s for s in sections}
    def offset(address):
        return next(s[4]+address-s[3] for s in sections if s[3]<=address<s[3]+s[5] and s[1]!=8)
    section=named['.lib.stub']
    entries=[]
    position=section[4]
    while position<section[4]+section[5]:
        name,version,flags,length,variables,functions,nids,stubs=struct.unpack_from('<IHHBBHII',data,position)
        entries.append({'name':text(data,offset(name)),'functions':functions,'variables':variables,'nids':nids,'stubs':stubs,'nid_values':list(struct.unpack_from('<'+str(functions)+'I',data,offset(nids)))})
        position+=length*4
    return entries

class ImportRangeTest(unittest.TestCase):
    def test_module_import_ranges_do_not_overlap(self):
        entries=imports(ROOT/'onscripter.elf')
        for field,size in [('nids',4),('stubs',8)]:
            ordered=sorted(entries,key=lambda item:item[field])
            for a,b in zip(ordered,ordered[1:]):
                self.assertLessEqual(a[field]+a['functions']*size,b[field],f"{a['name']} overlaps {b['name']} in {field}")

    def test_utility_table_contains_only_actual_utility_imports(self):
        utility=next(item for item in imports(ROOT/'onscripter.elf') if item['name']=='sceUtility')
        self.assertEqual(set(utility['nid_values']),{0x2A2B3DE0,0xE49BFE92,0xA5DA2406})

if __name__=='__main__': unittest.main()
