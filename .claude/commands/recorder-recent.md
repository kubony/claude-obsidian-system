---
description: List recording files from external recorder device (default: last 24 hours)
allowed-tools: Bash(find:*), Bash(ls:*)
argument-hint: [hours]
---

# Recent Recorder Files

Find and list all recording files from the external recorder device within the specified time period.

**Device path:** `/Volumes/NO NAME/RECORD/`
**Requested time period:** $ARGUMENTS hours (default: 24 hours if not specified)

Use the Bash tool to run find command with -mmin option. Calculate minutes = hours * 60.
- If no argument given, use 1440 minutes (24 hours)
- If argument is 1, use 60 minutes
- etc.

First check if the device is mounted:
```
ls "/Volumes/NO NAME/RECORD/" 2>/dev/null
```

If mounted, list files:
```
find "/Volumes/NO NAME/RECORD" -type f \( -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" -o -name "*.MP3" -o -name "*.WAV" -o -name "*.M4A" \) -mmin -[MINUTES] -exec ls -lh {} \; 2>/dev/null | sort -k6,7
```

If device is not mounted, inform the user to connect the recorder device.

Execute the command and summarize the findings. Offer to help process these recordings (e.g., copy to 00_녹음파일 folder, transcribe).
