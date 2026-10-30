# S1 annotation guidelines (v2)

[Methodology index](README.md)

Judge only the named axis. X, Y and Z are neutral shuffled labels. For a pair, choose the better version or **Same**. For three or more versions, give **Rank 1 to the best**; equal ranks mean a tie. Report any other problem (a change in meaning, a grammar error) separately, and explain briefly in the note if unsure.

The optional AI suggestion is assistance, not an answer key.

| Axis | Better version | Degraded versions (target score) |
|---|---|---|
| MEANING | says what the Original says | trim 1.0 · detail lost 0.67 · sentence lost 0.33 · contradiction 0.0 |
| FLUENCY | grammatical and natural | minor error 0.67 · major error 0.33 · severe 0.0 |
| OMIT | leaves out unnecessary detail | one detail back 0.5 · two details back 0.0 |
| SYN | uses simple words | one harder word back 0.5 · two 0.0 |
| EXPL | explains difficult terms | explanation removed 0.0 |
| MOD | main point first, sentences in a logical order | secondary information fronted 0.5 · fronted and sentences swapped 0.0 |
| ILLOC | the purpose is expressed directly | direct act made indirect 0.0 |

## MEANING — faithful content

The simplified text should keep the content of the Original. Worse means content is lost or a fact is wrong.

- Removing a redundant word ("also") changes nothing: **Same**.
- "Coventry is a city in England. It is also a metropolitan borough." > "… It is also a borough." (a detail is lost) > "Coventry is a city in England." (a sentence is lost) > "Coventry is a city in Scotland. …" (contradicts the Original).
- A change in certainty ("is" → "might be") is a MEANING change.

## FLUENCY — grammar

The text should be grammatical and read naturally. Worse means more or more serious errors; the meaning is unchanged.

- Minor: a missing article or a wrong preposition ("people already on a band").
- Major: broken agreement or two swapped words ("a side project are", "one or people more").
- Severe: three errors in one text.

## OMIT — unnecessary detail

The simplified text should leave out unnecessary detail. Worse means an unnecessary detail is back.

- "Taiwo is a Nigerian professional footballer" > "… footballer who plays as a defender for RoPS".
- Three versions: focused sentence first, one restored detail second, two restored details third.

## SYN — simple words

The simplified text should use simple words. Worse means a harder word is back without changing the meaning.

- "Gospel music is a style of music" > "Gospel music is a genre of music".
- Names and titles are never changed.

## EXPL — explanations

Difficult terms should be explained. Worse means a useful explanation was removed.

- "tachycardia (a fast heartbeat)" > "tachycardia".

## MOD — information order

Information should come in the order that is easiest to follow: the main point first, background after it, and each sentence after the one it depends on. Splitting a sentence is not judged here.

- Mild: secondary information moved to the front ("From January 2017 to July 2019 he served as President of the European Parliament").
- Strong: the same, and two dependent sentences swapped (a sentence that uses "it" or "the plan" comes before the one that introduces it).
- Rank: clean first, mild second, strong third.

## ILLOC — directness of the communicative act

A good Easy-to-Read text keeps the purpose of the Original (informing, instructing, asking) and expresses it **directly**: the reader knows at once what is stated, asked or required. Worse means the same act made indirect.

- Instruction: "Use soap and warm water" > "Soap and warm water should be used".
- Question: "Where did the name 'foxtrot' come from?" > "The question is where the name 'foxtrot' came from".
- Address to the reader: "You can only find it on Christmas Island" > "It is only found on Christmas Island".
- A reworded version that keeps the act direct ("Note that…" → "Remember that…") is as good as the clean text: **Same**.
- Turning a plain statement into an instruction is not a degradation, and a change in certainty is MEANING.
