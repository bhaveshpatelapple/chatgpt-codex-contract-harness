from .models import Episode
from .persistence import JsonRecordStore
from .retrieval import retrieve

class EpisodeStore:
    def __init__(self,path): self.store=JsonRecordStore(path,"episode",Episode.from_dict)
    def all(self): return self.store.load()
    def admit(self,task_kind,failure,repair,lesson,tags,verification_status,verification_id,created_sequence,expiry_sequence=None):
        return self.store.upsert(Episode.create(task_kind,failure,repair,lesson,tags,verification_status,verification_id,created_sequence,expiry_sequence))
    def retrieve(self,query): return retrieve(self.all(),query)
