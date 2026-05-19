import difflib

class PromptDiffEngine:
    @staticmethod
    def generate_diff(before: str, after: str) -> dict:
        """
        Generate a structured explainable diff between two prompts.
        Groups immediately sequential deletions and additions as modifications.
        """
        if not before:
            before = ""
        if not after:
            after = ""
            
        before_lines = [line.strip() for line in before.splitlines() if line.strip()]
        after_lines = [line.strip() for line in after.splitlines() if line.strip()]
        
        diff = difflib.ndiff(before_lines, after_lines)
        
        diff_lines = list(diff)
        
        added = []
        removed = []
        modified = []
        
        i = 0
        n = len(diff_lines)
        while i < n:
            line = diff_lines[i]
            marker = line[:2]
            
            if marker in ("- ", "+ "):
                # Start of a contiguous changes block
                block_removes = []
                block_adds = []
                
                while i < n and diff_lines[i][:2] in ("- ", "+ "):
                    m = diff_lines[i][:2]
                    c = diff_lines[i][2:].strip()
                    if m == "- ":
                        block_removes.append(c)
                    elif m == "+ ":
                        block_adds.append(c)
                    i += 1
                
                # Pair corresponding items as modifications
                min_len = min(len(block_removes), len(block_adds))
                for j in range(min_len):
                    modified.append({
                        "before": block_removes[j],
                        "after": block_adds[j]
                    })
                
                # Remaining items are clean additions or removals
                if len(block_adds) > min_len:
                    added.extend(block_adds[min_len:])
                if len(block_removes) > min_len:
                    removed.extend(block_removes[min_len:])
            else:
                i += 1
                
        return {
            "added": added,
            "removed": removed,
            "modified": modified
        }
