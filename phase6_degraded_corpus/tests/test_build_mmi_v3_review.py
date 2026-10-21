from phase6_degraded_corpus.src.reporting.build_mmi_v3_review import build

def item(axis,op,i):
    return {"canonical_pair_id":f"{axis}-{i}","canonical_original_id":f"o-{axis}-{i}","target_axis":axis,"operation":op,"corpus":"x","original":"Original.","clean_simplification":"Clean.","selected_index":0,"candidates":[{"degraded":"Bad.","valid":True}]}

def test_build_is_balanced_and_blinded():
    rows=[]
    for axis,ops in (("MOD",("mod_a","mod_b")),("ILLOC",("illoc_a","illoc_b"))):
        for i in range(8): rows.append(item(axis,ops[i%2],i))
    review,key=build(rows,count=6,seed=1)
    assert len(review)==12 and len(key)==12
    assert all("canonical_pair_id" not in row for row in review)
    for axis in ("MOD","ILLOC"):
        selected=[k for k in key if k["axis"]==axis]
        assert {op:sum(k["operation"]==op for k in selected) for op in {k["operation"] for k in selected}}=={(axis.casefold()+"_a"):3,(axis.casefold()+"_b"):3}
