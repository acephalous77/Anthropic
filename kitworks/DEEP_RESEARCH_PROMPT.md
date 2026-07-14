Research the Roland MC-707 groovebox's MIDI/project workflow in depth. I have
22 custom song "kits" as Standard MIDI Files (SMF) I want to load onto the
device efficiently, and I need authoritative, verified answers — not
guesses. Please browse Roland's official Reference Manual PDF, the v1.30/v1.50
firmware update PDFs (SMF Import feature), the MC-707 Owner's Manual, and
active community sources (Gearspace, Elektronauts "MC 707/101" mega-thread,
Roland Clan Forums, r/synthesizers, YouTube tutorial transcripts, the
"Awesome-MC-707" GitHub list) to answer:

## 1. SMF import — exact procedure and behavior
- What is the EXACT button sequence to import a Standard MIDI File into a
  clip? (I have partial info: select a clip, press [CLIP], set COMMAND to
  EDIT, press [ENTER], select "MIDI FILE", press [ENTER] to browse the SD
  card — please confirm or correct this against the actual manual text,
  quoting it verbatim.)
- SMF files must live in ROLAND/GROOVEBOX/MIDI/ on the SD card — confirm.
- Does import target ONE currently-selected clip, or can it target a whole
  TRACK? Is there really an "All Tracks" vs "Each Track" mode? If so, quote
  the manual's exact description of what each mode does — does "Each Track"
  fan a multi-track SMF's tracks into consecutive CLIPS on one track
  (a "clip column"), or does it do something else entirely (e.g. spread
  across multiple TRACKS, one SMF track per device track)?
- Is there ANY way to import more than one file in a single operation —
  multi-select in the file browser, a folder-level import, a "import all"
  batch command, drag-and-drop via USB mass storage while the unit is
  running, or an editor-software route (e.g. a DAW plugin, Roland Cloud
  tool, or third-party utility) that can push multiple clips/tracks at once
  over USB MIDI or file transfer? I've found no batch import in my own
  research — please confirm this is really absent, or find one if it exists.
- Are there firmware-version differences that matter here (e.g. did v1.30,
  v1.50, v1.8 change import behavior)? What's the latest firmware and did it
  add anything relevant?
- Length/track/measure limits on imported SMFs?

## 2. Track MIDI channels
- Exact procedure to view/change a track's MIDI channel: I found
  "[SHIFT] + [TRACK SEL n]" opens per-track settings with a MIDI tab, and
  "[SHIFT] + [KNOB ASSIGN]" opens UTILITY > SET > MIDI showing all tracks at
  once. Confirm/correct these, quoting the manual.
- Does the MIDI channel assigned to a track affect how an IMPORTED CLIP
  plays back internally, or does internal playback always route through
  that track's assigned instrument/tone regardless of the channel byte
  embedded in the imported MIDI file's note events? I need to know whether
  I need to match channel numbers in my source .mid files to each track's
  configured channel, or whether that's irrelevant for internal (non-DIN/
  USB-external) playback.
- How many tracks does the MC-707 have total (I believe 8 main tracks, but
  confirm), and is there a fixed drum track, or can any track be a drum kit?

## 3. Practical batch-loading workarounds
- Can the MC-707 receive/record MIDI live over USB while a track is armed,
  i.e., can I play a prepared MIDI file out from a computer over USB MIDI
  into the unit in real time and have it recorded onto a track as a
  substitute for menu-based import? What's the exact procedure (record-arm
  a track, set it to receive on USB, etc.)?
- Is there a way to prepare a full multi-track project OFFLINE (on a
  computer) and load it as a complete project, bypassing per-clip SMF
  import entirely? Specifically: is the .mpj project file format documented
  ANYWHERE (even unofficially/reverse-engineered)? Is there any existing
  tool (open source or commercial) that reads/writes/generates .mpj files?
  I found the "Awesome-MC-707" GitHub repo mentions ZenCore tone data is
  undocumented and a related format-doc repo is empty — please verify this
  is still the current state, or find any newer effort.
- Does the MC-101 (same OS family) have any more flexible import/project
  tooling that would carry over, given it shares firmware architecture with
  the MC-707?
- Are there any Editor/Librarian apps (Roland's own, or third-party) that
  can build/edit a full project offline and transfer it via USB?

## Output format
For each question, give a direct answer, your confidence level, and the
exact source (manual page/section, forum post URL + date, etc.) — quote
manual text verbatim where possible rather than paraphrasing. Flag clearly
anywhere official docs are silent or contradict community reports. I'd
rather have "the manual doesn't say and no one has tested this" than a
confident guess.
