from __future__ import annotations
import json
from pathlib import Path
import pytest
from phase4a_gold_standard.backend.errors import PermissionDeniedError, ValidationError
from phase4a_gold_standard.backend.security import AuthenticatedUser
from phase4a_gold_standard.backend.s1_service import S1Service,S1Settings
from phase6_degraded_corpus.src.annotation.ingest_annotations import analyze
from phase6_degraded_corpus.src.annotation.package_s1 import build

def user(name="reviewer-en",languages=("en",)):
    return AuthenticatedUser(1,name,name,"reviewer",languages,"csrf")
def item(case="S001"):
    return {"case_id":case,"axis":"SYN","format":"pair","original":"An arduous task.","versions":{"X":"A hard task.","Y":"An arduous task."}}
def test_s1_language_access_and_audit(tmp_path):
    service=S1Service(S1Settings(tmp_path/"s1.sqlite3")); assert service.import_items([item()],"reviewer-en")=={"inserted":1,"unchanged":0}
    assert service.next(user("reviewer-fr",("fr",))) is None  # French reviewers have S1 access but only their own items
    with pytest.raises(PermissionDeniedError): service.task("S001",user("reviewer-fr",("fr",)))
    with pytest.raises(PermissionDeniedError): service.next(user("reviewer-de",("de",)))
    task=service.next(user()); assert task["case_id"]=="S001" and task["annotation"]["version"]==0
    draft=service.save("S001",user(),{"choice":"X"},0,False); assert draft["version"]==1
    final=service.save("S001",user(),{"choice":"X","side_effect":"none","side_effect_version":None,"note":"","uncertain":False},1,True); assert final["state"]=="submitted"
    with service.database.connect() as db: assert db.execute("select count(*) from revisions").fetchone()[0]==2
def test_public_payload_rejects_hidden_key(tmp_path):
    service=S1Service(S1Settings(tmp_path/"s1.sqlite3"))
    with pytest.raises(ValidationError,match="hidden"): service.import_items([item()|{"operations":{"X":"clean"}}],"reviewer-en")
def test_controls_are_blinded_and_deterministic():
    first,key=build(); second,key2=build(); assert first==second and key==key2 and len(first)==30
    assert all(not ({"levels","operations","expected","control_kind"}&set(x)) for x in first)
    assert sum(x["versions"]["X"]==x["versions"]["Y"] for x in first)==15
def test_ingest_scores_pair_and_control(tmp_path):
    key=[{"case_id":"S001","axis":"SYN","format":"pair","levels":{"X":1.0,"Y":0.0},"operations":{"X":"clean","Y":"restore"}}]
    controls=[{"case_id":"C001","control_kind":"identical","expected":"Same"}]
    (tmp_path/"key.json").write_text(json.dumps(key)); (tmp_path/"controls.json").write_text(json.dumps(controls))
    rows=[{"case_id":"S001","axis":"SYN","format":"pair","state":"submitted","human_final":{"choice":"X","side_effect":"none","note":""},"llm_suggestion":{"choice":"Y","side_effect":"none"},"changed":True},{"case_id":"C001","state":"submitted","human_final":{"choice":"Same","side_effect":"none"}}]
    export=tmp_path/"export.jsonl"; export.write_text("".join(json.dumps(x)+"\n" for x in rows))
    result,adj=analyze(export,tmp_path/"key.json",tmp_path/"controls.json"); assert result["validity_by_axis_format"]["SYN/pair"]["rate"]==1; assert result["control_accuracy"]["rate"]==1; assert result["llm_change_rate_by_axis"]["SYN"]["rate"]==1; assert not adj
def test_spanish_items_need_a_spanish_reviewer(tmp_path):
    service=S1Service(S1Settings(tmp_path/"s1.sqlite3")); es=item("ES-S001")|{"language":"es"}
    service.import_items([es],"reviewer-es"); assert service.next(user("reviewer-es",("es",)))["language"]=="es"
    with pytest.raises(PermissionDeniedError): service.next(user("reviewer-es",("en",)))
    with pytest.raises(ValidationError,match="language"): service.import_items([item("DE-S001")|{"language":"de"}],"reviewer-es")
def test_ingest_keeps_only_its_language_round(tmp_path):
    key=[{"case_id":"FR-S001","axis":"SYN","format":"pair","levels":{"X":1.0,"Y":0.0},"operations":{"X":"clean","Y":"syn"}}]
    (tmp_path/"key.json").write_text(json.dumps(key)); (tmp_path/"controls.json").write_text("[]")
    answer={"choice":"X","side_effect":"none","note":""}
    rows=[{"case_id":"FR-S001","state":"submitted","human_final":answer},{"case_id":"S001","state":"submitted","human_final":answer},{"case_id":"ES-S001","state":"submitted","human_final":answer}]
    export=tmp_path/"export.jsonl"; export.write_text("".join(json.dumps(x)+"\n" for x in rows))
    result,_=analyze(export,tmp_path/"key.json",tmp_path/"controls.json","fr"); assert result["submitted_noncontrol"]==1
def test_human_version_shown_after_submit_and_answer_locked(tmp_path):
    service=S1Service(S1Settings(tmp_path/"s1.sqlite3")); service.import_items([item()],"reviewer-en")
    service.database.import_meta([{"case_id":"S001","dataset":"MultiSim · ASSET","human_versions":["X"]}])
    before=service.next(user()); assert before["dataset"]=="MultiSim · ASSET" and before["reveal"] is None
    final={"choice":"X","side_effect":"none","side_effect_version":None,"note":"","uncertain":False}
    service.save("S001",user(),final,0,True)
    after=service.task("S001",user()); assert after["reveal"]=={"human_versions":["X"]}
    with pytest.raises(ValidationError,match="locked"): service.save("S001",user(),final|{"choice":"Y"},1,True)
def test_prioritize_moves_items_first_and_keeps_the_rest(tmp_path):
    service=S1Service(S1Settings(tmp_path/"s1.sqlite3"))
    service.import_items([item(f"S00{i}")|{"_queue_rank":i} for i in range(1,5)],"reviewer-en")
    service.database.prioritize("reviewer-en",["S004","S002"])
    assert [x["case_id"] for x in service.database.list_items("reviewer-en")]==["S004","S002","S001","S003"]
    with pytest.raises(ValueError): service.database.prioritize("reviewer-en",["S999"])
