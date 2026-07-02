#!/usr/bin/env python3
"""LIVEKIT -- the on-the-go performance kit for accompanying Sophia.

Not new material: a CURATED selection from every pack, reorganized into
eight MOOD LANES you can navigate in real time as you gauge her prose,
tempo, and themes. Design facts it leans on:

  * The MC-707's project tempo is global -- MIDI clips follow it -- so a
    lane is KEY-locked (every clip in a lane harmonizes) and carries a
    suggested tempo, not a hard one. Nudge the project tempo to her voice.
  * Clips are named by INTENSITY TIER: 0_drone -> 1_pad -> 2_bass ->
    3_beat_low -> 4_beat_full -> 5_melody -> 6_arp. Load a lane across a
    track row and you can build from near-silence to full groove by
    unmuting left to right, and strip back down as she pulls inward.
  * Lanes are PAIRED for live pivots (relative major, same-root recolor,
    same-key gear-shift) -- see SOPHIA_FIELD_GUIDE.md, which is the other
    half of this deliverable: prose-reading -> lane/tier moves.

Sources must exist on disk (run make_everything.py first if not).

    python livekit.py   ->  output/livekit/<lane>/<tier>_<name>.mid + INDEX.csv
"""

import csv
import os
import shutil

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "output")
DEST = os.path.join(OUT, "livekit")

