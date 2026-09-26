from __future__ import annotations
from .files import FileInfo

MAX_TEXT=3500
MAX_CAPTION=1024

def split_message(text:str)->list[str]:
    chunks=[]; current=""
    for paragraph in text.split("\n\n"):
        candidate=f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate)<=MAX_TEXT: current=candidate; continue
        if current: chunks.append(current)
        while len(paragraph)>MAX_TEXT: chunks.append(paragraph[:MAX_TEXT]); paragraph=paragraph[MAX_TEXT:]
        current=paragraph
    if current: chunks.append(current)
    return chunks

def build_plan(text:str,files:list[FileInfo])->list[dict[str,object]]:
    if not files: return [{"kind":"text","text":chunk} for chunk in split_message(text)]
    caption=text if len(text)<=MAX_CAPTION else ""; plan=[]
    if 2<=len(files)<=10 and all(item.media_type in {"photo","video"} for item in files):
        plan.append({"kind":"media_group","file_indexes":list(range(len(files))),"caption":caption})
    else:
        for index,item in enumerate(files):
            plan.append({"kind":"file","file_index":index,"method":item.media_type,"caption":caption if index==0 else ""})
    if text and not caption: plan.extend({"kind":"text","text":chunk} for chunk in split_message(text))
    return plan
