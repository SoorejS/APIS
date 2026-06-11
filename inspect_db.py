import os

def parse_varint(data, index):
    result = 0
    shift = 0
    while True:
        byte = data[index]
        index += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return result, index

def decode_proto(data, index=0, end=None):
    if end is None:
        end = len(data)
    
    fields = []
    while index < end:
        try:
            key, index = parse_varint(data, index)
        except IndexError:
            break
        field_num = key >> 3
        wire_type = key & 0x07
        
        if wire_type == 0:  # Varint
            try:
                val, index = parse_varint(data, index)
                fields.append((field_num, "varint", val))
            except IndexError:
                break
        elif wire_type == 1:  # 64-bit
            val = data[index:index+8]
            index += 8
            fields.append((field_num, "64bit", val))
        elif wire_type == 2:  # Length-delimited
            try:
                length, index = parse_varint(data, index)
            except IndexError:
                break
            val = data[index:index+length]
            index += length
            # Try to decode as string
            try:
                val_str = val.decode('utf-8')
                if all(32 <= ord(c) < 127 or c in '\n\r\t' for c in val_str):
                    fields.append((field_num, "string", val_str))
                else:
                    raise UnicodeDecodeError("not printable", val, 0, 1, "not printable")
            except UnicodeDecodeError:
                # Try recursive decode if it could be a nested message
                try:
                    nested = decode_proto(val, 0, len(val))
                    fields.append((field_num, "nested", nested))
                except:
                    fields.append((field_num, "bytes", val))
        elif wire_type == 3:  # Start group
            fields.append((field_num, "start_group", ""))
        elif wire_type == 4:  # End group
            fields.append((field_num, "end_group", ""))
        elif wire_type == 5:  # 32-bit
            val = data[index:index+4]
            index += 4
            fields.append((field_num, "32bit", val))
        else:
            index += 1
    return fields

def print_first_fields(path, name):
    print(f"\n--- Decoded {name} ({path}) ---")
    if not os.path.exists(path):
        print("File not found")
        return
    with open(path, 'rb') as f:
        data = f.read(500)  # read first 500 bytes
    try:
        fields = decode_proto(data)
        # print top-level fields
        for fnum, ftype, val in fields[:15]:
            if ftype == "nested":
                print(f"Field {fnum} (nested, size {len(val)} sub-fields)")
            elif ftype == "string":
                print(f"Field {fnum} (string): {repr(val[:60])}")
            elif ftype == "bytes":
                print(f"Field {fnum} (bytes): length {len(val)}")
            else:
                print(f"Field {fnum} ({ftype}): {val}")
    except Exception as e:
        print("Error decoding:", e)

print_first_fields(r"C:\Users\soore\.gemini\antigravity\conversations\280cbb61-cf32-4921-8413-10170e7dbaf3.pb", "Old APIS convo")
print_first_fields(r"C:\Users\soore\.gemini\antigravity-ide\conversations\409eca5c-84f1-4eca-921b-8344cbfe9e16.pb", "New convo")
# Let's also check another old convo
print_first_fields(r"C:\Users\soore\.gemini\antigravity\conversations\9cd0a142-777c-434c-89bd-0ffe6baaad26.pb", "Old Extractor convo")
