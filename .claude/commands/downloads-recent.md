---
description: List files added to Downloads folder in the last N hours (default: 1 hour)
allowed-tools: Bash(mdfind:*), Bash(ls:*), Bash(mdls:*), Bash(find:*)
argument-hint: [hours]
---

# Recent Downloads

Find and list all files added to the Downloads folder within the specified time period.

**Requested time period:** $ARGUMENTS hours (default: 1 hour if not specified)

## Hybrid Approach: mdfind + find fallback

Spotlight 인덱싱이 안 된 새 파일이 있을 수 있으므로 **두 가지 방법을 모두 실행**:

### Step 1: find (mtime 기반) - 항상 실행

```bash
# Calculate minutes: hours * 60 (default 1 hour = 60 minutes)
find ~/Downloads -maxdepth 1 -type f -mmin -[MINUTES] -exec ls -lh {} \; 2>/dev/null
```

### Step 2: mdfind (kMDItemDateAdded 기반) - 보조

```bash
# 24시간 (1일):
mdfind -onlyin ~/Downloads 'kMDItemDateAdded > $time.today(-1)' 2>/dev/null | \
while read f; do ls -lh "$f" 2>/dev/null; done
```

**참고:**
- `find -mmin`: mtime 기준, Spotlight 인덱싱 불필요, 모든 파일 검출
- `mdfind`: kMDItemDateAdded 기준, Finder 표시와 일치하지만 새 파일 누락 가능
- AirDrop/공유로 받은 파일은 Spotlight 인덱싱이 늦어 `find`로만 검출될 수 있음

Execute both commands and combine results. For each file, show:
- Filename
- Size
- Date/Time

Offer to help with any of these files if needed (e.g., process recordings, open documents).