# lane -> (suggested bpm, key, prose cues, [(source, tier_name), ...])
LANES = {
    "1_INTIMACY_Am_72": (72, "A minor", "close, warm, first-person, small rooms", [
        ("sophia/01_Ember_72_Am/drone.mid",              "0_drone"),
        ("sophia/01_Ember_72_Am/pad.mid",                "1_pad"),
        ("stemlib/basses/dub_Am_72.mid",                 "2_bass_dub"),
        ("sophia/01_Ember_72_Am/bass.mid",               "2_bass_bed"),
        ("stemlib/beats/dilla_84.mid",                   "3_beat_low_dilla"),
        ("sophia/01_Ember_72_Am/drums.mid",              "4_beat_full"),
        ("stemlib/melodies/hook_Am_72.mid",              "5_melody_hook"),
        ("stemlib/arps/drift16_Am_72.mid",               "6_arp_drift"),
    ]),
    "2_STORYTELLING_Ddor_64": (64, "D dorian", "narrative, spoken cadence, needs answer-space", [
        ("sophia/02_Vesper_64_Ddor/drone.mid",           "0_drone"),
        ("sophia/02_Vesper_64_Ddor/pad.mid",             "1_pad"),
        ("stemlib/basses/dronepulse_Ddor_64.mid",        "2_bass_pulse"),
        ("sophia/02_Vesper_64_Ddor/bass.mid",            "2_bass_bed"),
        ("stemlib/percussion/tumbao_62.mid",             "3_beat_low_tumbao"),
        ("sophia/02_Vesper_64_Ddor/drums.mid",           "4_beat_full"),
        ("stemlib/melodies/cell_Ddor_64.mid",            "5_melody_cell"),
        ("stemlib/arps/pedal_Ddor_64.mid",               "6_arp_pedal"),
    ]),
    "3_GRIEF_Gm_80": (80, "G minor", "elegy, loss, the lament -- anything ending", [
        ("sophia/03_Sable_80_Gm/drone.mid",              "0_drone"),
        ("sophia/03_Sable_80_Gm/pad.mid",                "1_pad"),
        ("stemlib/basses/lament_Gm_80.mid",              "2_bass_lament"),
        ("sophia/03_Sable_80_Gm/bass.mid",               "2_bass_bed"),
        ("stemlib/beats/halftime_84.mid",                "3_beat_low_halftime"),
        ("sophia/03_Sable_80_Gm/drums.mid",              "4_beat_full"),
        ("stemlib/melodies/hook_Gm_80.mid",              "5_melody_hook"),
        ("stemlib/arps/roll_Gm_80.mid",                  "6_arp_roll"),
    ]),
    "4_WONDER_Cmaj_88": (88, "C major", "awe, light, gratitude, open sky", [
        ("sophia/04_Aurora_88_Cmaj/drone.mid",           "0_drone"),
        ("sophia/04_Aurora_88_Cmaj/pad.mid",             "1_pad"),
        ("stemlib/basses/pachelbel_Cmaj_88.mid",         "2_bass_canon"),
        ("sophia/04_Aurora_88_Cmaj/bass.mid",            "2_bass_bed"),
        ("stemlib/beats/bossa_88.mid",                   "3_beat_low_bossa"),
        ("sophia/04_Aurora_88_Cmaj/drums.mid",           "4_beat_full"),
        ("stemlib/melodies/additive_Cmaj_88.mid",        "5_melody_additive"),
        ("stemlib/arps/drift16_Cmaj_88.mid",             "6_arp_drift"),
    ]),
    "5_RITUAL_Fsphr_72": (72, "F# phrygian", "incantation, dark, ceremonial, repetition", [
        ("sophia/05_Nocturne_68_Fsm/drone.mid",          "0_drone"),
        ("sophia/05_Nocturne_68_Fsm/pad.mid",            "1_pad"),
        ("stemlib/basses/folia_Fsphr_72.mid",            "2_bass_folia"),
        ("loopkit/02_Midnight_72_Fsphr/bass/drone-pulse.mid", "2_bass_pulse"),
        ("loopkit/02_Midnight_72_Fsphr/beats/halftime.mid",   "3_beat_low_halftime"),
        ("loopkit/02_Midnight_72_Fsphr/beats/tribal-toms.mid", "4_beat_full_tribal"),
        ("stemlib/melodies/isorhythm_Fsphr_72.mid",      "5_melody_isorhythm"),
        ("codex/01_Luna_60_Fs-hira/melody/isorhythm.mid", "5_melody_luna"),
        ("stemlib/arps/quartal_Fsphr_72.mid",            "6_arp_quartal"),
    ]),
    "6_MYSTERY_Dsus_66": (66, "D (no third)", "questions, ambiguity, the unnamed -- she decides the color", [
        ("sophia/09_Quarry_66_Dmaj/drone.mid",           "0_drone"),
        ("sophia/09_Quarry_66_Dmaj/pad.mid",             "1_pad_sus"),
        ("stemlib/chords/sus_Dm_62.mid",                 "1_pad_sus_alt"),
        ("sophia/09_Quarry_66_Dmaj/bass.mid",            "2_bass_bed"),
        ("stemlib/basses/ostinato_Dm_62.mid",            "2_bass_osti"),
        ("sophia/09_Quarry_66_Dmaj/drums.mid",           "4_beat_full"),
        ("stemlib/arps/quartal_Dm_62.mid",               "6_arp_quartal"),
        ("stemlib/chords/quartal_Dm_62.mid",             "1_pad_quartal"),
    ]),
    "7_MOTION_Dmaj_96": (96, "D major", "momentum, resolve, journeys, dancing", [
        ("sophia/06_Solstice_96_Dmaj/drone.mid",         "0_drone"),
        ("sophia/06_Solstice_96_Dmaj/pad.mid",           "1_pad"),
        ("stemlib/basses/pump_Dmaj_96.mid",              "2_bass_pump"),
        ("sophia/06_Solstice_96_Dmaj/bass.mid",          "2_bass_bed"),
        ("stemlib/beats/afrobeat_96.mid",                "3_beat_low_afrobeat"),
        ("sophia/06_Solstice_96_Dmaj/drums.mid",         "4_beat_full"),
        ("stemlib/melodies/ringing_Dmaj_96.mid",         "5_melody_ringing"),
        ("stemlib/arps/updown8_Dmaj_96.mid",             "6_arp_updown"),
    ]),
    "8_RAPTURE_Gm_124": (124, "G minor", "ecstatic, breathless, prophetic rush", [
        ("stemlib/chords/pop_Gm_124.mid",                "1_pad_cycle"),
        ("stemlib/basses/acid16_Gm_124.mid",             "2_bass_acid"),
        ("loopkit/06_Idioteque_124_Gm/bass/ostinato-riff.mid", "2_bass_osti"),
        ("loopkit/06_Idioteque_124_Gm/beats/fourfloor.mid",    "3_beat_low_fourfloor"),
        ("loopkit/06_Idioteque_124_Gm/beats/motorik.mid",      "4_beat_full_motorik"),
        ("stemlib/melodies/phase_Gm_124.mid",            "5_melody_phase"),
        ("loopkit/06_Idioteque_124_Gm/melody/arp-drift.mid",   "6_arp_drift"),
        ("stemlib/percussion/shaker-top_124.mid",        "7_perc_shaker"),
    ]),
}


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    missing, rows = [], []
    for lane, (bpm, key, cues, clips) in LANES.items():
        folder = os.path.join(DEST, lane)
        os.makedirs(folder)
        for src_rel, tier in clips:
            src = os.path.join(OUT, src_rel)
            if not os.path.exists(src):
                missing.append(src_rel)
                continue
            dst = os.path.join(folder, f"{tier}.mid")
            shutil.copyfile(src, dst)
            rows.append([lane, f"{tier}.mid", bpm, key, cues, src_rel])
        print(f"  {lane:<24} {len(clips)} clips @ ~{bpm}bpm ({key})")
    with open(os.path.join(DEST, "INDEX.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["lane", "clip", "suggested_bpm", "key", "prose_cues", "source"])
        w.writerows(rows)
    guide = os.path.join(HERE, "SOPHIA_FIELD_GUIDE.md")
    if os.path.exists(guide):
        shutil.copyfile(guide, os.path.join(DEST, "FIELD_GUIDE.md"))
    if missing:
        raise SystemExit(f"MISSING SOURCES (regenerate packs first): {missing}")
    print(f"{len(rows)} clips -> {DEST}")


if __name__ == "__main__":
    main()
