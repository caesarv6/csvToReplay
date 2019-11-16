# coding: utf-8
import struct
import os

INPUT_CSV = "../Receive_19-11-15_163138_SV4.csv"
OUTPUT_REPLAY = os.path.basename(INPUT_CSV) + ".tr0"

CAN_FRAMES = []
# Read CVS and extract data frames
with open(INPUT_CSV, "r") as f_csv:
    first_line = True
    csv_headers = None
    for line in f_csv:
        if first_line:
            first_line = False
            csv_headers = line.replace("\"", "").split(";")
        else:
            csv_data = line.replace("\"", "").split(";")
            data_dict = {k: v for (k, v) in zip(csv_headers, csv_data)}
            CAN_FRAMES.append(data_dict)

with open(OUTPUT_REPLAY, "wb") as f_replay:
    header_part1 = "BB DB 7D 73 33 92 73 45 AB 62 97 3A FA 6C 6B 0C 01 00 01 00 64 00 00 00"
    header_part1 = bytes.fromhex(header_part1.replace(" ", ""))
    header_part2 = "00 00 00 00 1C 00 01 00 00 00 1C 00 55 00 53 00 42 00 2D 00 74 00 6F 00"\
                   "2D 00 43 00 41 00 4E 00 20 00 56 00 32 00 20 00 63 00 6F 00 6D 00 70 00"\
                   "61 00 63 00 74 00 20 00 20 00 43 00 41 00 4E 00 2D 00 31 00 00 00 00 00"
    header_part2 = bytes.fromhex(header_part2.replace(" ", ""))
    header_nb_frames = struct.pack("<i", len(CAN_FRAMES))
    replay_header = header_part1 + header_nb_frames + header_part2
    f_replay.write(replay_header)
    current_time = None
    frame_bin_list = []
    for frame in CAN_FRAMES:
        time_rel = int(frame["Time (rel)"].replace(".", ""))
        frame_id = struct.unpack(">I", bytes.fromhex(frame["ID (hex)"].replace(" ", "").zfill(8)))[0]
        length = int(frame["Length"])
        data = frame["Data (hex)"].replace(" ", "")
        if current_time is None:
            current_time = time_rel
        else:
            current_time += time_rel
        frame_bin = b"\x1c" + struct.pack("<Q", current_time) + b"\x00\x00\x00\x01\x01\x00"
        frame_bin += struct.pack("<I", frame_id) + struct.pack("<H", length) + bytes.fromhex(data)
        frame_bin_list.append(frame_bin)
    # try to pack frames into 128 consecutive frames
    while len(frame_bin_list) >= 128:
        packed_frames = b"".join(frame_bin_list[:128])
        packed_frames_length = len(packed_frames)
        f_replay.write(struct.pack("<I", packed_frames_length + 4) + packed_frames)
        frame_bin_list = frame_bin_list[128:]  # Remove 128 first frames
    if len(frame_bin_list) > 0:
        packed_frames = b"".join(frame_bin_list)  # Packing all remaining frames
        packed_frames_length = len(packed_frames)
        f_replay.write(struct.pack("<I", packed_frames_length + 4) + packed_frames)
