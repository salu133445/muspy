import muspy as msp
import os


data_path = ["../abc/" + f for f in os.listdir("../abc/") if f.endswith("abc") and f != "reelsH-L.abc" ]
total = 0
for f in data_path:
    abc_files = msp.read_abc_music21(f)
    total += len(abc_files)
    for abc_file in abc_files:
        abc_file.write_midi("Nottingham_recon/" + abc_file.meta.source.filename + ".mid")
    print("processed:", f, total)